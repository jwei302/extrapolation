import numpy as np
import scipy.linalg

N_UNLABELED = 10_000
SEED_P, SEED_Q = 99999, 99


def gram(phi, jitter=0.0):
    G = phi.T @ phi / phi.shape[0]
    G = 0.5 * (G + G.T)
    G[np.diag_indices_from(G)] += jitter
    return G


def gevp_bound(phi_P, phi_Q, jitter):
    """lambda_max(E_Q[phi phi^T], E_P[phi phi^T] + jitter I)."""
    A, B = gram(phi_Q), gram(phi_P, jitter)
    D = B.shape[0]
    return float(scipy.linalg.eigh(A, B, eigvals_only=True,
                                   subset_by_index=[D - 1, D - 1], driver="gvx")[0])


def gevp_population(model, ds, jitter):
    X_P, _ = ds.sample_interp_data(N_UNLABELED, seed=SEED_P)
    X_Q, _ = ds.generate_extrap_data(N=N_UNLABELED, seed=SEED_Q)
    return gevp_bound(*model.bound_features(X_P, X_Q), jitter)


def volume_bound(degree, rho_P, rho_Q):
    return float((2 * degree) ** (2 * degree) * rho_Q * rho_P ** (2 * degree))


def remez_bound(degree, residuals, rho_Q, n_dim=2):
    sq = np.asarray(residuals) ** 2
    return float((4 * n_dim * rho_Q) ** (2 * degree) * sq.max() / sq.mean())
