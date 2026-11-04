import argparse
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import ScalarFormatter, NullFormatter, FixedLocator, NullLocator, FuncFormatter
from scipy import stats

from plot import panels
from plot.panels import REGION_COLORS, REGION_ALPHA, TC_STYLE
from plot.style import (set_neurips_style, panel_figsize, PANEL_H_COMPACT, annotate_tc, annotate_regions,
                        METHOD_COLORS, METHOD_LABELS, PAIR_COLORS, BOUND_COLOR)
from data import display, get_dataset, ORDERED, PAIR
from models import NEURAL, load
from eval.labeled_budget import N_LAB
from eval.gp_vs_rff import M_LIST
from utils import SIZES

OUT = Path("figs")
DSETS = list(ORDERED)
C_EMP = METHOD_COLORS["poly"]


def _save(fig, name, dpi=300, **kw):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=dpi, **kw)
    plt.close(fig)


def _geo(vals):
    lg = np.log(np.asarray(vals, float))
    return np.exp(lg.mean()), np.exp(lg.mean() - lg.std()), np.exp(lg.mean() + lg.std())


def _band(ax, x, per_x, color, label, marker):
    y, lo, hi = np.array([_geo(v) for v in per_x]).T
    ax.plot(x, y, marker=marker, ms=4, lw=1.4, color=color, label=label, zorder=3)
    ax.fill_between(x, lo, hi, color=color, alpha=0.12, lw=0, zorder=1)
    return y


def _loglog(ax):
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, alpha=0.3, which="major")


def _centred_decades(ax, lo, hi, pad=0.18, pad_frac=0.06):
    l0, l1 = np.log10(lo), np.log10(hi)
    pad = max(pad, pad_frac * (l1 - l0))
    span = max(2.0, (l1 - l0) + 2 * pad)
    mid = 0.5 * (l0 + l1)
    ax.set_ylim(10.0 ** (mid - span / 2), 10.0 ** (mid + span / 2))
    ticks = [10.0 ** k for k in range(int(np.ceil(mid - span / 2)), int(np.floor(mid + span / 2)) + 1)]
    if len(ticks) >= 2:
        ax.set_yticks(ticks)


def _log_xticks(ax, lo, hi):
    cand = sorted({m * 10.0 ** e for e in range(int(np.floor(np.log10(lo))) - 1, int(np.ceil(np.log10(hi))) + 2)
                   for m in (1, 1.5, 2, 3, 4, 5, 7) if lo <= m * 10.0 ** e <= hi})
    chosen = [cand[0], cand[-1]] if len(cand) >= 2 else [float(f"{lo:.2g}"), float(f"{hi:.2g}")]
    ax.xaxis.set_major_locator(FixedLocator(chosen))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels([f"{v:.3g}" for v in chosen])


def _shared_ylabel(fig, col0_axes, text, fontsize=20, pad=0.02):
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    boxes = [ax.yaxis.label.get_window_extent(renderer=rend).transformed(inv) for ax in col0_axes]
    x = min(b.x0 for b in boxes) - 1.25 * max(b.width for b in boxes)
    t = fig.text(x, 0.5, text, rotation=90, ha="center", va="center", fontsize=fontsize)
    for fs in range(int(fontsize), 7, -1):
        t.set_fontsize(fs)
        if t.get_window_extent(renderer=rend).transformed(inv).height <= 1 - 2 * pad:
            break


