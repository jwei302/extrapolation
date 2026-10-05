import json
import pickle
import warnings
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler

from models import train_cli
from utils import train_val_split, prepare_mle, log_marginal_likelihood_cached


class RFFModel:

    def __init__(self, n_features, length_scales, alpha, seed=0):
        self.n_features = n_features
        self.length_scales = np.asarray(length_scales, dtype=np.float64)
        self.alpha = alpha
        self.seed = seed
        self.scaler = StandardScaler()

    def fit(self, X, y):
        self.scaler.fit(X)
        rng = np.random.default_rng(self.seed)
        self.W_ = rng.standard_normal((X.shape[1], self.n_features)) / self.length_scales[:, None]
        self.b_ = rng.uniform(0, 2 * np.pi, self.n_features)
        self.ridge_ = Ridge(alpha=self.alpha, fit_intercept=True).fit(self.features(X), y)
        return self

    def features(self, X):
        return np.sqrt(2 / self.n_features) * np.cos(self.scaler.transform(X) @ self.W_ + self.b_)

    def bound_features(self, X_P, X_Q):
        return self.features(X_P), self.features(X_Q)

    def predict(self, X):
        return self.ridge_.predict(self.features(X))


def from_params(params):
    return RFFModel(params["n_features"],
                    [params["length_scale_T"], params["length_scale_m"]], params["alpha"])


def train_rff(X_interp, y_interp, config, ds=None):
    n_features_list, alphas, n_rff_seeds = config["n_features_list"], config["alphas"], config["n_rff_seeds"]
    subset = X_interp[np.random.default_rng(0).choice(len(X_interp), min(200, len(X_interp)), replace=False)]
    median_dist = np.median(pairwise_distances(StandardScaler().fit_transform(subset)))
    ls_T_list = [median_dist * f for f in config["ls_T_factors"]]
    ls_m_list = [median_dist * f for f in config["ls_m_factors"]]

    X_tr, y_tr, X_val, y_val = train_val_split(X_interp, y_interp)
    y_tr_centered = y_tr - np.mean(y_tr)

    scaler = StandardScaler().fit(X_tr)
    X_tr_scaled = scaler.transform(X_tr)
    d = X_tr.shape[1]

    best_avg_logml = -np.inf
    best_params = {}

    total = len(n_features_list) * len(ls_T_list) * len(ls_m_list) * len(alphas)
    count = 0

    for n_feat in n_features_list:
        for ls_T in ls_T_list:
            for ls_m in ls_m_list:
                prepared_list = []
                length_scales = np.asarray([ls_T, ls_m], dtype=np.float64)
                for rff_seed in range(n_rff_seeds):
                    rng = np.random.default_rng(rff_seed)
                    W = rng.standard_normal((d, n_feat)) / length_scales[:, None]
                    b = rng.uniform(0, 2 * np.pi, n_feat)
                    Z_tr = np.sqrt(2 / n_feat) * np.cos(X_tr_scaled @ W + b)
                    prepared_list.append(prepare_mle(Z_tr, y_tr_centered))

                for a in alphas:
                    count += 1
                    logmls = [log_marginal_likelihood_cached(p, a) for p in prepared_list]
                    logmls = [v for v in logmls if np.isfinite(v)]
                    if not logmls:
                        continue
                    avg_logml = float(np.mean(logmls))

                    if avg_logml > best_avg_logml:
                        best_avg_logml = avg_logml
                        best_params = {
                            "n_features": n_feat,
                            "length_scale_T": ls_T,
                            "length_scale_m": ls_m,
                            "alpha": a,
                        }

                    if count % 100 == 0:
                        print(f"  [{count}/{total}] best avg log ML so far: {best_avg_logml:.2f}")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        best_model = RFFModel(
            best_params["n_features"],
            [best_params["length_scale_T"], best_params["length_scale_m"]],
            best_params["alpha"],
            seed=0,
        )
        best_model.fit(X_tr, y_tr)
        y_pred_val = best_model.predict(X_val)
    best_val_mse = (float(np.mean((y_pred_val - y_val) ** 2))
                    if np.all(np.isfinite(y_pred_val)) else float("inf"))

    best_params["log_marginal_likelihood"] = best_avg_logml
    best_params["val_mse"] = best_val_mse
    print(f"RFF best: n_features={best_params['n_features']}, "
          f"ls_T={best_params['length_scale_T']:.3f}, "
          f"ls_m={best_params['length_scale_m']:.3f}, "
          f"alpha={best_params['alpha']:.1e}, "
          f"avg log ML={best_avg_logml:.2f}, val MSE={best_val_mse:.2e}")

    return best_model, best_params


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
    train_cli("Train RFF model", "RFF",
              train_rff, save_model)
