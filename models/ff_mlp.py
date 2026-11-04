import math
import torch
import torch.nn as nn

from data import PAIR
from models import train_cli
from models.torch_utils import DTYPE, InputNorm, ResBlock, TorchModel, settings, train_neural, save_checkpoint, load_checkpoint


class FourierMLP(TorchModel):
    def __init__(self, input_dim, m_ff, sigma, hidden_sizes, activation,
                 input_mean=None, input_std=None, B=None):
        super().__init__()
        act_map = {"gelu": nn.GELU, "tanh": nn.Tanh, "silu": nn.SiLU,
                   "relu": nn.ReLU}
        act_cls = act_map[activation]

        # B: (m_ff, input_dim)
        if B is None:
            B = torch.randn(m_ff, input_dim, dtype=DTYPE) * sigma
        else:
            B = B.to(dtype=DTYPE)
        self.register_buffer("B", B)

        layers = []
        if input_mean is not None and input_std is not None:
            layers.append(InputNorm(input_mean, input_std))
        feat_dim = 2 * m_ff
        layers.extend([nn.Linear(feat_dim, hidden_sizes[0]),
                       nn.LayerNorm(hidden_sizes[0]), act_cls()])
        for i in range(1, len(hidden_sizes)):
            if hidden_sizes[i] == hidden_sizes[i - 1]:
                layers.append(ResBlock(hidden_sizes[i], act_cls))
            else:
                layers.extend([nn.Linear(hidden_sizes[i - 1], hidden_sizes[i]),
                               nn.LayerNorm(hidden_sizes[i]), act_cls()])
        layers.append(nn.Linear(hidden_sizes[-1], 1))

        self.input_norm, self.body = layers[0], nn.Sequential(*layers[1:])

        self.input_dim = input_dim
        self.m_ff = m_ff
        self.sigma = sigma
        self.hidden_sizes = list(hidden_sizes)
        self.activation = activation

    def _gamma(self, x):
        proj = 2.0 * math.pi * (x @ self.B.t())
        return torch.cat([torch.cos(proj), torch.sin(proj)], dim=-1)

    def forward(self, x):
        if self.input_norm is not None:
            x = self.input_norm(x)
        feats = self._gamma(x)
        return self.denorm(self.body(feats).squeeze(-1))


def train_ff_mlp(X, y, config, ds=None):
    grid = [{"hidden_sizes": [s.pop("width")] * s.pop("n_layers"), "activation": config["activation"], **s}
            for s in settings(config, m_ff="m_ff_list", sigma="sigmas", n_layers="n_layers_list", width="widths",
                              lr="lrs", weight_decay="weight_decays")]
    build = lambda s, im, istd: FourierMLP(X.shape[1], s["m_ff"], s["sigma"], s["hidden_sizes"], s["activation"], im, istd)
    return train_neural(build, grid, X, y, config)


def save_model(model, params, results_dir):
    save_checkpoint(model, params, results_dir,
                    {"input_dim": model.input_dim, "m_ff": model.m_ff, "sigma": model.sigma,
                     "hidden_sizes": model.hidden_sizes, "activation": model.activation})


def load_model(path):
    return load_checkpoint(path, lambda cfg: FourierMLP(
        cfg["input_dim"], cfg["m_ff"], cfg["sigma"], cfg["hidden_sizes"], cfg["activation"],
        torch.zeros(cfg["input_dim"], dtype=DTYPE), torch.ones(cfg["input_dim"], dtype=DTYPE)))


if __name__ == "__main__":
    train_cli("Train Fourier-features MLP", "FF_MLP", train_ff_mlp, save_model, datasets=PAIR)
