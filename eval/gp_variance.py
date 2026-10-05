import json
import warnings
from pathlib import Path

from data import get_dataset, PAIR
from models import load
from utils import SEEDS

N_GRID = 100


def error_and_variance(model, ds):
    TT, MM, y, X = ds.eval_grid(N_GRID, N_GRID)
    mu, sd = model.gp.predict(model.scaler.transform(X), return_std=True)
    return {"T": TT[0].tolist(),
            "err2": ((y.ravel() - mu) ** 2).reshape(TT.shape).mean(axis=0).tolist(),
            "var": (sd ** 2).reshape(TT.shape).mean(axis=0).tolist()}


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    out = {}
    for dataset in PAIR:
        ds = get_dataset(dataset)
        out[dataset] = {"Tc": ds.TC, "T_interp": list(ds.T_INTERP),
                        "curves": [error_and_variance(load(dataset, "gp", s), ds) for s in SEEDS]}
        print(f"  [{dataset}] done", flush=True)
    Path("results/gp_variance.json").write_text(json.dumps(out, indent=1))