def _bounds_grid(xlabel, legend_gap):
    set_neurips_style()
    fig, axes = plt.subplots(2, len(DSETS), figsize=(3.3 * len(DSETS), 6.0), layout="constrained", squeeze=False)
    for r, method in enumerate(("Poly", "RFF")):
        for c, dataset in enumerate(DSETS):
            if r == 0:
                axes[r][c].set_title(display(dataset), fontsize=20, pad=6)
            if c == 0:
                axes[r][c].set_ylabel(method, fontsize=20)

    def finish(handles):
        _shared_ylabel(fig, [axes[0][0], axes[1][0]], "Transfer Coefficient (log)")
        fig.text(0.5, -0.010, xlabel, fontsize=20, ha="center", va="top")
        k = len(handles) // 2
        fig.legend(handles=handles[:k], loc="upper right", ncol=k, frameon=False, fontsize=20,
                   bbox_to_anchor=(0.5 - legend_gap, -0.004))
        fig.legend(handles=handles[k:], loc="upper left", ncol=len(handles) - k, frameon=False, fontsize=20,
                   bbox_to_anchor=(0.5 + legend_gap, -0.004))
    return fig, axes, finish


def fig_bounds_vs_n():
    fig, axes, finish = _bounds_grid(r"Training set size $n$ (log)", 0.115)
    series = [("transfer_coefficient", r"$\Gamma_{\mathrm{emp}}$", dict(color=C_EMP, marker="o", ms=4, lw=1.5)),
              ("gevp_bound", r"$\Gamma_{\mathrm{GEVP}}$", dict(color=BOUND_COLOR, marker="s", ms=4, lw=1.5)),
              ("volume_bound", r"$\overline{\Gamma}_{\mathrm{Volume}}$", dict(color="#e377c2", marker="^", ms=3.5, lw=1.2, alpha=.85)),
              ("remez_bound", r"$\overline{\Gamma}_{\mathrm{Remez}}$", dict(color="#8c564b", marker="D", ms=3.5, lw=1.2, alpha=.85))]
    for r, method in enumerate(("poly", "rff")):
        for c, dataset in enumerate(DSETS):
            ax, j = axes[r][c], json.load(open(f"results/bounds_vs_n_{dataset}_{method}.json"))
            n, lo, hi = np.array(j["n"], float), np.inf, 0.0
            for key, label, style in series:
                v = np.array([_geo(seeds)[0] for seeds in j.get(key, [])])
                if len(v) and np.all(np.isfinite(v)):        # Remez is infinite where the fit interpolates exactly
                    ax.plot(n, v, "-", label=label, **style)
                    lo, hi = min(lo, v.min()), max(hi, v.max())
            _centred_decades(ax, lo, hi)
            _loglog(ax)                  # after the limits, so the log locator thins the decade labels
            ax.set_xticks([n[0], 1000, n[-1]])
    finish(axes[0][0].get_legend_handles_labels()[0])
    _save(fig, "fig_bounds_vs_n")


def fig_distance():
    fig, axes, finish = _bounds_grid(r"Distance $D$ (log)", 0.065)
    for r, method in enumerate(("poly", "rff")):
        for c, dataset in enumerate(DSETS):
            ax = axes[r][c]
            rows = sorted(json.load(open(f"results/distance_{dataset}_{method}.json"))["rows"], key=lambda z: z["d"])
            d = np.array([z["d"] for z in rows])
            for i, (key, color, marker) in enumerate((("transfer", C_EMP, "o"), ("gevp", BOUND_COLOR, "s"))):
                v = np.array([z[key] for z in rows])
                ax.plot(d, v, marker, ms=4.5, color=color)
                fit = stats.linregress(np.log(d), np.log(v))
                xs = np.linspace(d.min(), d.max(), 100)
                ax.plot(xs, np.exp(fit.intercept) * xs ** fit.slope, "-", lw=1.2, color=color, alpha=.85)
                ax.text(0.05, 0.95 - 0.17 * i, rf"$\beta={fit.slope:.2f}$", transform=ax.transAxes, fontsize=14,
                        color=color, va="top", bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                                                         edgecolor=color, alpha=0.9, linewidth=1.1))
            _centred_decades(ax, min(min(z["transfer"], z["gevp"]) for z in rows),
                             max(max(z["transfer"], z["gevp"]) for z in rows))
            _loglog(ax)
            _log_xticks(ax, float(d.min()), float(d.max()))
    finish([Line2D([], [], color=C_EMP, marker="o", ms=7, ls="-", lw=1.6, label=r"$\Gamma_{\mathrm{emp}}$"),
            Line2D([], [], color=BOUND_COLOR, marker="s", ms=7, ls="-", lw=1.6, label=r"$\Gamma_{\mathrm{GEVP}}$")])
    _save(fig, "fig_distance_powerlaw")


