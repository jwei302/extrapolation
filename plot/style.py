import matplotlib as mpl
import numpy as np

from models import METHODS

METHOD_LABELS = METHODS
METHOD_COLORS = {"poly": "#1f77b4", "rff": "#d62728", "gp": "#9467bd", "mlp": "#ff7f0e",
                 "ff_mlp": "#17becf", "siren": "#bcbd22", "pinn": "#e377c2", "graybox": "#8c564b"}
DATASET_COLORS = {"heisenberg": "#2c7fb8", "arpes": "#d95f02", "polaron": "#1b9e77",
                  "flory_huggins": "#7570b3", "rayleigh_benard": "#c2185b"}
PAIR_COLORS = {"heisenberg": "#1f77b4", "arpes": "#d62728"}
BOUND_COLOR = "#2ca02c"

PANEL_W, PANEL_H, PANEL_H_COMPACT = 4.2, 3.5, 2.7


def set_neurips_style():
    mpl.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "font.size": 13, "axes.labelsize": 13, "axes.titlesize": 14, "legend.fontsize": 11,
        "xtick.labelsize": 11, "ytick.labelsize": 11,
        "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.05,
        "axes.linewidth": 1.0, "lines.linewidth": 1.3, "text.usetex": False, "mathtext.fontset": "cm",
    })


def panel_figsize(ncol, nrow=1, height=PANEL_H):
    return (PANEL_W * ncol, height * nrow)


def annotate_tc(ax, tc, lo, hi, fontsize=None):
    x = (tc - lo) / (hi - lo)
    ax.text(np.clip(x, 0.02, 0.98), 0.985, r"$T_c$", transform=ax.transAxes,
            ha="center", va="top", fontsize=fontsize)


def annotate_regions(ax, interp, extrap, lo, hi, fontsize=None):
    for rng, text, colour in ((interp, "train $P$", "0.35"), (extrap, "extrap $Q$", "#d62728")):
        ax.text((np.mean(rng) - lo) / (hi - lo), 0.03, text, transform=ax.transAxes,
                ha="center", va="bottom", fontsize=fontsize, color=colour)
