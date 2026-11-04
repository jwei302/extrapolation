from data import Dataset


class Heisenberg(Dataset):
    DISPLAY = "Heisenberg"
    TC = 1.5
    T_INTERP = (2.0, 3.0)
    T_EXTRAP = (1.0, 2.0)
    M_RANGE = (-1.25, 1.25)
    TUNING_SYMBOL, TUNING_NAME, TUNING_CRIT, TUNING_UNIT = "T", "Temperature", "T_c", ""
    M_LABEL, F_LABEL, ORDER_LABEL = "$m$", "$f(T,m)$", r"$|m^*(T)|$"

    def f(self, T, m):
        return 0.5 * (1 - self.TC / T) * m**2 + (self.TC / T) ** 3 * m**4 / 12 + 0.01
