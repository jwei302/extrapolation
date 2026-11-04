import warnings
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import curve_fit

from data import Dataset, load_npz
from data.arpes.convert import build_npz

_NPZ = Path(__file__).parent / "edc.npz"
_DATA = {}
_INTERP = {}


def measurements():
    if not _DATA:
        d = load_npz(_NPZ, build=build_npz)
        I = d["I"]
        for grid in I:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")            
                fill = np.nan_to_num(np.nanmedian(grid, axis=0))
            grid[np.isnan(grid)] = np.take(fill, np.where(np.isnan(grid))[1])
        _DATA.update(T=d["T"], E=d["E"], I=I)
    return _DATA


def _interpolator(window):
    if window not in _INTERP:
        d = measurements()
        _INTERP[window] = RegularGridInterpolator((d["T"], d["E"]), d["I"][window],
                                                  bounds_error=False, fill_value=None, method="linear")
    return _INTERP[window]


class Arpes(Dataset):
    DISPLAY = "ARPES"
    TC = 90.0
    T_INTERP = (95.0, 150.0)
    T_EXTRAP = (65.0, 95.0)
    M_RANGE = (-0.1, 0.0)                  # binding energy E, eV
    SWEEP_WIDTH = 65.0
    TUNING_SYMBOL, TUNING_NAME, TUNING_CRIT, TUNING_UNIT = "T", "Temperature", "T_c", "K"
    M_LABEL, F_LABEL, ORDER_LABEL = "$E$ (meV)", "$I(T,E)$", r"$-E^*(T)$  (meV)"
    M_SCALE = 1000.0
    M_PLOT = (-0.025, 0.0)
    WINDOW = 1                             # momentum-integration window

    def f(self, T, E):
        return _interpolator(self.WINDOW)(np.column_stack([T, E]))

    def sample_T(self, rng, N, t_range):
        """Stratified in T over sqrt(N) equal-width bins, so sparse measured temperatures are all covered."""
        n_strata = min(max(1, int(round(np.sqrt(N)))), N)
        edges = np.linspace(t_range[0], t_range[1], n_strata + 1)
        sizes = np.full(n_strata, N // n_strata, dtype=int)
        sizes[: N - sizes.sum()] += 1
        T = np.concatenate([rng.uniform(edges[i], edges[i + 1], sizes[i]) for i in range(n_strata)])
        rng.shuffle(T)
        return T

    @property
    def T_FULL(self):
        T = measurements()["T"]
        return (float(T.min()), float(T.max()))

    def T_grid(self):
        return measurements()["T"].copy()

    def critical_point(self, predict):
        return float("nan") # used for Table 1

    def peak_energy(self, predict, T0, E_lo=-20.0, E_hi=1.0):
        """Peak position in meV of a predicted EDC at T0: a Gaussian-plus-baseline fit, else the argmax."""
        E = np.linspace(E_lo, E_hi, 400)
        y = predict(np.column_stack([np.full_like(E, T0), E / 1000.0]))
        mu0 = float(E[np.argmax(y)])
        gauss = lambda E, A, mu, sigma, c: A * np.exp(-0.5 * ((E - mu) / sigma) ** 2) + c
        try:
            mu = float(curve_fit(gauss, E, y, p0=[y.max() - y.min(), mu0, 5.0, y.min()], maxfev=5000)[0][1])
        except RuntimeError:
            return mu0
        return mu if E_lo <= mu <= E_hi else mu0
