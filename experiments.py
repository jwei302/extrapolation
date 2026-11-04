import argparse
import subprocess

from data import ORDERED as DATASETS, PAIR

EXPERIMENTS = {
    "distance": (
        "transfer coefficient vs distance to Tc, at fixed hyperparameters (Fig. 4)",
        [["python", "-m", "eval.distance", "--dataset", d, "--method", m]
         for d in DATASETS for m in ("poly", "rff")]),
    "bounds_vs_n": (
        "transfer coefficient and bounds vs training-set size (Fig. 3)",
        [["python", "-m", "eval.bounds_vs_n", "--dataset", d, "--method", m]
         for d in DATASETS for m in ("poly", "rff")]),
    "convergence": (
        "Monte Carlo convergence of the GEVP bound (Fig. 5)",
        [["python", "-m", "eval.gevp_convergence", "--dataset", d, "--method", m]
         for d in PAIR for m in ("poly", "rff")]),
    "gp_vs_rff": (
        "RFF against the GP, in feature count and training size (Fig. 6)",
        [["python", "-m", "eval.gp_vs_rff"]]),
    "gp_variance": (
        "GP posterior variance against realized error (Fig. 7)",
        [["python", "-m", "eval.gp_variance"]]),
    "budget": (
        "labeled-budget estimate of MSE_Q (Fig. 8)",
        [["python", "-m", "eval.labeled_budget"]]),
    "landau": (
        "Landau coefficient and order parameter of the Heisenberg fits (Fig. 9)",
        [["python", "-m", "eval.landau_coeff"]]),
    "arpes_sensitivity": (
        "ARPES preprocessing sensitivity (Table 2)",
        [["python", "-m", "eval.arpes_preprocessing"]]),
}


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--experiment", default="all",
                   help="Comma-separated, or 'all'. Choices: " + ", ".join(EXPERIMENTS))
    p.add_argument("--list", action="store_true", help="List the experiments and exit.")
    a = p.parse_args()

    if a.list:
        for k, (desc, cmds) in EXPERIMENTS.items():
            print(f"  {k:20s} {desc}  [{len(cmds)} job(s)]")
        return

    names = list(EXPERIMENTS) if a.experiment == "all" else a.experiment.split(",")
    cmds = [c for n in names for c in EXPERIMENTS[n][1]]
    print(f"{len(cmds)} job(s) across {len(names)} experiment(s)\n")
    for i, c in enumerate(cmds, 1):
        print(f"\n[{i}/{len(cmds)}] {' '.join(c)}", flush=True)
        subprocess.run(c, check=True)
    print("\nDone. Results in results/. Next: python figures.py")


if __name__ == "__main__":
    main()
