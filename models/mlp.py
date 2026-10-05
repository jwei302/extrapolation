import torch
import torch.nn as nn

from models import train_cli
from models.torch_utils import DTYPE, InputNorm, ResBlock, TorchModel, settings, train_neural, save_checkpoint, load_checkpoint


class MLP(TorchModel):
    def __init__(self, hidden_sizes, activation="relu", input_mean=None, input_std=None):
        super().__init__()
        act_map = {
            "gelu": nn.GELU,
            "tanh": nn.Tanh,
            "silu": nn.SiLU,
        }
        act_cls = act_map[activation]

        layers = []
        if input_mean is not None and input_std is not None:
            layers.append(InputNorm(input_mean, input_std))

        layers.extend([nn.Linear(2, hidden_sizes[0]), nn.LayerNorm(hidden_sizes[0]), act_cls()])
        for i in range(1, len(hidden_sizes)):
            if hidden_sizes[i] == hidden_sizes[i - 1]:
                layers.append(ResBlock(hidden_sizes[i], act_cls))
            else:
                layers.extend([nn.Linear(hidden_sizes[i - 1], hidden_sizes[i]),
                               nn.LayerNorm(hidden_sizes[i]), act_cls()])
        layers.append(nn.Linear(hidden_sizes[-1], 1))
        self.net = nn.Sequential(*layers)


    def forward(self, x):
        return self.denorm(self.net(x).squeeze(-1))


def train_mlp(X, y, config, ds=None):
    grid = [{"hidden_sizes": [s.pop("width")] * s.pop("n_layers"), **s}
            for s in settings(config, n_layers="n_layers_list", width="widths", activation="activations",
                              lr="lrs", weight_decay="weight_decays")]
    return train_neural(lambda s, im, istd: MLP(s["hidden_sizes"], s["activation"], im, istd), grid, X, y, config)


def save_model(model, params, results_dir):
    save_checkpoint(model, params, results_dir, {"hidden_sizes": params["hidden_sizes"], "activation": params["activation"]})


def load_model(path):
    return load_checkpoint(path, lambda cfg: MLP(cfg["hidden_sizes"], cfg["activation"],
                                                 torch.zeros(2, dtype=DTYPE), torch.ones(2, dtype=DTYPE)))


if __name__ == "__main__":
    train_cli("Train MLP model", "MLP", train_mlp, save_model)
