import numpy as np
from pathlib import Path

HERE = Path(__file__).parent

E_J0 = -0.371173
E_STEP = 0.001
N_E = 511
N_T = 100


def load_T(path=None):
    return np.loadtxt(path or HERE / "T_list.txt", skiprows=1)


def _parse_row(raw_line):
    fields = raw_line.split("\t")
    out = np.full(len(fields), np.nan, dtype=np.float64)
    for i, f in enumerate(fields):
        f = f.strip()
        if f:
            out[i] = float(f)
    return out


def load_intensity_blocks(path=None):
    path = path or HERE / "Tdep_EDC_AN_3momenta.txt"
    raw = path.read_text().splitlines()

    windows = {}
    i = 0
    while i < len(raw):
        line = raw[i]
        stripped = line.strip()
        if stripped.lower().startswith("comb"):
            header = stripped
            rows = []
            j = i + 1
            while j < len(raw):
                nxt = raw[j]
                nxt_stripped = nxt.strip()
                # Header for the next block ends this one
                if nxt_stripped.lower().startswith("comb"):
                    break
                # A line with no tabs and nothing else is a separator
                if "\t" not in nxt and not nxt_stripped:
                    j += 1
                    continue
                row = _parse_row(nxt)
                if row.size < N_T:
                    row = np.concatenate([row, np.full(N_T - row.size, np.nan)])
                elif row.size > N_T:
                    row = row[:N_T]
                rows.append(row)
                j += 1
                if len(rows) >= N_E:
                    break
            windows[header] = np.stack(rows, axis=0)
            i = j
        else:
            i += 1
    return windows


def build_npz(out_path=None):
    out_path = Path(out_path or HERE / "edc.npz")
    T = load_T()
    E = E_J0 + E_STEP * np.arange(N_E, dtype=np.float64)
    windows = load_intensity_blocks()
    names = list(windows.keys())
    I = np.stack([windows[n].T for n in names], axis=0)  # (n_windows, n_T, n_E)

    nan_frac = float(np.isnan(I).mean())
    print(f"  {I.shape} intensity array; NaN fraction = {nan_frac*100:.2f}%")

    np.savez(
        out_path,
        T=T, E=E, I=I,
        window_names=np.array(names, dtype=object),
    )
    print(f"Saved -> {out_path}")
    return out_path


if __name__ == "__main__":
    build_npz()
