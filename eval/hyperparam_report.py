import json
from pathlib import Path

from data import ORDERED
from models import MODELS_DIR, TARGETS

if __name__ == "__main__":
    lines = []
    for dataset in ORDERED:
        for method, datasets in TARGETS.items():
            if dataset in datasets:
                with open(MODELS_DIR / dataset / method / "seed46_n2000" / "params.json") as f:
                    params = json.load(f)
                lines.append(f"{dataset:16} {method:8} " + ", ".join(f"{k}={v}" for k, v in params.items()))
    Path("results/hyperparams.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
