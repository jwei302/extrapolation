import argparse
import subprocess

from data import ORDERED as DATASETS, PAIR


def _draft(fig):
    return [["python", "-m", "plot.paper_figures", "--fig", fig]]


FIGURES = {
    "landscape":      ("Fig. 1  ground truth and predicted surfaces, all targets", _draft("landscape")),
    "order_param":    ("Fig. 2  derived nonanalytic quantity", _draft("order_param")),
    "bounds_vs_n":    ("Fig. 3  transfer coefficient vs training-set size", _draft("bounds_vs_n")),
    "distance":       ("Fig. 4  transfer coefficient vs distance to Tc", _draft("distance")),
    "convergence":    ("Fig. 5  Monte Carlo convergence of the GEVP bound", _draft("convergence")),
    "gp_vs_rff":      ("Fig. 6  RFF as a finite proxy for the GP", _draft("gp_vs_rff")),
    "gp_variance":    ("Fig. 7  GP posterior variance vs realized error", _draft("gp_variance")),
    "budget":         ("Fig. 8  labeled-budget estimate of MSE_Q", _draft("budget")),
    "landau":         ("Fig. 9  Landau coefficient and order parameter", _draft("landau")),
    "neural":         ("Fig. 10 neural architecture landscapes", _draft("neural")),
    "slices":         ("Fig. 11 fixed-parameter slices", _draft("slices")),
}

TABLES = {
    "metrics":        ("Table 1  extrapolation metrics, all targets",
                       [["python", "-m", "eval.metrics_table", "--dataset", d] for d in DATASETS]),
    "metrics_neural": ("Table 3  neural baselines",
                       [["python", "-m", "eval.metrics_table", "--dataset", d,
                         "--methods", "neural"] for d in PAIR]),
    "hyperparams":    ("Tables 4-5  selected hyperparameters",
                       [["python", "-m", "eval.hyperparam_report"]]),
}


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--figure", default="", help="Comma-separated, or 'all'.")
    p.add_argument("--table", default="", help="Comma-separated, or 'all'.")
    p.add_argument("--list", action="store_true", help="List figures and tables, then exit.")
    a = p.parse_args()

    if a.list or (not a.figure and not a.table):
        print("figures:")
        for k, (d, _) in FIGURES.items():
            print(f"  {k:15s} {d}")
        print("\ntables:")
        for k, (d, _) in TABLES.items():
            print(f"  {k:15s} {d}")
        print("\nusage: python figures.py --figure all --table all")
        return

    cmds = []
    for sel, catalog in ((a.figure, FIGURES), (a.table, TABLES)):
        if not sel:
            continue
        for n in (list(catalog) if sel == "all" else sel.split(",")):
            cmds += catalog[n][1]

    print(f"{len(cmds)} job(s)\n")
    for i, c in enumerate(cmds, 1):
        print(f"\n[{i}/{len(cmds)}] {' '.join(c)}", flush=True)
        subprocess.run(c, check=True)
    print("\nDone. Figures in figs/.")


if __name__ == "__main__":
    main()
