#!/bin/sh
#SBATCH --job-name=scaled_dp_vectorization    
#SBATCH --output=benchmark_log.txt     
#SBATCH --cpus-per-task=2
#SBATCH --ntasks=1
#SBATCH --time=03:00:00

#SBATCH --reservation=fri 

# Set up paths to GEM5
GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM5_PATH=$GEM5_ROOT/build/RISCV_ALL_RUBY

# Print GEM5 version and check VLEN support
echo "=========================================="
echo "GEM5 Scaled Dot-Product Benchmark"
echo "=========================================="
echo ""
echo "Checking GEM5 configuration..."
srun apptainer exec $GEM5_WORKSPACE/gem5_rv.sif $GEM5_PATH/gem5.opt --help | grep -i vlen
echo ""

# Compile the kernel using apptainer
echo "Compiling kernel..."
srun apptainer exec $GEM5_WORKSPACE/gem5_rv.sif bash -c "cd $(pwd) && make clean && make"

# Run benchmark with GEM5
echo ""
echo "Running vectorization benchmark..."
echo "Testing VLEN: 128, 256, 512, 1024, 2048, 4096 bits"
echo ""

# Array of VLEN values to test
VLEN_VALUES="128 256 512 1024 2048 4096"

# Create results directory
mkdir -p benchmark_results

# Loop through each VLEN value
for VLEN in $VLEN_VALUES; do
    echo "=========================================="
    echo "Running benchmark with VLEN = $VLEN bits"
    echo "=========================================="
    
    OUTPUT_DIR="benchmark_results/vlen_${VLEN}"
    mkdir -p "$OUTPUT_DIR"
    
    srun apptainer exec $GEM5_WORKSPACE/gem5_rv.sif \
        $GEM5_PATH/gem5.opt --outdir="$OUTPUT_DIR" \
        cpu_benchmark.py --vlen="$VLEN"
    
    echo ""
done

echo "=========================================="
echo "Benchmark complete. Results in:"
echo "  - benchmark_results/vlen_*/stats.txt"
echo "=========================================="
echo ""
echo "Performance Summary:"
echo "=========================================="
echo "VLEN (bits)  | Cycles        | Instructions | CPI"
echo "-"
for VLEN in $VLEN_VALUES; do
    STATS_FILE="benchmark_results/vlen_${VLEN}/stats.txt"
    if [ -f "$STATS_FILE" ]; then
        # Extract relevant statistics
        CYCLES=$(grep "simTicks" "$STATS_FILE" | tail -1 | awk '{print $2}')
        INSTRS=$(grep "committedInsts" "$STATS_FILE" | grep "system.cpu" | tail -1 | awk '{print $2}')
        if [ -n "$CYCLES" ] && [ -n "$INSTRS" ] && [ "$INSTRS" != "0" ]; then
            CPI=$(echo "scale=4; $CYCLES / $INSTRS" | bc)
            printf "%-11d | %-13s | %-12s | %s\n" "$VLEN" "$CYCLES" "$INSTRS" "$CPI"
        fi
    fi
done
echo ""
