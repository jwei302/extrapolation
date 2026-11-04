import argparse
import importlib
import json
from pathlib import Path

import numpy as np

from configs import get_config
from data import get_dataset
from eval.bounds import gevp_population
from utils import SEEDS, N_TRAIN, train_val_split, fit_or_load

MODELS_DIR = Path("results/models/distance_sweeps")


def reference_hps(dataset, method):
    d = get_config(dataset).DISTANCES[0]
    return json.load(open(MODELS_DIR / dataset / f"d{d:.2f}" / method / f"seed{SEEDS[0]}_n{N_TRAIN}" / "params.json"))


def pinned_model(method, hps, X_tr, y_tr, path):
    mod = importlib.import_module(f"models.{method}")
    return fit_or_load(path, lambda: mod.from_params(hps).fit(X_tr, y_tr),
                       mod.save_model, mod.load_model, params=hps)


def run(dataset, method):
    ds, cfg = get_dataset(dataset), get_config(dataset)
    jitter = cfg.NUMERICS[f"jitter_{method}"]
    hps = reference_hps(dataset, method)
    rows = []
    for d in cfg.DISTANCES:
        ds.set_distance(d)
        X_q, y_q = ds.generate_extrap_data()
        transfer = []
        for s in SEEDS:
            X, y = ds.sample_interp_data(N_TRAIN, s)
            X_tr, y_tr, X_val, y_val = train_val_split(X, y)
            m = pinned_model(method, hps, X_tr, y_tr,
                             MODELS_DIR / dataset / f"d{d:.2f}" / f"{method}_pinned" / f"seed{s}_n{N_TRAIN}")
            transfer.append(np.mean((m.predict(X_q) - y_q) ** 2) / np.mean((m.predict(X_val) - y_val) ** 2))
            if s == SEEDS[0]:
                gevp = gevp_population(m, ds, jitter)
        rows.append({"d": float(d), "transfer": float(np.exp(np.mean(np.log(transfer)))), "gevp": gevp})
        print(f"  [{dataset}/{method}] d={d:<8.4f} Gamma_emp={rows[-1]['transfer']:.4e}  "
              f"Gamma_GEVP={gevp:.4e}", flush=True)
    return hps, rows


if __name__ == "__main__":
    from data import DATASETS
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", required=True, choices=list(DATASETS))
    ap.add_argument("--method", required=True, choices=["poly", "rff"])
    a = ap.parse_args()
    hps, rows = run(a.dataset, a.method)
    out = Path("results") / f"distance_{a.dataset}_{a.method}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"dataset": a.dataset, "method": a.method,
                               "pinned_hps": hps, "rows": rows}, indent=1))
    print(f"Wrote {out}")
