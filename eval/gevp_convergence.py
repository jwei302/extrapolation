import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import scipy.linalg

from configs import get_config
from data import get_dataset
from eval.bounds import N_UNLABELED
from models import load

RESULTS = Path("results/gevp_convergence")
SIZES = {"poly": [200, 500, 1000, 2000, 5000, 10000, 30000, 100000, 300000],
         "rff":  [200, 500, 1000, 2000, 5000, 10000, 30000, 100000]}

REF = {("heisenberg", "poly"): dict(n=12_000_000, eps=0.05),
       ("arpes", "poly"):      dict(n=12_000_000, eps=0.05),
       ("arpes", "rff"):       dict(n=16_000_000, eps=0.10),
       ("heisenberg", "rff"):  dict(n=1_000_000, eps=None)}
REPS_SMALL, REPS_LARGE = 10, 3
CHUNK = 25_000


def _gram(fn, X, jitter=0.0):
    G, n = None, X.shape[0]
    for i in range(0, n, CHUNK):
        phi = fn(X[i:i + CHUNK])
        G = phi.T @ phi if G is None else G + phi.T @ phi
    G /= n
    G = 0.5 * (G + G.T)
    if jitter:
        G[np.diag_indices_from(G)] += jitter
    return G


def _gamma_qr(fn, X_P, X_Q, jitter):
    """lambda_max(A, B + jitter I) via QR of the stacked features."""
    n_P = X_P.shape[0]
    Phi_P = fn(X_P) / np.sqrt(n_P)
    D = Phi_P.shape[1]
    M = np.vstack([Phi_P, np.sqrt(jitter) * np.eye(D)])
    R = np.linalg.qr(M, mode="r")
    n_Q = X_Q.shape[0]
    C = np.zeros((D, D))
    for i in range(0, n_Q, CHUNK):
        Z = scipy.linalg.solve_triangular(R, fn(X_Q[i:i + CHUNK]).T,
                                          trans="T", lower=False)
        C += Z @ Z.T
    C = 0.5 * (C + C.T) / n_Q
    return float(scipy.linalg.eigh(C, eigvals_only=True,
                                   subset_by_index=[D - 1, D - 1])[0])


def _gamma(fn, X_P, X_Q, jitter):
    """lambda_max(A, B + jitter I) from chunked Grams."""
    A, B = _gram(fn, X_Q), _gram(fn, X_P, jitter)
    s = 1.0 / np.sqrt(np.diag(B))
    A = s[:, None] * A * s[None, :]
    B = s[:, None] * B * s[None, :]
    D = B.shape[0]
    try:
        return float(scipy.linalg.eigh(A, B, eigvals_only=True,
                                       subset_by_index=[D - 1, D - 1],
                                       driver="gvx")[0])
    except np.linalg.LinAlgError:             
        w = scipy.linalg.eig(A, B, right=False)
        w = w.real[np.isfinite(w.real)]
        return float(w.max())


def run(dataset, method):
    warnings.simplefilter("ignore")
    ds, cfg = get_dataset(dataset), get_config(dataset)
    jitter = cfg.NUMERICS[f"jitter_{method}"]
    fn = load(dataset, method).features
    D_feat = fn(np.array([[np.mean(ds.T_INTERP), np.mean(ds.M_RANGE)]])).shape[1]
    gamma = _gamma_qr if D_feat <= 500 else _gamma     
    sizes = SIZES[method]
    ref = REF[(dataset, method)]
    n_ref = ref["n"]
    out = {"dataset": dataset, "method": method, "D_feat": int(D_feat),
           "jitter": jitter, "n_ref": n_ref, "N_used": N_UNLABELED,
           "ref_certified_eps": ref["eps"]}
    print(f"  [{dataset}/{method}] D_feat={D_feat} jitter={jitter:g} "
          f"ref N={n_ref} certified_eps={ref['eps']}", flush=True)

    XP, _ = ds.sample_interp_data(n_ref, seed=500001)
    XQ, _ = ds.generate_extrap_data(N=n_ref, seed=700001)
    g_ref = gamma(fn, XP, XQ, jitter)
    print(f"    reference Gamma = {g_ref:.6e}", flush=True)
    if ref["eps"] is None:
        XP2, _ = ds.sample_interp_data(n_ref, seed=510001)
        XQ2, _ = ds.generate_extrap_data(N=n_ref, seed=710001)
        g_ref2 = gamma(fn, XP2, XQ2, jitter)
        out["ref_pair_disagreement"] = float(abs(g_ref - g_ref2) / abs(g_ref))
        print(f"    2nd reference   = {g_ref2:.6e}  pair disagreement = "
              f"{out['ref_pair_disagreement']:.3e}", flush=True)
    conv = []
    for n in sizes:
        k = REPS_SMALL if n < sizes[-1] else REPS_LARGE
        for rep in range(k):
            XP, _ = ds.sample_interp_data(n, seed=500000 + 977 * rep)
            XQ, _ = ds.generate_extrap_data(N=n, seed=700000 + 977 * rep)
            g = gamma(fn, XP, XQ, jitter)
            conv.append({"n_mc": n, "rep": rep, "gamma": g,
                         "rel": abs(g - g_ref) / abs(g_ref)})
        r = [c["rel"] for c in conv if c["n_mc"] == n]
        print(f"    N={n:>7d}  N/D={n/D_feat:7.2f}  median rel err={np.median(r):.4e}", flush=True)
    out["gamma_ref"] = g_ref
    out["convergence"] = conv

    dist = []
    for d in cfg.DISTANCES:
        ds.set_distance(float(d))
        XP, _ = ds.sample_interp_data(n_ref, seed=500001)
        XQ, _ = ds.generate_extrap_data(N=n_ref, seed=700001)
        gr = gamma(fn, XP, XQ, jitter)
        rr = []
        for rep in range(REPS_SMALL):
            XP, _ = ds.sample_interp_data(N_UNLABELED, seed=500000 + 977 * rep)
            XQ, _ = ds.generate_extrap_data(N=N_UNLABELED, seed=700000 + 977 * rep)
            rr.append(abs(gamma(fn, XP, XQ, jitter) - gr) / abs(gr))
        dist.append({"d": float(d), "gamma_ref": gr,
                     "rels": [float(x) for x in rr],
                     "rel_median": float(np.median(rr)),
                     "rel_mean": float(np.mean(rr)),
                     "rel_p05": float(np.percentile(rr, 5)),
                     "rel_p95": float(np.percentile(rr, 95))})
        print(f"    d={d:8.4f}  rel err at N={N_UNLABELED}: {np.median(rr):.4e}", flush=True)
    out["distance"] = dist

    RESULTS.mkdir(parents=True, exist_ok=True)
    p = RESULTS / f"{dataset}_{method}.json"
    p.write_text(json.dumps(out, indent=1, default=str))
    print(f"  wrote {p}", flush=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--method", required=True, choices=list(SIZES))
    a = ap.parse_args()
    run(a.dataset, a.method)
