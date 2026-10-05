import json
from pathlib import Path

import numpy as np

from data import PAIR, get_dataset
from models import load
from utils import SEEDS, SIZES, N_TRAIN, train_val_split

M_LIST = [500, 1000, 2000, 4000, 8000, 16000]      # feature counts of the RFF sweep train.py runs on PAIR


def transfer(model, ds, seed, n, X_extrap, y_extrap):
    _, _, X_val, y_val = train_val_split(*ds.sample_interp_data(n, seed))
    return float(np.mean((model.predict(X_extrap) - y_extrap) ** 2) / np.mean((model.predict(X_val) - y_val) ** 2))


if __name__ == "__main__":
    for dataset in PAIR:
        ds = get_dataset(dataset)
        X_extrap, y_extrap = ds.generate_extrap_data()
        out = {"m": {m: [transfer(load(dataset, "rff", s, subdir=f"rff_m{m}"), ds, s, N_TRAIN, X_extrap, y_extrap)
                         for s in SEEDS] for m in M_LIST}}
        for method in ("rff", "gp"):
            out[method] = {n: [transfer(load(dataset, method, s, n), ds, s, n, X_extrap, y_extrap) for s in SEEDS]
                           for n in SIZES}
        Path(f"results/gp_vs_rff_{dataset}.json").write_text(json.dumps(out, indent=1))
        print(f"  [{dataset}] done", flush=True)