def fig_landscape():
    set_neurips_style()
    titles = ["Ground truth"] + [METHOD_LABELS[m] for m in ("poly", "rff", "gp", "mlp")]
    PANEL_H, XLAB_H, TITLE_H, GAP_H, LEGEND_H = 2.59, 0.47, 0.33, 0.12, 0.50
    gap = [GAP_H] * (len(DSETS) - 1) + [LEGEND_H]
    row_h = [PANEL_H + XLAB_H + gap[r] + (TITLE_H if r == 0 else 0.0) for r in range(len(DSETS))]
    fig = plt.figure(figsize=(15.95, sum(row_h)))          # rows placed by hand: no layout engine solves 25 mplot3d panels
    rows = fig.subfigures(len(DSETS), 1, hspace=0.0, height_ratios=row_h)
    for r, (row, dataset) in enumerate(zip(rows, DSETS)):
        outer = row.add_gridspec(1, 2, width_ratios=[0.030, 1], wspace=0.008, left=0.0, right=0.993,
                                 bottom=(XLAB_H + gap[r]) / row_h[r], top=1.0 - (TITLE_H / row_h[r] if r == 0 else 0.001))
        ax_lab = row.add_subplot(outer[0, 0])
        ax_lab.set_axis_off()
        ax_lab.text(1.0, 0.5, display(dataset), rotation=90, fontsize=22, ha="right", va="center", transform=ax_lab.transAxes)
        split = outer[0, 1].subgridspec(1, 2, width_ratios=[1.06, 4.0], wspace=0.115)   # column 1 keeps its axis text
        rest = split[0, 1].subgridspec(1, 4, wspace=0.11)
        panels.landscape(row, [split[0, 0]] + [rest[0, k] for k in range(4)], dataset,
                                titles if r == 0 else [""] * 5)
    fig.legend(handles=[Line2D([], [], lw=2.0, label="critical temperature $T_c$", **TC_STYLE),
                        Patch(facecolor=REGION_COLORS["train"], alpha=REGION_ALPHA, label="training region $P$"),
                        Patch(facecolor=REGION_COLORS["extrap"], alpha=REGION_ALPHA, label="extrapolation region $Q$")],
               ncol=3, loc="center", bbox_to_anchor=(0.5, 0.52 * LEGEND_H / sum(row_h)), frameon=False,
               fontsize=19, handlelength=2.2, columnspacing=3.2)
    with plt.rc_context({"savefig.bbox": "standard"}):          # mplot3d leaves axis labels out of its tight bbox
        _save(fig, "fig_landscape_all", dpi=170)


def fig_order_parameter():
    set_neurips_style()
    fig = plt.figure(figsize=(15.5, 8.6), layout="constrained")
    gs = fig.add_gridspec(2, 6)
    for slot, dataset in zip([gs[0, 0:2], gs[0, 2:4], gs[0, 4:6], gs[1, 1:3], gs[1, 3:5]], DSETS):
        ax = fig.add_subplot(slot)
        panels.order_parameter(ax, dataset)
        ax.set_title(display(dataset), fontsize=20)
        ax.xaxis.label.set_fontsize(19)
        ax.yaxis.label.set_fontsize(19)
        ax.tick_params(which="both", labelsize=16)
    handles = [Line2D([], [], color="k", lw=1.8, label="Ground truth")]
    handles += [Line2D([], [], color=METHOD_COLORS[m], lw=1.4, label=METHOD_LABELS[m]) for m in ("poly", "rff", "gp", "mlp")]
    handles += [Line2D([], [], color="k", ls=":", lw=1.2, label=r"critical point $T_c$"),
                Patch(facecolor="#e6eefc", label="train $P$"), Patch(facecolor="0.93", label="extrap $Q$")]
    ax_leg = fig.add_subplot(gs[1, 5:6])
    ax_leg.set_axis_off()
    ax_leg.legend(handles=handles, loc="center left", frameon=False, handlelength=1.8, borderaxespad=0.0, fontsize=17)
    _save(fig, "fig_order_parameter_all", dpi=180)


