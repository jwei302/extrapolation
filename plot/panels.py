import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap, LightSource, Normalize, to_rgb
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import proj3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from data import get_dataset
from models import MAIN, load
from plot.style import DATASET_COLORS, METHOD_COLORS, METHOD_LABELS


def load_models(dataset):
    return [(m, load(dataset, m).predict) for m in MAIN]


# --- landscapes (Fig. 1, Fig. 10) ---

VIEW = (25, -60)
LIGHT = LightSource(azdeg=315, altdeg=55)
REGION_COLORS = {"extrap": "#d4d4d4", "train": "#cdddf3"}
REGION_ALPHA = 0.7
TC_STYLE = dict(color="red", linestyle="--", alpha=0.8)
TICK3D, TICK2D, LBL, TITLE = 12, 13, 17, 20


def cmap(hex_color):
    rgb = to_rgb(hex_color)
    return LinearSegmentedColormap.from_list(hex_color, [tuple(0.45 + 0.55 * c for c in rgb), rgb], N=256)


def surface_panel(ax, TT, MM, Z, colors, vmin, vmax, ds, title=""):
    ax.plot_surface(TT, MM, Z, cmap=colors, vmin=vmin, vmax=vmax, alpha=0.97, edgecolor="none",
                    rasterized=True, shade=True, lightsource=LIGHT, antialiased=True)
    z_pad = 0.05 * (vmax - vmin) if vmax > vmin else 0.05
    z_floor = (vmax + z_pad) if ds.INVERT_Z else (vmin - z_pad)
    m_lo, m_hi = ds.M_PLOT
    polys = [[(t[0], m_lo, z_floor), (t[1], m_lo, z_floor), (t[1], m_hi, z_floor), (t[0], m_hi, z_floor)]
             for t in (ds.T_EXTRAP, ds.T_INTERP)]
    ax.add_collection3d(Poly3DCollection(polys, facecolors=[REGION_COLORS["extrap"], REGION_COLORS["train"]],
                                         edgecolors="none", alpha=REGION_ALPHA))
    ax.plot([ds.TC, ds.TC], [m_lo, m_hi], [z_floor, z_floor], linewidth=1.0, **TC_STYLE)
    ax.set_xlabel(f"${ds.TUNING_SYMBOL}$")
    ax.set_ylabel(ds.M_LABEL)
    ax.set_zlabel(ds.F_LABEL)
    ax.set_zlim(vmin - z_pad, vmax + z_pad)
    ax.set_title(title)
    ax.tick_params(pad=1)
    if ds.INVERT_Z:
        ax.invert_zaxis()
    ax.view_init(*VIEW)
    # flip the tuning axis if the training region projects to the right of Q
    ymid, zmid, proj = 0.5 * sum(ax.get_ylim()), 0.5 * sum(ax.get_zlim()), ax.get_proj()
    screen_x = lambda t: proj3d.proj_transform(t, ymid, zmid, proj)[0]
    if screen_x(np.mean(ds.T_INTERP)) > screen_x(np.mean(ds.T_EXTRAP)):
        ax.invert_xaxis()


def render_surfaces(row, cells, ds, models, titles):
    TT, MM, Z_true, X = ds.eval_grid()
    keep = (MM[:, 0] >= ds.M_PLOT[0]) & (MM[:, 0] <= ds.M_PLOT[1])
    Zs = [Z[keep] for Z in [Z_true] + [predict(X).reshape(TT.shape) for _, predict in models]]
    vmin, vmax = float(min(Z.min() for Z in Zs)), float(max(Z.max() for Z in Zs))
    colors = cmap(DATASET_COLORS[ds.name])
    for c, (Z, title) in enumerate(zip(Zs, titles)):
        ax = row.add_subplot(cells[c], projection="3d")
        surface_panel(ax, TT[keep], MM[keep], Z, colors, vmin, vmax, ds, title)
        ax.title.set_fontsize(TITLE)
        ax.tick_params(labelsize=TICK3D)
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_locator(MaxNLocator(5))
            axis.labelpad = 4
        ax.zaxis.set_major_locator(MaxNLocator(4))
        ax.zaxis.set_rotate_label(False)
        ax.set_zlabel(ds.F_LABEL, rotation=90, labelpad=5, fontsize=LBL)
        ax.xaxis.label.set_fontsize(LBL)
        ax.yaxis.label.set_fontsize(LBL)
        if c > 0:                                  # one set of axis text per row
            ax.set_xlabel(""); ax.set_ylabel(""); ax.set_zlabel("")
            for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
                axis.set_ticklabels([])
        ax.set_box_aspect(None, zoom=1.18)


