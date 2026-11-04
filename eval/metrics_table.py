import argparse
import json
from pathlib import Path

import numpy as np

from data import DATASETS, get_dataset
from models import METHODS, MAIN, NEURAL, load
from utils import SEEDS, N_TRAIN, compute_all_metrics, train_val_split

PRESETS = {"main": MAIN, "neural": NEURAL}
COLUMNS = [("val_nmse", "Val NMSE", ".3e", ".1e"), ("extrap_nmse", "Extrap NMSE", ".3e", ".1e"),
           ("val_relative_error_pct", "Val Rel%", ".2f", ".2f"), ("extrap_relative_error_pct", "Extrap Rel%", ".2f", ".2f"),
           ("transfer_coefficient", "Transfer", ".3e", ".1e"), ("Tc_error_pct", "|dTc|/Tc %", ".2f", ".2f")]


def per_seed(dataset, methods):
    ds = get_dataset(dataset)
    X_extrap, y_extrap = ds.generate_extrap_data()
    out = {}
    for seed in SEEDS:
        X, y = ds.sample_interp_data(N_TRAIN, seed)
        _, _, X_val, y_val = train_val_split(X, y)
        out[seed] = {m: compute_all_metrics(load(dataset, m, seed).predict, X_val, y_val, X_extrap, y_extrap, ds)
                     for m in methods}
    return out


def table(rows, methods):
    lines = [f"{'Method':<18}" + "".join(f"{head:>22}" for _, head, _, _ in COLUMNS)]
    for m in methods:
        cells = []
        for key, _, mean_fmt, std_fmt in COLUMNS:
            v = np.array([r[m][key] for r in rows.values()])
            v = v[np.isfinite(v)]
            cells.append(f"{v.mean():{mean_fmt}}+-{v.std():{std_fmt}}" if len(v) else "nan")
        lines.append(f"{METHODS[m]:<18}" + "".join(f"{c:>22}" for c in cells))
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", required=True, choices=list(DATASETS))
    ap.add_argument("--methods", default="main", choices=list(PRESETS))
    a = ap.parse_args()
    methods = PRESETS[a.methods]
    rows = per_seed(a.dataset, methods)
    text = table(rows, methods)
    print(text)
    out = Path("results") / a.dataset
    out.mkdir(parents=True, exist_ok=True)
    (out / f"metrics_table_{a.methods}.txt").write_text(text + "\n")
    (out / f"metrics_per_seed_{a.methods}.json").write_text(json.dumps(rows, indent=1))
