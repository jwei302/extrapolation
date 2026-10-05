import numpy as np
from pathlib import Path
from data.polaron.diagonalization import polaron_energy, alpha_from_lambda

OMEGA, T, R, M = 3.0, 1.0, 4, 10
K_MAX_FRAC = 0.6
K_GRID = np.linspace(0.0, K_MAX_FRAC * np.pi, 61)
LAMBDAS = np.round(np.arange(0.0, 1.0501, 0.025), 4)
OUT = Path(__file__).parent / "dispersion.npz"

if __name__ == "__main__":
    E = np.empty((len(LAMBDAS), len(K_GRID)))
    for i, lam in enumerate(LAMBDAS):
        a = alpha_from_lambda(float(lam), OMEGA, T)
        for j, K in enumerate(K_GRID):
            E[i, j] = polaron_energy(K, a, OMEGA, R, M, T)
        j0 = int(np.argmin(E[i]))
        print(f"  lambda={lam:6.3f}  K_GS/pi={K_GRID[j0]/np.pi:.4f}  "
              f"E_min={E[i,j0]:+.6f}", flush=True)
    np.savez(OUT, E=E, K=K_GRID, lam=LAMBDAS, omega=OMEGA, t=T, R=R, M=M)
    nz = LAMBDAS[[int(np.argmin(E[i])) > 0 for i in range(len(LAMBDAS))]]
    print(f"\nlambda_c (first nonzero K_GS) = {nz.min() if len(nz) else float('nan')}")
    print(f"wrote {OUT}  E.shape={E.shape}")
