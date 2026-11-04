import math
import torch
import torch.nn as nn

from data import PAIR
from models import train_cli
from models.torch_utils import DTYPE, InputNorm, TorchModel, settings, train_neural, save_checkpoint, load_checkpoint


class SineLayer(nn.Module):
    def __init__(self, in_features, out_features, omega_0=30.0,
                 is_first=False):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features)
        self.omega_0 = omega_0
        self.is_first = is_first
        self._init_weights()

    def _init_weights(self):
        with torch.no_grad():
            d = self.linear.in_features
            if self.is_first:
                self.linear.weight.uniform_(-1.0 / d, 1.0 / d)
            else:
                bound = math.sqrt(6.0 / d) / self.omega_0
                self.linear.weight.uniform_(-bound, bound)
            if self.linear.bias is not None:
                self.linear.bias.uniform_(-1.0 / math.sqrt(d),
                                          1.0 / math.sqrt(d))

    def forward(self, x):
        return torch.sin(self.omega_0 * self.linear(x))


class SIREN(TorchModel):

    def __init__(self, input_dim, hidden_sizes, omega_0_first=30.0,
                 omega_0_hidden=1.0, input_mean=None, input_std=None):
        super().__init__()
        self.input_norm = (InputNorm(input_mean, input_std)
                           if input_mean is not None and input_std is not None
                           else None)

        layers = [SineLayer(input_dim, hidden_sizes[0],
                            omega_0=omega_0_first, is_first=True)]
        for i in range(1, len(hidden_sizes)):
            layers.append(SineLayer(hidden_sizes[i - 1], hidden_sizes[i],
                                    omega_0=omega_0_hidden, is_first=False))
        out = nn.Linear(hidden_sizes[-1], 1)
        with torch.no_grad():
            d = hidden_sizes[-1]
            bound = math.sqrt(6.0 / d) / omega_0_hidden
            out.weight.uniform_(-bound, bound)
            if out.bias is not None:
                out.bias.uniform_(-1.0 / math.sqrt(d), 1.0 / math.sqrt(d))
        layers.append(out)
        self.net = nn.Sequential(*layers)


        self.input_dim = input_dim
        self.hidden_sizes = list(hidden_sizes)
        self.omega_0_first = omega_0_first
        self.omega_0_hidden = omega_0_hidden

    def forward(self, x):
        if self.input_norm is not None:
            x = self.input_norm(x)
        return self.denorm(self.net(x).squeeze(-1))


def train_siren(X, y, config, ds=None):
    grid = [{"hidden_sizes": [s.pop("width")] * s.pop("n_layers"), "omega_0_hidden": config["omega_0_hidden"], **s}
            for s in settings(config, n_layers="n_layers_list", width="widths", omega_0_first="omega_0_first_list",
                              lr="lrs", weight_decay="weight_decays")]
    build = lambda s, im, istd: SIREN(X.shape[1], s["hidden_sizes"], s["omega_0_first"], s["omega_0_hidden"], im, istd)
    return train_neural(build, grid, X, y, config)


def save_model(model, params, results_dir):
    save_checkpoint(model, params, results_dir,
                    {"input_dim": model.input_dim, "hidden_sizes": model.hidden_sizes,
                     "omega_0_first": model.omega_0_first, "omega_0_hidden": model.omega_0_hidden})


def load_model(path):
    return load_checkpoint(path, lambda cfg: SIREN(
        cfg["input_dim"], cfg["hidden_sizes"], cfg["omega_0_first"], cfg["omega_0_hidden"],
        torch.zeros(cfg["input_dim"], dtype=DTYPE), torch.ones(cfg["input_dim"], dtype=DTYPE)))


if __name__ == "__main__":
    train_cli("Train SIREN", "SIREN", train_siren, save_model, datasets=PAIR)
