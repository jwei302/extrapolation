import importlib
import json
import warnings
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.signal import savgol_filter

from configs import method_config
from data import get_dataset
from data.arpes.arpes import measurements
from models import KERNEL
from utils import SEEDS, N_TRAIN

A = get_dataset("arpes")
DEFAULTS = {"interp": "linear", "e_lo": -0.10, "smooth": "none",
            "peak": "gaussian", "kwindow": 1}
VARIANTS = {
    "interp": ["linear", "cubic"],
    "e_lo": [-0.08, -0.10, -0.12],
    "smooth": ["none", "savgol"],
    "peak": ["gaussian", "argmax", "parabolic"],
    "kwindow": [0, 1, 2],
}


def build_interpolator(spec):
    d = measurements()
    T, E, grid = d["T"], d["E"], d["I"][spec["kwindow"]]
    if spec["smooth"] == "savgol":
        grid = savgol_filter(grid, window_length=7, polyorder=2, axis=1)
    method = "cubic" if spec["interp"] == "cubic" else "linear"
    return RegularGridInterpolator((T, E), grid, bounds_error=False,
                                   fill_value=None, method=method)


def sample(spec, interp, N, seed, region):
    rng = np.random.default_rng(seed)
    T_range = A.T_INTERP if region == "P" else A.T_EXTRAP
    e_range = (spec["e_lo"], 0.0)
    T = A.sample_T(rng, N, T_range)
    E = rng.uniform(e_range[0], e_range[1], N)
    X = np.column_stack([T, E])
    return X, interp(X)


def _scan(pred_fn, T0, E_lo_meV=-20.0, E_hi_meV=1.0, n=400):
    E_meV = np.linspace(E_lo_meV, E_hi_meV, n)
    X = np.column_stack([np.full_like(E_meV, T0), E_meV / 1000.0])
    return E_meV, pred_fn(X)


def _peak_argmax(pred_fn, T0):
    E_meV, y = _scan(pred_fn, T0)
    return float(E_meV[np.argmax(y)])


def _peak_parabolic(pred_fn, T0):
    E_meV, y = _scan(pred_fn, T0)
    n = len(E_meV)
    i = int(np.argmax(y))
    if i == 0 or i == n - 1:
        return float(E_meV[i])
    y0, y1, y2 = y[i - 1], y[i], y[i + 1]
    denom = (y0 - 2 * y1 + y2)
    if denom == 0:
        return float(E_meV[i])
    delta = 0.5 * (y0 - y2) / denom
    step = E_meV[1] - E_meV[0]
    return float(E_meV[i] + delta * step)


def peak_curve(pred_fn, T_grid, mode):
    fn = {"gaussian": A.peak_energy, "argmax": _peak_argmax, "parabolic": _peak_parabolic}[mode]
    return np.array([fn(pred_fn, float(t)) for t in T_grid])


def fit_methods(X_int, y_int):
    predicts = {}
    for m in KERNEL:
        train = getattr(importlib.import_module(f"models.{m}"), f"train_{m}")
        predicts[m] = train(X_int, y_int, config=method_config("arpes", m))[0].predict
    return predicts


def run():
    warnings.simplefilter("ignore")
    T_grid_full = A.T_grid()
    T_plot = T_grid_full[(T_grid_full >= A.T_EXTRAP[0])
                         & (T_grid_full <= A.T_INTERP[1])]

    specs = [("default", dict(DEFAULTS))]
    for knob, values in VARIANTS.items():
        for v in values:
            if v == DEFAULTS[knob]:
                continue
            s = dict(DEFAULTS)
            s[knob] = v
            specs.append((f"{knob}={v}", s))

    rows, curves, fit_cache = [], {}, {}
    for name, spec in specs:
        interp = build_interpolator(spec)
        curves[name] = {"T": T_plot.tolist(),
                        "truth": peak_curve(interp, T_plot, spec["peak"]).tolist()}
        X_Q, y_Q = sample(spec, interp, 2000, 99, "Q")
        var_Q = float(np.var(y_Q))
        per_method = {m: [] for m in KERNEL}
        key = tuple(spec[k] for k in ("interp", "e_lo", "smooth", "kwindow"))
        for seed in SEEDS:
            if (key, seed) not in fit_cache:
                X_int, y_int = sample(spec, interp, N_TRAIN, seed, "P")
                fit_cache[(key, seed)] = fit_methods(X_int, y_int)
            for m, pred in fit_cache[(key, seed)].items():
                per_method[m].append(float(np.mean((pred(X_Q) - y_Q) ** 2)) / var_Q)
        for m, vals in per_method.items():
            v = np.array(vals)
            rows.append({"variant": name, "method": m,
                         "nmse_Q_mean": float(v.mean()),
                         "nmse_Q_std": float(v.std())})
        print(f"  [{name}] done", flush=True)
    return {"rows": rows, "curves": curves,
            "specs": {n: s for n, s in specs}}


def report(out):
    curves, rows = out["curves"], out["rows"]
    T = np.asarray(curves["default"]["T"])
    lo, hi = int(np.argmin(np.abs(T - 65))), int(np.argmin(np.abs(T - 95)))
    mig = lambda c: abs(c[lo] - c[hi])
    base = np.asarray(curves["default"]["truth"])
    nmse = {(r["variant"], r["method"]): r for r in rows}

    L = ["| variant | max dE* (meV) | d mig. (%) | poly | RFF | GP |",
         "|---|---|---|---|---|---|"]
    for name, c in ((n, np.asarray(v["truth"])) for n, v in curves.items()):
        cells = [f"{nmse[name, m]['nmse_Q_mean']:.3f} ± {nmse[name, m]['nmse_Q_std']:.3f}"
                 for m in KERNEL]
        L.append(f"| {name} | {np.nanmax(np.abs(c - base)):.2f} | "
                 f"{100 * (mig(c) - mig(base)) / mig(base):+.1f} | " + " | ".join(cells) + " |")
    L += ["", f"Default migration |E*(65K) - E*(95K)| = {mig(base):.2f} meV."]
    return "\n".join(L)


if __name__ == "__main__":
    out = run()
    Path("results/arpes_preprocessing.json").write_text(json.dumps(out, indent=1))
    text = report(out)
    Path("results/arpes_preprocessing.txt").write_text(text + "\n")
    print("\n" + text)
