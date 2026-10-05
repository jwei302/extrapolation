import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


def build_basis(R, M):
    sites = 2 * R + 1
    cfgs = []

    def rec(pos, left, acc):
        if pos == sites - 1:
            cfgs.append(tuple(acc + [left * 0]) if False else tuple(acc + [0]))
            for n in range(1, left + 1):
                cfgs.append(tuple(acc + [n]))
            return
        for n in range(left + 1):
            rec(pos + 1, left - n, acc + [n])

    rec(0, M, [])
    return cfgs, {c: i for i, c in enumerate(cfgs)}


def _shift(cfg, s, R):
    sites = 2 * R + 1
    out = [0] * sites
    for i, n in enumerate(cfg):
        if n == 0:
            continue
        j = i + s
        if j < 0 or j >= sites:
            return None
        out[j] = n
    return tuple(out)


def build_H(K, alpha, Omega, R, M, t=1.0):
    cfgs, index = build_basis(R, M)
    dim = len(cfgs)
    rows, cols, vals = [], [], []
    eK_m, eK_p = np.exp(-1j * K), np.exp(1j * K)

    for a, cfg in enumerate(cfgs):
        rows.append(a); cols.append(a); vals.append(Omega * sum(cfg))

        for s, phase in ((-1, eK_m), (+1, eK_p)):
            shifted = _shift(cfg, s, R)
            if shifted is None:
                continue
            # kinetic
            b = index[shifted]
            rows.append(b); cols.append(a); vals.append(-t * phase)
            # coupling: (u_0 - u_{-1}) for s=-1 ; (u_{+1} - u_0) for s=+1
            d_plus, d_minus = ((0, -1) if s == -1 else (+1, 0))
            for d, sign in ((d_plus, +1.0), (d_minus, -1.0)):
                i = d + R
                n = shifted[i]
                # annihilate
                if n > 0:
                    tgt = list(shifted); tgt[i] = n - 1
                    b2 = index[tuple(tgt)]
                    rows.append(b2); cols.append(a)
                    vals.append(sign * alpha * phase * np.sqrt(n))
                # create
                if sum(shifted) < M:
                    tgt = list(shifted); tgt[i] = n + 1
                    b2 = index[tuple(tgt)]
                    rows.append(b2); cols.append(a)
                    vals.append(sign * alpha * phase * np.sqrt(n + 1))
    H = sp.coo_matrix((vals, (rows, cols)), shape=(dim, dim), dtype=complex).tocsr()
    return H, dim


def ground_energy(K, alpha, Omega, R, M, t=1.0):
    H, dim = build_H(K, alpha, Omega, R, M, t)
    if dim < 200:
        return float(np.linalg.eigvalsh(H.toarray())[0])
    return float(spla.eigsh(H, k=1, which="SA", return_eigenvectors=False,
                            maxiter=5000, tol=1e-10)[0])


def alpha_from_lambda(lam, Omega, t=1.0):
    return np.sqrt(lam * t * Omega / 2.0)


def lanczos_coeffs(H, seed, n_iter=300, tol=1e-12):
    v_prev = np.zeros_like(seed)
    v = seed / np.linalg.norm(seed)
    a_list, b_list = [], []
    b = 0.0
    for _ in range(n_iter):
        w = H @ v
        a = float(np.real(np.vdot(v, w)))
        a_list.append(a)
        w = w - a * v - b * v_prev
        b = float(np.linalg.norm(w))
        if b < tol:
            break
        b_list.append(b)
        v_prev, v = v, w / b
    return np.array(a_list), np.array(b_list)


def green(z, a, b):
    g = np.zeros_like(np.asarray(z, dtype=complex))
    for i in range(len(a) - 1, -1, -1):
        bb = b[i] ** 2 if i < len(b) else 0.0
        g = 1.0 / (z - a[i] - bb * g)
    return g


def polaron_energy(K, alpha, Omega, R, M, t=1.0, eta=1e-3, n_iter=300,
                   w_pad=1.0, n_w=40001, weight_frac=1e-3):
    H, dim = build_H(K, alpha, Omega, R, M, t)
    seed = np.zeros(dim, dtype=complex)
    cfgs, index = build_basis(R, M)
    seed[index[tuple([0] * (2 * R + 1))]] = 1.0
    a, b = lanczos_coeffs(H, seed, n_iter=min(n_iter, dim))
    lo = float(a.min() - abs(b).max() - w_pad) if len(b) else float(a.min() - w_pad)
    w = np.linspace(lo, lo + 2 * w_pad + 4 * t + Omega * M, n_w)
    A = -np.imag(green(w + 1j * eta, a, b)) / np.pi
    thresh = weight_frac * A.max()
    for i in range(1, len(w) - 1):
        if A[i] > thresh and A[i] >= A[i - 1] and A[i] > A[i + 1]:
            y0, y1, y2 = A[i - 1], A[i], A[i + 1]
            den = y0 - 2 * y1 + y2
            dx = 0.5 * (y0 - y2) / den if den != 0 else 0.0
            return float(w[i] + dx * (w[1] - w[0]))
    return float(w[int(np.argmax(A))])
