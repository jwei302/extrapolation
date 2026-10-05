import importlib
from pathlib import Path

import numpy as np

from utils import region_densities, slide_interp

_HERE = Path(__file__).parent
DATASETS = tuple(sorted(
    d.name for d in _HERE.iterdir()
    if d.is_dir() and (d / f"{d.name}.py").exists()))

ORDER = ("heisenberg", "flory_huggins", "polaron", "rayleigh_benard", "arpes")
ORDERED = tuple(d for d in ORDER if d in DATASETS) + \
          tuple(d for d in DATASETS if d not in ORDER)
PAIR = ("heisenberg", "arpes")      # the two targets every deeper study uses


def get_dataset(name):
    module = importlib.import_module(f"data.{name}.{name}")
    return getattr(module, "".join(w.capitalize() for w in name.split("_")))()


def display(name):
    return get_dataset(name).DISPLAY


class Dataset:
    """A target f(t, m) on a box, with P = T_INTERP and Q = T_EXTRAP in t; `f` maps two 1-D float64 arrays to one."""
    M_SCALE = 1.0           # plotted units of m per model unit
    INVERT_Z = False        # draw the surface upside down (Rayleigh-Benard's hot plate sits at the bottom)

    def __init__(self):
        self.name = type(self).__module__.rsplit(".", 1)[-1]
        self.RHO_P, self.RHO_Q = region_densities(self.T_INTERP, self.T_EXTRAP)

    # --- the distance sweep keeps P's width and Q's rectangle unless a subclass says otherwise
    @property
    def SWEEP_WIDTH(self):
        return self.T_INTERP[1] - self.T_INTERP[0]

    @property
    def SWEEP_EXTRAP(self):
        return self.T_EXTRAP

    @property
    def T_FULL(self):
        return (min(self.T_INTERP[0], self.T_EXTRAP[0]), max(self.T_INTERP[1], self.T_EXTRAP[1]))

    @property
    def M_PLOT(self):
        return self.M_RANGE

    def truth(self, X):
        return self.f(X[:, 0], X[:, 1])

    def order_parameter(self, y, m):
        return abs(float(m[int(np.argmin(y))]))

    def order_parameter_curve(self, predict, t):
        m = np.linspace(*self.M_RANGE, 401)
        return np.array([self.order_parameter(predict(np.column_stack([np.full_like(m, t0), m])), m) for t0 in t])

    def critical_point(self, predict):
        t = np.linspace(*self.T_FULL, 401)
        return self.transition(t, self.order_parameter_curve(predict, t))

    def transition(self, t, op):
        """Where the order parameter first rises 12% of its range above its flat side."""
        w = 9
        pad = np.r_[np.full(w // 2, op[0]), op, np.full(w // 2, op[-1])]
        op = np.array([np.median(pad[i:i + w]) for i in range(len(op))])
        base = np.percentile(op, 20)
        level = base + 0.12 * (op.max() - base)
        above = op > level
        i = int(np.argmax(~above) if above[0] else np.argmax(above))
        if i == 0:
            return float("nan")
        y0, y1 = op[i - 1], op[i]
        return float(t[i - 1] if y1 == y0 else t[i - 1] + (level - y0) * (t[i] - t[i - 1]) / (y1 - y0))

    def set_distance(self, d):
        below = self.T_INTERP[1] <= self.TC
        self.T_INTERP = slide_interp(self.TC, d, self.SWEEP_WIDTH, below)
        self.T_EXTRAP = self.SWEEP_EXTRAP
        self.RHO_P, self.RHO_Q = region_densities(self.T_INTERP, self.T_EXTRAP)

    def sample_T(self, rng, N, t_range):
        return rng.uniform(*t_range, N)

    def draw(self, t_range, N, rng):
        X = np.column_stack([self.sample_T(rng, N, t_range), rng.uniform(*self.M_RANGE, N)])
        return X, self.f(X[:, 0], X[:, 1])

    def sample_interp_data(self, N, seed):
        return self.draw(self.T_INTERP, N, np.random.default_rng(seed))

    def generate_extrap_data(self, N=2000, seed=99):
        return self.draw(self.T_EXTRAP, N, np.random.default_rng(seed))

    def eval_grid(self, n_T=100, n_m=100):
        TT, MM = np.meshgrid(np.linspace(*self.T_FULL, n_T), np.linspace(*self.M_RANGE, n_m))
        X = np.column_stack([TT.ravel(), MM.ravel()])
        return TT, MM, self.f(TT.ravel(), MM.ravel()).reshape(TT.shape), X


def load_npz(path, build=None):
    if build and not path.exists():
        build()
    return np.load(path, allow_pickle=True)