def fig_slices():
    set_neurips_style()
    TICK, LBL, TITLE = 14, 18, 19
    fig = plt.figure(figsize=(15.0, 3.5 * len(DSETS)), layout="constrained")
    fig.get_layout_engine().set(w_pad=0.01, h_pad=0.01, wspace=0.0, hspace=0.0)
    for row, dataset in zip(fig.subfigures(len(DSETS), 1, hspace=0.0), DSETS):
        outer = row.add_gridspec(1, 2, width_ratios=[0.030, 1], wspace=0.008)
        ax_lab = row.add_subplot(outer[0, 0])
        ax_lab.set_axis_off()
        ax_lab.text(1.0, 0.5, display(dataset), rotation=90, fontsize=22, ha="right", va="center", transform=ax_lab.transAxes)
        inner = outer[0, 1].subgridspec(1, 4, wspace=0.06)
        handles, labels = panels.slices([row.add_subplot(inner[0, i]) for i in range(4)], dataset, TICK, LBL, TITLE)
    fig.legend(handles, labels, loc="upper center", ncol=len(labels), frameon=False, fontsize=22, bbox_to_anchor=(0.5, -0.005))
    _save(fig, "fig_slices_all", dpi=200)


def fig_gp_vs_rff():
    set_neurips_style()
    fig = plt.figure(figsize=panel_figsize(2, 2, height=PANEL_H_COMPACT), layout="constrained")
    sfs = fig.subfigures(2, 1, hspace=0.04)
    axes = list(sfs[0].subplots(1, 2)) + list(sfs[1].subplots(1, 2))
    for col, dataset in enumerate(PAIR):
        j = json.load(open(f"results/gp_vs_rff_{dataset}.json"))
        ax = axes[col]
        y = _band(ax, M_LIST, [j["m"][str(m)] for m in M_LIST], METHOD_COLORS["rff"], "RFF", "o")
        g, glo, ghi = _geo(j["gp"][str(SIZES[-1])])
        ax.axhline(g, color=METHOD_COLORS["gp"], ls="--", lw=1.6, zorder=4, label="GP")
        ax.axhspan(glo, ghi, color=METHOD_COLORS["gp"], alpha=0.10, lw=0, zorder=0)
        _centred_decades(ax, min(y.min(), g), max(y.max(), g))
        _loglog(ax)
        ax.set_title(f"({chr(97 + col)}) {display(dataset)}", pad=5)
        if col == 0:
            ax.set_ylabel("Transfer Coefficient")
        ax = axes[col + 2]
        y_r = _band(ax, SIZES, [j["rff"][str(n)] for n in SIZES], METHOD_COLORS["rff"], "RFF", "o")
        y_g = _band(ax, SIZES, [j["gp"][str(n)] for n in SIZES], METHOD_COLORS["gp"], "GP", "s")
        _centred_decades(ax, min(y_r.min(), y_g.min()), max(y_r.max(), y_g.max()))
        _loglog(ax)
        ax.set_title(f"({chr(99 + col)}) {display(dataset)}", pad=5)
        if col == 0:
            ax.set_ylabel("Transfer Coefficient")
        ax.set_xticks([SIZES[0], 1000, SIZES[-1]])
        ax.xaxis.set_major_formatter(ScalarFormatter())
    sfs[0].supxlabel(r"RFF features $m$")
    sfs[1].supxlabel(r"Training set size $n$")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="outside lower center", ncol=len(l), frameon=False, fontsize=13, handlelength=1.6, columnspacing=1.3)
    _save(fig, "fig_gp_vs_rff")


