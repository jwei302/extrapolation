from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from data import Dataset, load_npz

RA_C = 776.2
_NPZ = Path(__file__).parent / "profiles.npz"
_INTERP = []


def _interp():
    if not _INTERP:
        d = load_npz(_NPZ)
        _INTERP.append(RegularGridInterpolator((np.log10(d["Ra"]), d["z"]), d["Tbar"],
                                               bounds_error=False, fill_value=None, method="cubic"))
    return _INTERP[0]


class RayleighBenard(Dataset):
    DISPLAY = "Rayleigh-Benard"
    TC = float(np.log10(RA_C))
    T_INTERP = (float(np.log10(1500.0)), float(np.log10(7500.0)))
    T_EXTRAP = (float(np.log10(300.0)), float(np.log10(1500.0)))
    M_RANGE = (0.0, 1.0)
    TUNING_SYMBOL, TUNING_NAME, TUNING_CRIT, TUNING_UNIT = r"\log_{10}\mathrm{Ra}", "Rayleigh number", r"\mathrm{Ra}_c", ""
    M_LABEL, F_LABEL, ORDER_LABEL = "$z$", r"$\bar{T}(z)$", r"$\Phi$"
    M_PLOT = (0.1, 0.9)                 
    INVERT_Z = True

    def f(self, T, m):
        return _interp()(np.column_stack([T, m]))

    def order_parameter(self, y, z):
        """RMS departure of the profile from pure conduction, 1 - z."""
        return float(np.sqrt(np.mean((y - (1.0 - z)) ** 2)))

    def transition(self, t, op):
        """Zero crossing of the branch leaving the conduction plateau."""
        ra, span = 10.0 ** t, op.max() - op.min()
        i0 = int(np.where(op <= op.min() + 0.02 * span)[0][-1])
        sel = np.where((np.arange(len(op)) > i0) & (op > op.min() + 0.02 * span)
                       & (op <= op.min() + 0.35 * span))[0]
        if len(sel) >= 3:
            a, b = np.polyfit(ra[sel], op[sel], 1)
            if a > 0 and ra[0] * 0.5 <= -b / a <= ra[-1]:
                return float(np.log10(-b / a))
        return float(t[i0])
