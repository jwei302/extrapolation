import numpy as np

from data import Dataset


class FloryHuggins(Dataset):
    DISPLAY = "Flory-Huggins"
    TC = 1.0
    T_INTERP = (1.5, 2.5)
    T_EXTRAP = (0.5, 1.5)
    M_RANGE = (-0.48, 0.48)
    TUNING_SYMBOL, TUNING_NAME, TUNING_CRIT, TUNING_UNIT = "T", "Temperature", "T_c", ""
    M_LABEL, F_LABEL, ORDER_LABEL = "$m$", "$f(T,m)$", r"$|m^*(T)|$"

    def f(self, T, m):
        x = np.clip(m + 0.5, 1e-12, 1.0 - 1e-12)
        return T * (x * np.log(x) + (1 - x) * np.log(1 - x)) + 2 * self.TC * x * (1 - x)
