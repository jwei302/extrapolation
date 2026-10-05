import importlib
from pathlib import Path

from data import ORDERED, PAIR

MODELS_DIR = Path("results/models")
METHODS = {"poly": "Polynomial", "rff": "RFF", "gp": "Gaussian Process", "mlp": "MLP",
           "ff_mlp": "FF-MLP", "siren": "SIREN", "pinn": "PINN", "graybox": "Gray-box"}
KERNEL = ["poly", "rff", "gp"]
MAIN = KERNEL + ["mlp"]
NEURAL = ["mlp", "ff_mlp", "siren", "pinn", "graybox"]
TARGETS = {m: (PAIR if m in NEURAL[1:] else ORDERED) for m in METHODS}     # datasets each method runs on


def load(dataset, method, seed=46, n=2000, subdir=None):
    module = importlib.import_module(f"models.{method}")
    return module.load_model(MODELS_DIR / dataset / (subdir or method) / f"seed{seed}_n{n}")


def train_cli(description, config_key, train_fn, save_fn, datasets=None):
    import argparse
    from data import DATASETS, get_dataset
    from configs import get_config
    from utils import compute_all_metrics, train_val_split

    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--dataset", default="heisenberg",
                    choices=list(datasets or DATASETS))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--results-subdir", default=config_key.lower())
    a = ap.parse_args()

    ds, cfg = get_dataset(a.dataset), get_config(a.dataset)
    out_dir = MODELS_DIR / a.dataset / a.results_subdir / f"seed{a.seed}_n{a.n}"
    X, y = ds.sample_interp_data(a.n, a.seed)
    X_extrap, y_extrap = ds.generate_extrap_data()

    model, params = train_fn(X, y, getattr(cfg, config_key), ds)
    save_fn(model, params, out_dir)

    _, _, X_val, y_val = train_val_split(X, y)
    m = compute_all_metrics(model.predict, X_val, y_val, X_extrap, y_extrap, ds)
    print(f"\n  Val NMSE:     {m['val_nmse']:.4e}")
    print(f"  Extrap NMSE:  {m['extrap_nmse']:.4e}")
    print(f"  Extrap Rel %: {m['extrap_relative_error_pct']:.2f}")
    print(f"  Transfer:     {m['transfer_coefficient']:.2f}")

