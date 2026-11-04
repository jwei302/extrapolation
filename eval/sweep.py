import argparse
import importlib

from configs import get_config
from data import DATASETS, get_dataset
from models import KERNEL, MODELS_DIR
from utils import SEEDS, SIZES, N_TRAIN


def run(method, dataset, distance=None, features=None):
    ds, cfg = get_dataset(dataset), get_config(dataset)
    module, config = importlib.import_module(f"models.{method}"), getattr(cfg, method.upper())
    base, cells = MODELS_DIR / dataset / method, [(s, n) for n in SIZES for s in SEEDS]
    if distance is not None:                      # one reference model: its hyperparameters are pinned downstream
        ds.set_distance(distance)
        base, cells = MODELS_DIR / "distance_sweeps" / dataset / f"d{distance:.2f}" / method, [(SEEDS[0], N_TRAIN)]
    if features is not None:                      # RFF at a fixed feature count, for the GP-proxy sweep (Fig. 6)
        base, cells = MODELS_DIR / dataset / f"rff_m{features}", [(s, N_TRAIN) for s in SEEDS]
        config = {**config, "n_features_list": [features]}
    for seed, n in cells:
        path = base / f"seed{seed}_n{n}"
        if (path / "model.pkl").exists():
            continue
        print(f"  [{dataset}/{method}] seed={seed} n={n}", flush=True)
        X, y = ds.sample_interp_data(n, seed)
        model, params = getattr(module, f"train_{method}")(X, y, config)
        module.save_model(model, params, path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--method", required=True, choices=KERNEL)
    ap.add_argument("--dataset", required=True, choices=list(DATASETS))
    ap.add_argument("--distance", type=float)
    ap.add_argument("--features", type=int)
    a = ap.parse_args()
    run(a.method, a.dataset, a.distance, a.features)
