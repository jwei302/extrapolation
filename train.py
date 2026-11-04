import argparse
import subprocess

from configs import get_config
from data import ORDERED as DATASETS, PAIR
from eval.gp_vs_rff import M_LIST
from models import METHODS, KERNEL, TARGETS
from utils import SEEDS


def jobs_for(dataset, method):
    if method in KERNEL:
        jobs = [["python", "-m", "eval.sweep", "--method", method, "--dataset", dataset]]
        if method != "gp":      # the reference model whose hyperparameters Figs. 3 and 4 pin
            jobs.append(jobs[0] + ["--distance", str(get_config(dataset).DISTANCES[0])])
        if method == "rff" and dataset in PAIR:
            jobs += [jobs[0] + ["--features", str(m)] for m in M_LIST]
        return jobs
    return [["python", "-m", f"models.{method}", "--dataset", dataset, "--seed", str(s), "--n", "2000"]
            for s in SEEDS]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", default="all", help=f"Comma-separated, or 'all'. Choices: {', '.join(DATASETS)}")
    p.add_argument("--method", default="all", help=f"Comma-separated, or 'all'. Choices: {', '.join(METHODS)}")
    p.add_argument("--list", action="store_true", help="List the methods, the datasets each trains on, and exit.")
    a = p.parse_args()

    datasets = DATASETS if a.dataset == "all" else a.dataset.split(",")
    methods = list(METHODS) if a.method == "all" else a.method.split(",")
    if a.list:
        for m in methods:
            ds_m = [d for d in datasets if d in TARGETS[m]]
            print(f"  {m:8s} {METHODS[m]:17s} {', '.join(ds_m)}  [{sum(len(jobs_for(d, m)) for d in ds_m)} job(s)]")
        return

    cmds = [c for m in methods for d in datasets if d in TARGETS[m] for c in jobs_for(d, m)]

    print(f"{len(cmds)} job(s)\n")
    for i, c in enumerate(cmds, 1):
        print(f"\n[{i}/{len(cmds)}] {' '.join(c)}", flush=True)
        subprocess.run(c, check=True)
    print("\nDone. Models in results/models/. Next: python experiments.py")


if __name__ == "__main__":
    main()
