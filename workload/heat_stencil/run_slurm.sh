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
        --l1d=8KiB
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
        --l1d=64KiB
    echo "  done (exit $?)"
done

echo ""
echo "--- Results Summary ---"
echo ""

for CACHE in 8kb 64kb; do
    echo "Cache: $CACHE"
    echo "VLEN  | impl   | CPI      | L1 misses"
    echo "------|--------|----------|-----------"
    for VLEN in $VLENS; do
        STATS="$SCRIPT_DIR/benchmark_results/$CACHE/vlen_$VLEN/stats.txt"
        if [ ! -f "$STATS" ]; then
            echo "$VLEN  | -      | no stats |"
            continue
        fi

        # stats.txt has two sections separated by "---": first=scalar, second=vector
        # Extract CPI: numCycles / committedInsts per section
        python3 - "$STATS" "$VLEN" "$CACHE" <<'PYEOF'
import sys, re

stats_file = sys.argv[1]
vlen       = sys.argv[2]
cache      = sys.argv[3]

# Split into sections on Begin/End markers.
# Multiple records may exist within a section; keep the last value for each key.
sections = []
current  = {}
in_section = False
with open(stats_file) as f:
    for line in f:
        if line.startswith('---------- Begin'):
            current = {}
            in_section = True
        elif line.startswith('---------- End'):
            if in_section:
                sections.append(current)
            in_section = False
        elif in_section:
            m = re.match(r'^(\S+)\s+(\S+)', line)
            if m:
                key, val = m.group(1), m.group(2)
                try:
                    current[key] = float(val)
                except ValueError:
                    current[key] = val

def get(sec, key):
    return sec.get(key)

labels = ['scalar', 'vector']
for i, label in enumerate(labels):
    idx = i + 1  # section 0 is GEM5 init overhead; scalar=1, vector=2
    if idx >= len(sections):
        print(f"{vlen:5} | {label:6} | no data  |")
        continue
    sec    = sections[idx]
    cpi    = get(sec, 'board.processor.cores.core.cpi')
    misses = get(sec, 'board.cache_hierarchy.l1dcaches.overallMisses::total')
    cpi_str  = f"{cpi:.4f}" if cpi is not None else "?"
    miss_str = f"{int(misses)}" if misses is not None else "?"
    print(f"{vlen:5} | {label:6} | {cpi_str:8} | {miss_str}")
PYEOF

    done
    echo ""
done

echo "Completed: $(date)"
