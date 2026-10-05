import numpy as np
import scipy.linalg
from pathlib import Path


SEEDS = [42, 43, 44, 45, 46]
SIZES = list(range(200, 2001, 200))
N_TRAIN = 2000


def region_densities(interp, extrap):
    span = max(interp[1], extrap[1]) - min(interp[0], extrap[0])
    return span / (interp[1] - interp[0]), span / (extrap[1] - extrap[0])


def slide_interp(tc, d, width, below=False):
    d = float(d)
    if below:
        hi = tc - d
        return (hi - width, hi)
    return (tc + d, tc + d + width)


def train_val_split(X, y, val_frac=0.2, seed=42):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(X))
    n_val = int(len(X) * val_frac)
    return X[idx[n_val:]], y[idx[n_val:]], X[idx[:n_val]], y[idx[:n_val]]


def fit_or_load(path, fit_fn, save_fn, load_fn, params):
    path = Path(path)
    if (path / "model.pkl").exists():
        return load_fn(path)
    model = fit_fn()
    save_fn(model, params, path)
    return model


def prepare_mle(Phi, y):
    n, D = Phi.shape
    y = np.asarray(y, dtype=np.float64).ravel()
    out = {"n": n, "D": D, "yty": float(y @ y)}
    if D <= n:                                   # cheaper in feature space
        eigvals, V = scipy.linalg.eigh(Phi.T @ Phi)
        out.update(mode="D", eigvals=np.clip(eigvals, 0.0, None),
                   proj=V.T @ (Phi.T @ y))
    else:                                        # cheaper in sample space
        eigvals, U = scipy.linalg.eigh(Phi @ Phi.T)
        out.update(mode="n", eigvals=np.clip(eigvals, 0.0, None), proj=U.T @ y)
    return out


def log_marginal_likelihood_cached(prepared, alpha):
    n, D, ev = prepared["n"], prepared["D"], prepared["eigvals"]
    if prepared["mode"] == "D":
        quad = float(np.sum(prepared["proj"] ** 2 / (ev + alpha)))
        y_Minv_y = (prepared["yty"] - quad) / alpha
        log_det_M = float(np.sum(np.log(ev + alpha)) + (n - D) * np.log(alpha))
    else:
        y_Minv_y = float(np.sum(prepared["proj"] ** 2 / (ev + alpha)))
        log_det_M = float(np.sum(np.log(ev + alpha)))
    if not np.isfinite(y_Minv_y) or y_Minv_y <= 0:
        return -np.inf
    return -0.5 * (n + n * np.log(y_Minv_y / n) + log_det_M + n * np.log(2 * np.pi))


def log_marginal_likelihood(Phi, y, alpha):
    return log_marginal_likelihood_cached(prepare_mle(Phi, y), alpha)


def normalized_mse(y_pred, y_true):
    return float(np.mean((y_pred - y_true) ** 2) / np.var(y_true))


def relative_error_pct(y_pred, y_true):
    """Mean absolute error as a percentage of std(y_true), stable when y passes through zero."""
    return float(100.0 * np.mean(np.abs(y_pred - y_true)) / np.std(y_true))


def compute_all_metrics(predict, X_val, y_val, X_extrap, y_extrap, ds):
    y_pred_val, y_pred_extrap = predict(X_val), predict(X_extrap)
    val_mse = float(np.mean((y_pred_val - y_val) ** 2))
    extrap_mse = float(np.mean((y_pred_extrap - y_extrap) ** 2))
    return {
        "val_mse": val_mse,
        "extrap_mse": extrap_mse,
        "transfer_coefficient": extrap_mse / val_mse,
        "val_nmse": normalized_mse(y_pred_val, y_val),
        "extrap_nmse": normalized_mse(y_pred_extrap, y_extrap),
        "val_relative_error_pct": relative_error_pct(y_pred_val, y_val),
        "extrap_relative_error_pct": relative_error_pct(y_pred_extrap, y_extrap),
        "Tc_error_pct": 100.0 * abs(ds.critical_point(predict) - ds.TC) / ds.TC,
    }
