#!/bin/bash
#SBATCH --job-name=heat_stencil_benchmark
#SBATCH --output=benchmark_log.txt
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --reservation=fri

GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_PATH=$GEM5_WORKSPACE/gem5
GEM5_BIN=$GEM5_PATH/build/RISCV/gem5.opt
SCRIPT_DIR=$SLURM_SUBMIT_DIR

echo "=== Heat Stencil Benchmark ==="
echo "Started: $(date)"
echo "Script dir: $SCRIPT_DIR"
echo ""

# Compile the binary
echo "--- Compiling ---"
cd "$SCRIPT_DIR"
apptainer exec $GEM5_WORKSPACE/gem5_rv.sif make
echo ""

VLENS="128 256 512 1024 2048 4096"

# ── 8KB L1 cache runs ────────────────────────────────────────────────────────
echo "--- Running with 8KB L1 cache ---"
for VLEN in $VLENS; do
    OUTDIR="$SCRIPT_DIR/benchmark_results/8kb/vlen_${VLEN}"
    mkdir -p "$OUTDIR"
    echo "[$(date +%H:%M:%S)] VLEN=$VLEN, L1D=8KiB -> $OUTDIR"
    apptainer exec $GEM5_WORKSPACE/gem5_rv.sif \
        $GEM5_BIN \
        --outdir="$OUTDIR" \
        "$SCRIPT_DIR/cpu_benchmark.py" \
        --vlen=$VLEN \
        --l1-size=8KiB
    echo "  done (exit $?)"
done

# ── 64KB L1 cache runs ───────────────────────────────────────────────────────
echo ""
echo "--- Running with 64KB L1 cache ---"
for VLEN in $VLENS; do
    OUTDIR="$SCRIPT_DIR/benchmark_results/64kb/vlen_${VLEN}"
    mkdir -p "$OUTDIR"
    echo "[$(date +%H:%M:%S)] VLEN=$VLEN, L1D=64KiB -> $OUTDIR"
    apptainer exec $GEM5_WORKSPACE/gem5_rv.sif \
        $GEM5_BIN \
        --outdir="$OUTDIR" \
        "$SCRIPT_DIR/cpu_benchmark.py" \
        --vlen=$VLEN \
        --l1-size=64KiB
    echo "  done (exit $?)"
done

echo ""
echo "Completed: $(date)"
