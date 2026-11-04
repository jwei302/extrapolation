import json
import pickle
import warnings
from pathlib import Path

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from models import train_cli
from utils import train_val_split, log_marginal_likelihood


class AxisPolynomialFeatures(BaseEstimator, TransformerMixin):

    def __init__(self, axis_degrees=(1, 10)):
        self.axis_degrees = tuple(axis_degrees)

    @property
    def degree(self):
        return int(sum(self.axis_degrees))

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        d0, d1 = self.axis_degrees
        x0, x1 = X[:, 0], X[:, 1]
        return np.column_stack([(x0 ** a) * (x1 ** b)
                                for a in range(d0 + 1) for b in range(d1 + 1) if a + b > 0])


class PolyModel(Pipeline):

    def features(self, X):
        return self[:-1].transform(X)

    def bound_features(self, X_P, X_Q):
        """An axis-restricted fit is bounded over the enclosing total-degree class, scaled by its P-draw RMS."""
        poly = self.named_steps["poly"]
        if not isinstance(poly, AxisPolynomialFeatures):
            return self.features(X_P), self.features(X_Q)
        phi = PolynomialFeatures(degree=poly.degree, include_bias=False).fit(X_P).transform
        phi_P, phi_Q = phi(X_P), phi(X_Q)
        scale = 1 / np.sqrt(np.mean(phi_P ** 2, axis=0))
        return phi_P * scale, phi_Q * scale


def from_params(params):
    poly = (AxisPolynomialFeatures(params["axis_degrees"]) if params.get("axis_degrees")
            else PolynomialFeatures(degree=params["degree"], include_bias=False))
    return PolyModel([("poly", poly), ("scaler", StandardScaler()),
                      ("ridge", Ridge(alpha=params["alpha"], fit_intercept=True))])


def train_poly(X_interp, y_interp, config, ds=None):
    X_tr, y_tr, X_val, y_val = train_val_split(X_interp, y_interp)
    y_tr_centered = y_tr - np.mean(y_tr)
    bases = ([{"axis_degrees": list(ad)} for ad in config["axis_degrees"]]
             if config.get("axis_degrees") else [{"degree": d} for d in config["degrees"]])

    best, best_logml = None, -np.inf
    for basis in bases:
        for alpha in config["alphas"]:
            params = {**basis, "alpha": alpha}
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = from_params(params).fit(X_tr, y_tr)
                y_pred = model.predict(X_val)
            if not np.all(np.isfinite(y_pred)):
                continue
            logml = log_marginal_likelihood(model.features(X_tr), y_tr_centered, alpha)
            if np.isfinite(logml) and logml > best_logml:
                best_logml = logml
                best = (model, params, float(np.mean((y_pred - y_val) ** 2)))

    model, params, val_mse = best
    params.update(degree=model.named_steps["poly"].degree,
                  log_marginal_likelihood=float(best_logml), val_mse=val_mse)
    print(f"Polynomial best: {params}")
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
    train_cli("Train polynomial model", "POLY",
              train_poly, save_model)
