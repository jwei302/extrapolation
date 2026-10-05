import torch
import torch.nn as nn
import torch.nn.functional as F

from data import PAIR
from models import train_cli
from models.torch_utils import DTYPE, TorchModel, settings, train_neural, save_checkpoint, load_checkpoint


class _CoeffNet(nn.Module):
    def __init__(self, n_out, width, n_layers, act_cls=nn.GELU):
        super().__init__()
        layers = [nn.Linear(1, width), act_cls()]
        for _ in range(n_layers - 1):
            layers += [nn.Linear(width, width), act_cls()]
        layers.append(nn.Linear(width, n_out))
        self.net = nn.Sequential(*layers)

    def forward(self, t):
        return self.net(t)


class GrayBox(TorchModel):
    def __init__(self, spec, width, n_layers, input_mean=None, input_std=None):
        super().__init__()
        self.spec = dict(spec)
        self.structure = spec["structure"]
        n_out = len(spec["orders"]) if self.structure == "coeff_poly" else 5   # peak: A, E0, w, b0, b1
        self.coeffs = _CoeffNet(n_out, width, n_layers)
        im = input_mean if input_mean is not None else torch.zeros(2, dtype=DTYPE)
        istd = input_std if input_std is not None else torch.ones(2, dtype=DTYPE)
        self.register_buffer("input_mean", im)
        self.register_buffer("input_std", istd)

    def forward(self, X):
        t = ((X[:, :1] - self.input_mean[0]) / self.input_std[0])
        x = X[:, 1]
        c = self.coeffs(t)
        if self.structure == "coeff_poly":
            xn = (x - self.input_mean[1]) / self.input_std[1]
            out = sum(c[:, i] * xn ** k
                      for i, k in enumerate(self.spec["orders"]))
        else:
            e_lo, e_hi = self.spec["E_range"]
            A = F.softplus(c[:, 0])
            E0 = e_lo + torch.sigmoid(c[:, 1]) * (e_hi - e_lo)
            w = F.softplus(c[:, 2]) * (e_hi - e_lo) * 0.25 + 1e-4 * (e_hi - e_lo)
            out = (A * torch.exp(-0.5 * ((x - E0) / w) ** 2)
                   + c[:, 3] + c[:, 4] * (x - self.input_mean[1]) / self.input_std[1])
        return self.denorm(out)


def train_graybox(X, y, config, ds=None):
    spec = {"structure": config["structure"]}
    if config["structure"] == "coeff_poly":
        spec["orders"] = list(config["orders"])
    else:
        spec["E_range"] = [float(X[:, 1].min()), float(X[:, 1].max())]
    grid = settings(config, n_layers="n_layers_list", width="widths", lr="lrs", weight_decay="weight_decays")
    model, params = train_neural(lambda s, im, istd: GrayBox(spec, s["width"], s["n_layers"], im, istd), grid, X, y, config)
    return model, {**params, "spec": spec}


def save_model(model, params, results_dir):
    save_checkpoint(model, params, results_dir, {"spec": model.spec, "width": params["width"], "n_layers": params["n_layers"]})


def load_model(path):
    return load_checkpoint(path, lambda cfg: GrayBox(cfg["spec"], cfg["width"], cfg["n_layers"]))


if __name__ == "__main__":
    train_cli("Train gray-box model", "GRAYBOX", train_graybox, save_model, datasets=PAIR)
