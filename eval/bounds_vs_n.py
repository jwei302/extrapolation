import argparse
import json
from pathlib import Path

import numpy as np

from configs import get_config
from data import get_dataset
from eval.bounds import gevp_population, volume_bound, remez_bound
from eval.distance import reference_hps, pinned_model
from utils import SEEDS, SIZES, train_val_split

MODELS_DIR = Path("results/models")


def bounds_vs_n(dataset, method):
    ds, cfg = get_dataset(dataset), get_config(dataset)
    hps = reference_hps(dataset, method)
    X_extrap, y_extrap = ds.generate_extrap_data()

    def model_at(seed, n):
        X, y = ds.sample_interp_data(n, seed)
        X_tr, y_tr, X_val, y_val = train_val_split(X, y)
        m = pinned_model(method, hps, X_tr, y_tr,
                         MODELS_DIR / dataset / f"{method}_pinned" / f"seed{seed}_n{n}")
        return m, X, y, X_val, y_val

    gevp = gevp_population(model_at(SEEDS[0], max(SIZES))[0], ds, cfg.NUMERICS[f"jitter_{method}"])

    out = {"dataset": dataset, "method": method, "pinned_hps": hps, "n": SIZES}
    for n in SIZES:
        rows = []
        for seed in SEEDS:
            m, X, y, X_val, y_val = model_at(seed, n)
            val_mse = np.mean((m.predict(X_val) - y_val) ** 2)
            row = {"transfer_coefficient": float(np.mean((m.predict(X_extrap) - y_extrap) ** 2) / val_mse),
                   "gevp_bound": gevp}
            if method == "poly":
                row["volume_bound"] = volume_bound(hps["degree"], ds.RHO_P, ds.RHO_Q)
                row["remez_bound"] = remez_bound(hps["degree"], m.predict(X) - y, ds.RHO_Q)
            rows.append(row)
        for k in rows[0]:
            out.setdefault(k, []).append([r[k] for r in rows])
        print(f"  [{dataset}/{method}] n={n}: {len(rows)} seeds", flush=True)
    return out


if __name__ == "__main__":
    from data import DATASETS
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", required=True, choices=list(DATASETS))
    ap.add_argument("--method", required=True, choices=["poly", "rff"])
    a = ap.parse_args()
    out = Path("results") / f"bounds_vs_n_{a.dataset}_{a.method}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(bounds_vs_n(a.dataset, a.method), indent=1))
    print(f"Wrote {out}")
