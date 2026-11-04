#!/bin/bash
# Submit a pipeline stage to SLURM. Self-submits: ./slurm.sh <stage> [args...]
#   ./slurm.sh train --dataset heisenberg
#   ./slurm.sh experiments --experiment distance
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00
set -euo pipefail
STAGE=${1:-train}; shift || true

if [[ -z "${SLURM_JOB_ID:-}" ]]; then
    mkdir -p logs
    # Only the neural trainers need a GPU; everything else is CPU-only.
    [[ "$STAGE" == train ]] && GPU=(--partition=gpu_h200 --gpus=h200:1) || GPU=(--partition=day)
    exec sbatch --job-name="$STAGE" "${GPU[@]}" \
        --output="logs/%x_%j.out" --error="logs/%x_%j.err" "$0" "$STAGE" "$@"
fi

cd "$(git rev-parse --show-toplevel)"
source .venv/bin/activate
python -u "$STAGE.py" "$@"
