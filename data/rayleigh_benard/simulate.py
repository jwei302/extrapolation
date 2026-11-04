import sys
from pathlib import Path
import numpy as np

from data.rayleigh_benard.solver import run_rb

HERE = Path(__file__).parent
RUN = HERE / "run"
NPZ = HERE / "profiles.npz"

RA_GRID = np.geomspace(300.0, 3.0e4, 64)
NX, NZ, T_END = 96, 49, 12.0


def run(i):
    RUN.mkdir(exist_ok=True)
    Ra = float(RA_GRID[i])
    r = run_rb(Ra, Nx=NX, Nz=NZ, t_end=T_END, avg_frac=0.6)
    out = RUN / f"rb_{i:03d}.npz"
    if r.get("blewup"):
        print(f"[{i}] Ra={Ra:.1f} BLEW UP")
        np.savez(out, Ra=Ra, blewup=True)
    else:
        print(f"[{i}] Ra={Ra:.1f}  Nu={r['Nu']:.3f}")
        np.savez(out, Ra=Ra, z=r["z"], Tbar=r["Tbar"], Nu=r["Nu"], blewup=False)


def gather():
    files = sorted(RUN.glob("rb_*.npz"))
    Ras, Nus, Tbars, zref = [], [], [], None
    for f in files:
        d = np.load(f)
        if bool(d["blewup"]):
            continue
        Ras.append(float(d["Ra"])); Nus.append(float(d["Nu"]))
        Tbars.append(d["Tbar"]); zref = d["z"]
    order = np.argsort(Ras)
    Ras = np.array(Ras)[order]; Nus = np.array(Nus)[order]
    Tbars = np.array(Tbars)[order]
    np.savez(NPZ, Ra=Ras, z=zref, Tbar=Tbars, Nu=Nus)
    print(f"Saved {NPZ}: {len(Ras)} Ra values, Ra in [{Ras.min():.0f}, {Ras.max():.0f}]")
    print("Nu(Ra):")
    for Ra, Nu in zip(Ras, Nus):
        print(f"  Ra={Ra:8.1f}  Nu={Nu:.3f}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        for i in range(len(RA_GRID)):
            run(i)
        gather()
    elif sys.argv[1] == "gather":
        gather()
    else:
        run(int(sys.argv[1]))
