import numpy as np
import torch
import torch.nn.functional as F

from data import PAIR
from models import train_cli
from models.mlp import MLP, save_model, load_model      # a PINN is an MLP, saved and loaded as one
from models.torch_utils import DEVICE, DTYPE, settings, train_neural


def _residual(model, constraints, Xc, Xc_flip, Xg, grid_shape, y_mean, y_std):
    """even_x2: f(t, -m) = f(t, m); nonneg: f >= 0; sumrule: the same integral over m at every t."""
    total = 0.0
    if "even_x2" in constraints:
        total = total + F.mse_loss(model(Xc), model(Xc_flip))
    if "nonneg" in constraints:
        total = total + torch.mean(F.relu(-y_mean / y_std - model(Xc)) ** 2)
    if "sumrule" in constraints:
        rows = model(Xg).reshape(grid_shape).mean(dim=1)
        total = total + torch.mean((rows - rows.mean()) ** 2)
    return total


def train_pinn(X, y, config, ds):
    (t_lo, t_hi), (m_lo, m_hi) = (ds.T_EXTRAP[0], ds.T_INTERP[1]), ds.M_RANGE
    rng = np.random.default_rng(0)
    Xc = torch.tensor(np.column_stack([rng.uniform(t_lo, t_hi, config["n_colloc"]),
                                       rng.uniform(m_lo, m_hi, config["n_colloc"])]), dtype=DTYPE, device=DEVICE)
    Xc_flip = Xc.clone()
    Xc_flip[:, 1] = -Xc_flip[:, 1]
    grid_shape = tuple(config["grid_shape"])
    TT, MM = np.meshgrid(np.linspace(t_lo, t_hi, grid_shape[0]), np.linspace(m_lo, m_hi, grid_shape[1]), indexing="ij")
    Xg = torch.tensor(np.column_stack([TT.ravel(), MM.ravel()]), dtype=DTYPE, device=DEVICE)

    def physics(setting, y_mean, y_std):
        return lambda model: setting["lambda_phys"] * _residual(model, config["constraints"], Xc, Xc_flip, Xg,
                                                                grid_shape, y_mean, y_std)

    grid = [{"hidden_sizes": [s.pop("width")] * s.pop("n_layers"), **s}
            for s in settings(config, n_layers="n_layers_list", width="widths", activation="activations",
                              lr="lrs", weight_decay="weight_decays", lambda_phys="lambdas")]
    model, params = train_neural(lambda s, im, istd: MLP(s["hidden_sizes"], s["activation"], im, istd),
                                 grid, X, y, config, physics)
    return model, {**params, "constraints": config["constraints"]}


if __name__ == "__main__":
    train_cli("Train physics-informed MLP", "PINN", train_pinn, save_model, datasets=PAIR)
