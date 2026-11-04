import numpy as np



def _laplacian_stack(Nz, dz, kx2):
    L = np.zeros((kx2.size, Nz, Nz))
    main = -2.0 / dz ** 2
    off = 1.0 / dz ** 2
    idx = np.arange(1, Nz - 1)
    L[:, idx, idx - 1] = off
    L[:, idx, idx] = main - kx2[:, None]
    L[:, idx, idx + 1] = off
    return L


def _cn_inverses(Nz, L, coef, dt):
    I = np.eye(Nz)[None]
    A = I - (dt / 2.0) * coef * L
    B = I + (dt / 2.0) * coef * L
    A[:, 0, :] = 0.0; A[:, 0, 0] = 1.0
    A[:, -1, :] = 0.0; A[:, -1, -1] = 1.0
    return np.linalg.inv(A), B


def run_rb(Ra, Pr=1.0, aspect=2.0, Nx=128, Nz=65, cfl=0.3,
           t_end=25.0, avg_frac=0.5, seed=0):
    rng = np.random.default_rng(seed)
    Lx = aspect
    z = np.linspace(0.0, 1.0, Nz)
    dz = z[1] - z[0]
    dx = Lx / Nx
    kx = 2 * np.pi * np.fft.rfftfreq(Nx, d=dx)
    Nkx = kx.size
    kx2 = kx ** 2
    ik = 1j * kx[:, None]
    U = max(np.sqrt(Ra * Pr), 5.0)
    dt = float(min(2e-3, cfl * min(dx, dz) / U))
    dealias = (kx <= (2.0 / 3.0) * kx.max())[:, None]

    L = _laplacian_stack(Nz, dz, kx2)
    Ainv_t, B_t = _cn_inverses(Nz, L, 1.0, dt)
    Ainv_w, B_w = _cn_inverses(Nz, L, Pr, dt)
    # Poisson: lap psi = -W, psi=0 at walls
    P = L.copy()
    P[:, 0, 0] = 1.0; P[:, -1, -1] = 1.0
    Pinv = np.linalg.inv(P)

    def bmv(M, v):          # batched matrix-vector over the kx axis
        return np.einsum('kij,kj->ki', M, v)

    theta = (1.0 - z)[None, :] * np.ones((Nx, 1))
    theta += 1e-2 * np.sin(np.pi * z)[None, :] * rng.standard_normal((Nx, 1))
    th = np.fft.rfft(theta, axis=0)
    W = np.zeros((Nkx, Nz), dtype=complex)

    def dz_c(fh):
        g = np.empty_like(fh)
        g[:, 1:-1] = (fh[:, 2:] - fh[:, :-2]) / (2 * dz)
        g[:, 0] = (fh[:, 1] - fh[:, 0]) / dz
        g[:, -1] = (fh[:, -1] - fh[:, -2]) / dz
        return g

    def nonlin(W, th):
        rhs = -W.copy(); rhs[:, 0] = 0.0; rhs[:, -1] = 0.0
        psih = bmv(Pinv, rhs)
        up = np.fft.irfft(dz_c(psih), n=Nx, axis=0)
        wv = -(ik * psih)
        wp = np.fft.irfft(wv, n=Nx, axis=0)

        def adv(fh):
            fx = np.fft.irfft(ik * fh, n=Nx, axis=0)
            fz = np.fft.irfft(dz_c(fh), n=Nx, axis=0)
            return np.fft.rfft(up * fx + wp * fz, axis=0)
        NW = -adv(W) * dealias + Pr * Ra * (ik * th)
        NT = -adv(th) * dealias
        return NW, NT, wv

    bc_t_lo = np.zeros(Nkx, complex); bc_t_lo[0] = 1.0 * Nx
    nsteps = int(t_end / dt)
    t_avg = avg_frac * t_end
    Tsum = np.zeros(Nz); Nu_sum = 0.0; navg = 0
    NW_o = NT_o = None
    for step in range(nsteps):
        NW, NT, wv = nonlin(W, th)
        eT = dt * (1.5 * NT - 0.5 * NT_o) if NT_o is not None else dt * NT
        eW = dt * (1.5 * NW - 0.5 * NW_o) if NW_o is not None else dt * NW
        rt = bmv(B_t, th) + eT
        rt[:, 0] = bc_t_lo; rt[:, -1] = 0.0
        th = bmv(Ainv_t, rt)
        rw = bmv(B_w, W) + eW
        rw[:, 0] = 0.0; rw[:, -1] = 0.0
        W = bmv(Ainv_w, rw)
        NW_o, NT_o = NW, NT
        if not np.all(np.isfinite(th)):
            return dict(Ra=Ra, blewup=True)
        if step * dt >= t_avg:
            Tsum += np.fft.irfft(th, n=Nx, axis=0).mean(axis=0)
            wp = np.fft.irfft(wv, n=Nx, axis=0)
            tp = np.fft.irfft(th, n=Nx, axis=0)
            Nu_sum += 1.0 + np.trapezoid((wp * tp).mean(axis=0), z)
            navg += 1
    return dict(Ra=Ra, z=z, Tbar=Tsum / max(navg, 1),
                Nu=float(Nu_sum / max(navg, 1)), blewup=False, dt=dt, nsteps=nsteps)


if __name__ == "__main__":
    import time
    for Ra in [300.0, 700.0, 1000.0, 2000.0, 5000.0, 1e4]:
        t0 = time.time()
        r = run_rb(Ra, t_end=20.0, Nx=96, Nz=49)
        dt_wall = time.time() - t0
        if r.get("blewup"):
            print(f"Ra={Ra:8.0f}: BLEW UP  ({dt_wall:.1f}s)")
        else:
            print(f"Ra={Ra:8.0f}  Nu={r['Nu']:.3f}  ({dt_wall:.1f}s, {r['nsteps']} steps)")
