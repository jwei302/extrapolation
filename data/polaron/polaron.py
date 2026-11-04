from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from data import Dataset, load_npz

_NPZ = Path(__file__).parent / "dispersion.npz"
_INTERP = []


def _interp():
    if not _INTERP:
        d = load_npz(_NPZ)
        _INTERP.append(RegularGridInterpolator((d["lam"], d["K"]), d["E"],
                                               bounds_error=False, fill_value=None, method="cubic"))
    return _INTERP[0]


class Polaron(Dataset):
    DISPLAY = "Polaron"
    TC = 0.6839
    T_INTERP = (0.2, 0.6)               
    T_EXTRAP = (0.6, 1.0)
    M_RANGE = (0.0, 0.6 * float(np.pi))
    SWEEP_WIDTH = 0.2
    SWEEP_EXTRAP = (TC - 0.1, TC + 0.1)
    TUNING_SYMBOL, TUNING_NAME, TUNING_CRIT, TUNING_UNIT = r"\lambda_{\mathrm{SSH}}", "Coupling", r"\lambda_c", ""
    M_LABEL, F_LABEL, ORDER_LABEL = "$K$", r"$E(K;\lambda)$", r"$K^*(\lambda)$"

    def f(self, lam, K):
        return _interp()(np.column_stack([lam, K]))
