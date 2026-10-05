import json
from pathlib import Path

import numpy as np

from data import get_dataset
from models import load
from utils import SEEDS

STEP = 1e-3          # finite-difference step in m


def landau_coefficient(predict, T):
    at = lambda m: predict(np.column_stack([T, np.full_like(T, m)]))
    return 0.5 * (at(STEP) - 2 * at(0.0) + at(-STEP)) / STEP ** 2


if __name__ == "__main__":
    ds = get_dataset("heisenberg")
    T = np.linspace(*ds.T_FULL, 401)
    out = {"T": T.tolist()}
    for name, predicts in (("truth", [ds.truth]),
                           ("poly", [load("heisenberg", "poly", s).predict for s in SEEDS]),
                           ("graybox", [load("heisenberg", "graybox", s).predict for s in SEEDS])):
        a = np.mean([landau_coefficient(p, T) for p in predicts], axis=0)
        op = np.mean([ds.order_parameter_curve(p, T) for p in predicts], axis=0)
        out[name] = {"a": a.tolist(), "order_parameter": op.tolist()}
        cross = np.flatnonzero(np.diff(np.sign(a)))
        print(f"  {name:8} a(T) changes sign at T=" + (", ".join(f"{T[i]:.3f}" for i in cross) or "never"))
    Path("results/landau_coeff.json").write_text(json.dumps(out, indent=1))