def edc_setup(ds):
    T = np.sort(ds.T_grid())
    T = T[(T >= ds.T_EXTRAP[0]) & (T <= ds.T_INTERP[1])]
    E = np.linspace(*ds.M_PLOT, 300)
    y0 = ds.f(np.full_like(E, T[len(T) // 2]), E)
    return dict(T=T, E=E, step=0.25 * float(y0.max() - y0.min()),
                norm_ex=Normalize(T.min(), ds.T_INTERP[0]), norm_in=Normalize(ds.T_INTERP[0], T.max()))


def edc_panel(ax, predict, ds, s, title=""):
    E_meV = s["E"] * ds.M_SCALE
    k_tc = int(np.argmin(np.abs(s["T"] - ds.TC)))
    for k, T0 in enumerate(s["T"]):
        y = predict(np.column_stack([np.full_like(s["E"], T0), s["E"]])) + k * s["step"]
        if k == k_tc:
            ax.plot(E_meV, y, lw=2.4, zorder=12, **TC_STYLE)
        elif T0 < ds.T_INTERP[0]:
            ax.plot(E_meV, y, color=cm.Greys(0.40 + 0.60 * (1 - s["norm_ex"](T0))), lw=0.85, alpha=0.9, zorder=2)
        else:
            ax.plot(E_meV, y, color=cm.Blues(0.40 + 0.60 * s["norm_in"](T0)), lw=0.85, alpha=0.9, zorder=2)
        peak = ds.peak_energy(predict, float(T0))
        if E_meV[0] <= peak <= E_meV[-1]:
            ax.plot(peak, float(np.interp(peak, E_meV, y)), marker="o", mfc="white", mec="black",
                    ms=3.5, mew=0.7, linestyle="none", zorder=15)
    ax.set_xlim(E_meV[0], E_meV[-1])
    ax.set_xlabel(ds.M_LABEL)
    ax.set_title(title)
    ax.grid(alpha=0.3)


def render_edcs(row, cells, ds, models, titles):
    s = edc_setup(ds)
    ax0 = None
    for c, ((_, predict), title) in enumerate(zip([("truth", ds.truth)] + models, titles)):
        ax = row.add_subplot(cells[c], sharey=ax0)
        ax0 = ax0 or ax
        edc_panel(ax, predict, ds, s, title)
        ax.tick_params(labelsize=TICK2D)
        ax.xaxis.label.set_fontsize(LBL)
        ax.yaxis.label.set_fontsize(LBL)
        ax.title.set_fontsize(TITLE)
        if c == 0:                                 
            ax.set_ylabel(ds.F_LABEL)
            ax.yaxis.set_label_position("right")
            ax.yaxis.tick_right()
        else:
            ax.set_xlabel("")
            plt.setp(ax.get_yticklabels(), visible=False)
            plt.setp(ax.get_xticklabels(), visible=False)


# --- order parameter (Fig. 2) ---

def _regions(ax, ds, tc_label):
    ax.axvspan(*ds.T_EXTRAP, color="0.93", zorder=0)
    ax.axvspan(*ds.T_INTERP, color="#e6eefc", zorder=0)
    ax.axvline(ds.TC, color="k", linestyle=":", linewidth=1.0, label=tc_label)


def render_order_parameter(ax, ds, models):
    T = np.linspace(*ds.T_FULL, 300)

    def op(predict):
        curve = ds.order_parameter_curve(predict, T)
        return np.where(curve > 0.02, curve, 0.0)       # the disordered side sits at zero

    _regions(ax, ds, f"${ds.TUNING_CRIT} = {ds.TC}$")
    ax.plot(T, op(ds.truth), "k-", label="Ground truth", linewidth=1.8)
    for m, predict in models:
        ax.plot(T, op(predict), color=METHOD_COLORS[m], label=METHOD_LABELS[m], linewidth=1.0)
    ax.set_xlim(T[0], T[-1])
    if ds.T_INTERP[0] < ds.T_EXTRAP[0]:        # training at low values: flip so P sits on the right like the others
        ax.invert_xaxis()
    ax.set_xlabel(f"{ds.TUNING_NAME} ${ds.TUNING_SYMBOL}$")
    ax.set_ylabel(ds.ORDER_LABEL)
    ax.grid(True, alpha=0.3)


def render_order_parameter_arpes(ax, ds, models):
    T = ds.T_grid()
    T = T[(T >= ds.T_EXTRAP[0]) & (T <= ds.T_INTERP[1])]
    peaks = lambda predict: -np.array([ds.peak_energy(predict, t) for t in T])
    _regions(ax, ds, f"$T_c = {ds.TC:.0f}$ K")
    ax.plot(T, peaks(ds.truth), "o-", color="k", linewidth=1.8, markersize=4, label="Ground truth")
    for m, predict in models:
        ax.plot(T, peaks(predict), "o--", color=METHOD_COLORS[m], linewidth=1.0, markersize=3,
                alpha=0.9, label=METHOD_LABELS[m])
    ax.set_xlim(T[0], T[-1])
    ax.set_xlabel(f"{ds.TUNING_NAME} ${ds.TUNING_SYMBOL}$ ({ds.TUNING_UNIT})")
    ax.set_ylabel(ds.ORDER_LABEL)
    ax.grid(alpha=0.3)


# --- slices (Fig. 11) ---

SLICES = {"heisenberg": [1.2, 1.5, 1.8, 2.5], "flory_huggins": [0.6, 0.9, 1.2, 1.8],
          "polaron": [0.4, 0.642, 0.684, 0.842], "arpes": [80.0, 85.0, 90.0, 100.0]}


def train_first(values, ds):
    in_P = lambda t: ds.T_INTERP[0] <= t <= ds.T_INTERP[1]
    return [t for t in values if in_P(t)] + sorted([t for t in values if not in_P(t)],
                                                    reverse=ds.T_EXTRAP[1] <= ds.T_INTERP[0])


def render_slices(axes, ds, models, tick, lbl, title):
    x = np.linspace(*ds.M_PLOT, 300)
    for c, (ax, t0) in enumerate(zip(axes, train_first(SLICES[ds.name], ds))):
        X = np.column_stack([np.full_like(x, t0), x])
        ax.plot(x * ds.M_SCALE, ds.truth(X), "k-", label="Ground truth", lw=1.5)
        for m, predict in models:
            ax.plot(x * ds.M_SCALE, predict(X), color=METHOD_COLORS[m], label=METHOD_LABELS[m], lw=1.0)
        in_P = ds.T_INTERP[0] <= t0 <= ds.T_INTERP[1]
        ax.set_title(f"${ds.TUNING_SYMBOL} = {t0}$ {ds.TUNING_UNIT}".rstrip(),
                     color="tab:blue" if in_P else "tab:red", fontsize=title)
        ax.set_xlabel(ds.M_LABEL, fontsize=lbl)
        if c == 0:
            ax.set_ylabel(ds.F_LABEL, fontsize=lbl)
        ax.grid(alpha=0.3)
        ax.tick_params(labelsize=tick)
    return axes[0].get_legend_handles_labels()


# --- Rayleigh-Benard ---

Z = np.linspace(0, 1, 200)


def render_slices_rb(axes, ds, models, tick, lbl, title):
    log_ra = lambda lo_hi, frac: lo_hi[0] + frac * (lo_hi[1] - lo_hi[0])
    Q = (max(ds.T_EXTRAP[0], np.log10(600.0)), ds.T_EXTRAP[1])
    cells = [(log_ra(ds.T_INTERP, 0.5), True)] + [(log_ra(Q, f), False) for f in (0.85, 0.45, 0.05)]
    for c, (ax, (lr, in_P)) in enumerate(zip(axes, cells)):
        X = np.column_stack([np.full_like(Z, lr), Z])
        ax.plot(ds.truth(X), Z, "k-", lw=2.2, label="Ground truth")
        for m, predict in models:
            ax.plot(predict(X), Z, color=METHOD_COLORS[m], lw=1.1, label=METHOD_LABELS[m])
        ax.set_title(f"Ra={10 ** lr:.0f}", color="tab:blue" if in_P else "tab:red", fontsize=title)
        ax.set_xlabel(r"$\bar T$", fontsize=lbl)
        if c == 0:
            ax.set_ylabel("$z$", fontsize=lbl)
        ax.set_ylim(0, 1)
        ax.grid(alpha=.3)
        ax.tick_params(labelsize=tick)
    return axes[0].get_legend_handles_labels()


def render_order_parameter_rb(ax, ds, models):
    ra_lo, ra_hi = 10 ** ds.T_EXTRAP[0], 10 ** ds.T_INTERP[1]
    Ra = np.geomspace(ra_lo, ra_hi, 120)
    op = lambda predict: [ds.order_parameter(predict(np.column_stack([np.full_like(Z, np.log10(r)), Z])), Z) for r in Ra]
    ax.plot(Ra, op(ds.truth), "k-", lw=2.4, label="Ground truth")
    for m, predict in models:
        ax.plot(Ra, op(predict), color=METHOD_COLORS[m], lw=1.3, label=METHOD_LABELS[m])
    ax.axvspan(ra_lo, 10 ** ds.T_INTERP[0], color="0.93", label="extrap")
    ax.axvspan(10 ** ds.T_INTERP[0], ra_hi, color="#e6eefc", label="train")
    ax.set_xlim(ra_lo, ra_hi)
    ax.axvline(10 ** ds.TC, color="k", ls=":", lw=1.0, label=f"$Ra_c$={10 ** ds.TC:.0f}")
    ax.axhline(0.0, color="0.5", lw=.6)
    ax.set(xscale="log", xlabel="Ra", ylabel=ds.ORDER_LABEL)
    ax.grid(alpha=.3)


# --- dispatch ---

_LANDSCAPE = {"arpes": render_edcs}
_ORDER_PARAMETER = {"arpes": render_order_parameter_arpes, "rayleigh_benard": render_order_parameter_rb}
_SLICES = {"rayleigh_benard": render_slices_rb}


def landscape(row, cells, dataset, titles):
    _LANDSCAPE.get(dataset, render_surfaces)(row, cells, get_dataset(dataset), load_models(dataset), titles)


def order_parameter(ax, dataset):
    _ORDER_PARAMETER.get(dataset, render_order_parameter)(ax, get_dataset(dataset), load_models(dataset))


def slices(axes, dataset, tick, lbl, title):
    return _SLICES.get(dataset, render_slices)(axes, get_dataset(dataset), load_models(dataset), tick, lbl, title)
