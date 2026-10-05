import json
from pathlib import Path

import numpy as np

from configs import get_config
from data import get_dataset, PAIR
from eval.bounds import gevp_population
from models import load
from utils import SEEDS, N_TRAIN, train_val_split

N_LAB = [5, 10, 20, 50, 100, 200, 500]
N_DRAWS = 200

if __name__ == "__main__":
    rows = []
    for dataset in PAIR:
        ds, cfg = get_dataset(dataset), get_config(dataset)
        X_Q, y_Q = ds.generate_extrap_data()
        for method in ("poly", "rff"):
            for seed in SEEDS:
                model = load(dataset, method, seed)
                _, _, X_val, y_val = train_val_split(*ds.sample_interp_data(N_TRAIN, seed))
                mse_P = float(np.mean((model.predict(X_val) - y_val) ** 2))
                bound = gevp_population(model, ds, cfg.NUMERICS[f"jitter_{method}"]) * mse_P
                mse_Q = float(np.mean((model.predict(X_Q) - y_Q) ** 2))
                rng = np.random.default_rng(seed)
                for n in N_LAB:
                    estimates = []
                    for _ in range(N_DRAWS):
                        X, y = ds.draw(ds.T_EXTRAP, n, rng)
                        estimates.append(float(np.mean((model.predict(X) - y) ** 2)))
                    rows.append({"dataset": dataset, "method": method, "seed": seed, "n_lab": n,
                                 "mse_Q": mse_Q, "bound": bound, "estimates": estimates})
                below = np.mean(np.array(rows[-5]["estimates"]) < mse_Q / 2)
                print(f"  [{dataset}/{method}/seed{seed}] MSE_Q={mse_Q:.3e}  bound={bound:.3e}  "
                      f"P(estimate < MSE_Q / 2 at n_lab=20)={below:.2f}", flush=True)
    Path("results/labeled_budget.json").write_text(json.dumps(rows))