def _calibration_panel(ax, blob, ds):
    curves = blob["curves"]
    T = np.asarray(curves[0]["T"])
    err = np.vstack([c["err2"] for c in curves])
    var = np.vstack([c["var"] for c in curves])
    ax.axvspan(*blob["T_interp"], color="0.85", alpha=0.7, linewidth=0, zorder=0)
    ax.axvspan(*ds.T_EXTRAP, color="#d62728", alpha=0.07, linewidth=0, zorder=0)
    ax.fill_between(T, err.min(axis=0), err.max(axis=0), color="#d62728", alpha=0.25, linewidth=0)
    ax.plot(T, err.mean(axis=0), color="#d62728", linewidth=1.5, label=r"realized $(f^*-\mu)^2$")
    ax.fill_between(T, var.min(axis=0), var.max(axis=0), color="#1f77b4", alpha=0.25, linewidth=0)
    ax.plot(T, var.mean(axis=0), color="#1f77b4", linewidth=1.5, label=r"GP posterior $\sigma^2$")
    ax.axvline(blob["Tc"], color="k", linestyle=":", linewidth=1.2)
    ax.set_yscale("log")
    ax.set_xlim(T.min(), T.max())
    annotate_tc(ax, blob["Tc"], T.min(), T.max(), 11)
    annotate_regions(ax, blob["T_interp"], ds.T_EXTRAP, T.min(), T.max(), 9)


def fig_gp_variance():
    set_neurips_style()
    res = json.load(open("results/gp_variance.json"))
    fig, axes = plt.subplots(1, len(PAIR), figsize=panel_figsize(len(PAIR), height=PANEL_H_COMPACT),
                             layout="constrained", squeeze=False)
    for j, dataset in enumerate(PAIR):
        _calibration_panel(axes[0][j], res[dataset], get_dataset(dataset))
        axes[0][j].set_title(f"({chr(97 + j)}) {display(dataset)}")
        axes[0][j].set_xlabel(r"Temperature $T$")
    fig.supylabel("Squared error / Variance", fontsize=plt.rcParams["axes.labelsize"])
    h, l = axes[0][0].get_legend_handles_labels()
    fig.legend(h, l, loc="outside lower center", ncol=len(l), frameon=False, fontsize=13, handlelength=1.4, columnspacing=1.0)
    _save(fig, "fig_gp_variance")


def fig_convergence():
    set_neurips_style()
    fig, axes = plt.subplots(1, 2, figsize=panel_figsize(2), layout="constrained")
    YLIM = (1e-1, 1e3)
    for dataset in PAIR:
        for method, marker, ls in (("poly", "o", "-"), ("rff", "s", "--")):
            blob = json.load(open(f"results/gevp_convergence/{dataset}_{method}.json"))
            color, label = PAIR_COLORS[dataset], rf"{display(dataset)} $\times$ {METHOD_LABELS[method]}"
            ns = sorted({c["n_mc"] for c in blob["convergence"]})
            r = [[100.0 * c["rel"] for c in blob["convergence"] if c["n_mc"] == n] for n in ns]
            axes[0].fill_between(ns, [np.percentile(v, 5) for v in r], [np.percentile(v, 95) for v in r],
                                 color=color, alpha=.10, lw=0)
            axes[0].plot(ns, [np.median(v) for v in r], ls, color=color, marker=marker, ms=4.5, lw=1.5, label=label)
            rows = sorted(blob["distance"], key=lambda z: z["d"])
            d = [z["d"] for z in rows]
            axes[1].fill_between(d, [100 * z["rel_p05"] for z in rows], [100 * z["rel_p95"] for z in rows],
                                 color=color, alpha=.10, lw=0)
            axes[1].plot(d, [100 * z["rel_mean"] for z in rows], ls, color=color, marker=marker, ms=4.5, lw=1.5, label=label)
    axes[0].axvline(10_000, color="0.15", ls=":", lw=1.5)
    axes[0].set(xscale="log", yscale="log", ylim=YLIM, xlabel=r"Unlabeled draws $N_{\mathrm{MC}}$",
                ylabel="Relative error", title="(a) Sufficiency")
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}%"))
    axes[1].set(xscale="log", yscale="log", ylim=YLIM, xlabel=r"Distance $D$ to $T_c$", title="(b) Distance Independence")
    axes[1].yaxis.set_major_formatter(NullFormatter())
    axes[1].yaxis.set_minor_formatter(NullFormatter())
    for ax in axes:
        ax.grid(alpha=.3)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="outside lower center", ncol=2, frameon=False, fontsize=13, handlelength=1.5, columnspacing=1.4)
    _save(fig, "fig_gevp_convergence")


