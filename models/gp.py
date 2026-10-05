import numpy as np
import json
import warnings
import pickle
from pathlib import Path
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern, DotProduct, ConstantKernel
from sklearn.preprocessing import StandardScaler

from models import train_cli
from utils import train_val_split


class GPModel:
    def __init__(self, scaler=None, gp=None, alpha=None):
        self.scaler = scaler if scaler is not None else StandardScaler()
        self.gp = gp
        self.alpha = alpha

    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        return self.gp.predict(X_scaled)


def _base_kernels(d, cfg):
    cv_b = cfg["constant_value_bounds"]
    ls_b = cfg["length_scale_bounds"]
    ard_b = cfg.get("length_scale_bounds_per_axis", ls_b)
    ard_ls = [float(np.sqrt(lo * hi)) for lo, hi in ard_b] if "length_scale_bounds_per_axis" in cfg else [1.0] * d
    bases = {
        "RBF": ConstantKernel(1.0, cv_b) * RBF(length_scale=ard_ls,
                                               length_scale_bounds=ard_b),
        "MAT": ConstantKernel(1.0, cv_b) * Matern(length_scale=ard_ls,
                                                  length_scale_bounds=ard_b,
                                                  nu=2.5),
    }
    bases["LIN"] = ConstantKernel(1.0, cv_b) * DotProduct(sigma_0=1.0, sigma_0_bounds=cv_b)
    return bases


def kernel_from_spec(spec, d, cfg):
    bases = _base_kernels(d, cfg)
    if spec in bases:
        return bases[spec]
    depth = 0
    for i, ch in enumerate(spec):
        depth += (ch == "(") - (ch == ")")
        if depth == 0:
            break
    inner, op, base = spec[1:i], spec[i + 1], spec[i + 2:]
    left = kernel_from_spec(inner, d, cfg)
    right = bases[base]
    return left + right if op == "+" else left * right


def train_gp(X_interp, y_interp, config, ds=None):
    X_tr, y_tr, X_val, y_val = train_val_split(X_interp, y_interp)
    scaler = StandardScaler().fit(X_tr)
    X_tr, X_val = scaler.transform(X_tr), scaler.transform(X_val)
    best = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for alpha in config["alphas"]:
            gp = GaussianProcessRegressor(kernel=kernel_from_spec(config["kernel"], X_tr.shape[1], config), alpha=alpha,
                                          n_restarts_optimizer=config["n_restarts_optimizer"], normalize_y=True).fit(X_tr, y_tr)
            val_mse = float(np.mean((gp.predict(X_val) - y_val) ** 2))
            if best is None or val_mse < best["val_mse"]:
                best, model = {"alpha": alpha, "val_mse": val_mse}, GPModel(scaler, gp, alpha)
    params = {**best, "kernel": config["kernel"], "optimized_kernel": str(model.gp.kernel_),
              "log_marginal_likelihood": float(model.gp.log_marginal_likelihood_value_)}
    print(f"GP: alpha={best['alpha']:.1e}, val MSE={best['val_mse']:.2e}, kernel {model.gp.kernel_}")
    return model, params


def save_model(model, params, path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    with open(path / "model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open(path / "params.json", "w") as f:
        json.dump(params, f, indent=2)


def load_model(path):
    with open(Path(path) / "model.pkl", "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    train_cli("Train GP model", "GP", train_gp, save_model)