def fig_landau():
    set_neurips_style()
    ds, j = get_dataset("heisenberg"), json.load(open("results/landau_coeff.json"))
    T = np.array(j["T"])
    fig, axes = plt.subplots(1, 2, figsize=panel_figsize(2, height=PANEL_H_COMPACT), layout="constrained")
    for name, label, color in (("truth", "Truth", "k"), ("poly", METHOD_LABELS["poly"], METHOD_COLORS["poly"]),
                               ("graybox", METHOD_LABELS["graybox"], "#17becf")):
        lw = 2.0 if name == "truth" else 1.5
        axes[0].plot(T, j[name]["a"], "-", color=color, linewidth=lw, label=label, zorder=3)
        axes[1].plot(T, j[name]["order_parameter"], "-", color=color, linewidth=lw, label=label, zorder=3)
    axes[0].axhline(0.0, color="0.35", linewidth=1.0, zorder=1)
    for ax in axes:
        ax.axvspan(*ds.T_INTERP, color="0.85", alpha=0.7, linewidth=0, zorder=0)
        ax.axvspan(*ds.T_EXTRAP, color="#d62728", alpha=0.07, linewidth=0, zorder=0)
        ax.axvline(ds.TC, color="k", linestyle=":", linewidth=1.2)
        ax.set_xlim(T.min(), T.max())
        annotate_tc(ax, ds.TC, T.min(), T.max())
        annotate_regions(ax, ds.T_INTERP, ds.T_EXTRAP, T.min(), T.max())
        ax.grid(alpha=0.3)
    axes[0].set(ylim=(-0.34, 0.30), ylabel=r"$a(T)$")
    axes[0].set_title(r"(a) Landau coefficient $a(T)$", pad=10)
    axes[1].set(ylim=(-0.11, 0.78), ylabel=r"$|m^*(T)|$")
    axes[1].set_title(r"(b) Order parameter $|m^*(T)|$", pad=10)
    axes[1].legend(frameon=False, loc="center right")
    fig.supxlabel(r"Temperature $T$")
    _save(fig, "fig_landau_coeff")


def fig_budget():
    set_neurips_style()
    rows = json.load(open("results/labeled_budget.json"))
    fig, axes = plt.subplots(2, 2, figsize=panel_figsize(2, 2, height=PANEL_H_COMPACT), layout="constrained")
    for ax, (dataset, method) in zip(axes.flat, [(d, m) for d in PAIR for m in ("poly", "rff")]):
        sel = [r for r in rows if r["dataset"] == dataset and r["method"] == method]
        pct = np.array([np.percentile(sum((r["estimates"] for r in sel if r["n_lab"] == n), []), [5, 50, 95]) for n in N_LAB])
        ax.fill_between(N_LAB, pct[:, 0], pct[:, 2], color="#1f77b4", alpha=0.25, linewidth=0)
        ax.plot(N_LAB, pct[:, 1], "o-", color="#1f77b4", markersize=3, linewidth=1.3, label="median estimate")
        ax.axhline(np.mean([r["mse_Q"] for r in sel]), color="#d62728", linewidth=1.4, label=r"true MSE$_Q$")
        ax.axhline(np.mean([r["bound"] for r in sel]), color=BOUND_COLOR, linestyle="--", linewidth=1.4,
                   label=r"$\Gamma_{\mathrm{GEVP}} \cdot \mathrm{MSE}_P$")
        ax.set(xscale="log", yscale="log")
        ax.set_title(rf"{display(dataset)} $\times$ {METHOD_LABELS[method]}", pad=6)
    for r in range(2):
        axes[r][0].set_ylabel(r"Estimate of MSE$_Q$")
        axes[1][r].set_xlabel(r"Number of labeled points $n_{\mathrm{lab}}$")
    h, l = axes[0][0].get_legend_handles_labels()
    fig.legend(h, l, loc="outside lower center", ncol=len(l), frameon=False, fontsize=13, handlelength=1.6, columnspacing=1.3)
    _save(fig, "fig_labeled_budget")


def fig_neural():
    set_neurips_style()
    plt.rcParams.update({"xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 13})
    fig = plt.figure(figsize=(13.0, 11.0))
    top, bottom = fig.subfigures(2, 1, height_ratios=[10.5, 0.5], hspace=0.0)
    left, right = top.subfigures(1, 2, wspace=0.04)
    cells = lambda ds: [("(a) Ground truth", ds.truth)] + [(f"({chr(98 + i)}) {METHOD_LABELS[m]}", load(ds.name, m).predict)
                                                           for i, m in enumerate(NEURAL)]
    ds = get_dataset("heisenberg")
    TT, MM, Z_true, X = ds.eval_grid()
    gs = left.add_gridspec(3, 2, wspace=0.30, hspace=0.42)
    for i, ((title, predict), color) in enumerate(zip(cells(ds), ["#2ca02c"] + [METHOD_COLORS[m] for m in NEURAL])):
        ax = left.add_subplot(gs[i // 2, i % 2], projection="3d")
        panels.surface_panel(ax, TT, MM, predict(X).reshape(TT.shape), panels.cmap(color), Z_true.min(), Z_true.max(), ds, title)
    left.supxlabel("(i) Heisenberg", fontsize=16)
    ds = get_dataset("arpes")
    s = panels.edc_setup(ds)
    gs = right.add_gridspec(3, 2, wspace=0.30, hspace=0.45)
    ax0 = None
    for i, (title, predict) in enumerate(cells(ds)):
        ax = right.add_subplot(gs[i // 2, i % 2], sharey=ax0)
        ax0 = ax0 or ax
        panels.edc_panel(ax, predict, ds, s, title)
        if i % 2 == 0:
            ax.set_ylabel(ds.F_LABEL)
        else:
            plt.setp(ax.get_yticklabels(), visible=False)
    right.supxlabel("(ii) ARPES", fontsize=16)
    bottom.legend(handles=[Line2D([], [], lw=2.0, label="critical temperature $T_c$", **TC_STYLE),
                           Patch(facecolor=REGION_COLORS["train"], alpha=REGION_ALPHA, label="training region $P$"),
                           Patch(facecolor=REGION_COLORS["extrap"], alpha=REGION_ALPHA, label="extrapolation region $Q$")],
                  ncol=3, loc="center", frameon=False, fontsize=16, handlelength=2.2, columnspacing=3.2)
    _save(fig, "fig_neural_architectures", bbox_inches="tight")


FIGURES = {"landscape": fig_landscape, "order_param": fig_order_parameter, "bounds_vs_n": fig_bounds_vs_n,
           "distance": fig_distance, "convergence": fig_convergence, "gp_vs_rff": fig_gp_vs_rff,
           "gp_variance": fig_gp_variance, "budget": fig_budget, "landau": fig_landau, "neural": fig_neural,
           "slices": fig_slices}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fig", required=True, choices=list(FIGURES))
    FIGURES[ap.parse_args().fig]()
