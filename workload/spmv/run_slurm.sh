#!/bin/sh
#SBATCH --job-name=spmv_analysis
#SBATCH --output=spmv_benchmark.log
#SBATCH --cpus-per-task=2
#SBATCH --ntasks=1
#SBATCH --time=24:00:00
#SBATCH --reservation=fri

# ============================================================================
# Sparse Matrix-Vector Multiplication (SpMV) Performance Analysis
# ============================================================================
# Tests all four SpMV kernels:
# 1. Unit-stride: Contiguous memory access pattern
# 2. Strided: Fixed stride-8 memory access pattern
# 3. Gather (sorted): Predictable gather with sorted column indices
# 4. Gather (random): Unpredictable gather with random column indices
#
# Experimental setup:
# - L1 cache sizes: 8KB and 64KB
# - Vector lengths (VLEN): 256, 512, 1024 bits
# - Scalar CPU: O3 with default settings
#
# Metrics collected per kernel:
# - CPI (Cycles Per Instruction)
# - L1 cache miss events
# ============================================================================

# Set up paths to GEM5
GEM5_WORKSPACE=/d/hpc/projects/FRI/GEM5/gem5_workspace
GEM5_ROOT=$GEM5_WORKSPACE/gem5
GEM5_PATH=$GEM5_ROOT/build/RISCV_ALL_RUBY

# Print header
echo "=========================================="
echo "SpMV Kernel Performance Analysis"
echo "=========================================="
echo "Using GEM5 from: $GEM5_PATH"
echo "Starting at: $(date)"
echo ""

# Test GEM5 availability
echo "Checking GEM5 configuration..."
if srun apptainer exec $GEM5_WORKSPACE/gem5_rv.sif $GEM5_PATH/gem5.opt --help > /tmp/gem5_help.txt 2>&1; then
    if grep -q -i vlen /tmp/gem5_help.txt; then
        echo "✓ GEM5 with VLEN support detected"
    else
        echo "⚠ GEM5 help output (no VLEN found, but proceeding):"
        head -5 /tmp/gem5_help.txt
    fi
else
    echo "ERROR: Failed to run GEM5"
    exit 1
fi
echo ""

# Compile the kernel
echo "=========================================="
echo "Compiling spmv kernel..."
echo "=========================================="
WORK_DIR=$(pwd)
echo "Working directory: $WORK_DIR"

srun apptainer exec $GEM5_WORKSPACE/gem5_rv.sif bash -c "cd $WORK_DIR && make clean && make" || {
    echo "ERROR: Compilation failed"
    exit 1
}

if [ ! -f ./spmv.bin ]; then
    echo "ERROR: Failed to compile spmv.bin"
    echo "Listing directory contents:"
    ls -la
    exit 1
fi
echo "✓ Compilation successful!"
echo ""

# Define test parameters
VLEN_VALUES="256 512 1024"
L1_SIZES="8KiB 64KiB"
KERNEL_IDS="1 2 3 4"
KERNEL_NAMES="unit_stride strided gather_sorted gather_random"

# Create results directory
mkdir -p benchmark_results

# Generate summary file header
SUMMARY_FILE="benchmark_results/performance_summary.txt"
{
    echo "=============================================================================="
    echo "SpMV Performance Analysis Summary"
    echo "=============================================================================="
    echo "Experimental Configuration:"
    echo "  - Scalar Processor: O3 (default settings)"
    echo "  - Clock Frequency: 3GHz"
    echo "  - Memory: 7GiB DDR3-1600"
    echo ""
    echo "Test Parameters:"
    echo "  - Vector Lengths (VLEN): 256, 512, 1024 bits"
    echo "  - L1 Cache Sizes: 8KiB, 64KiB"
    echo "  - Kernels:"
    echo "    1. Unit-stride:  contiguous memory access"
    echo "    2. Strided:      stride-8 memory access"
    echo "    3. Gather (sorted): predictable gather"
    echo "    4. Gather (random): unpredictable gather"
    echo ""
    echo "Test commenced at: $(date)"
    echo "=============================================================================="
    echo ""
} > "$SUMMARY_FILE"

# Initialize counters
TOTAL_TESTS=0
COMPLETED_TESTS=0

# Count total tests
for L1_SIZE in $L1_SIZES; do
    for VLEN in $VLEN_VALUES; do
        for KERNEL_ID in $KERNEL_IDS; do
            TOTAL_TESTS=$((TOTAL_TESTS + 1))
        done
    done
done

echo "Total tests to run: $TOTAL_TESTS"
echo ""

# Loop through each L1 cache size
for L1_SIZE in $L1_SIZES; do
    echo "=========================================="
    echo "Testing with L1 cache size: $L1_SIZE"
    echo "=========================================="
    echo ""
    
    # Normalize cache size name for directory
    L1_NAME=$(echo "$L1_SIZE" | sed 's/[KiB]//g')
    
    # Loop through each VLEN value
    for VLEN in $VLEN_VALUES; do
        echo "VLEN = $VLEN bits:"
        
        # Loop through each kernel
        KERNEL_IDX=0
        for KERNEL_ID in $KERNEL_IDS; do
            KERNEL_NAME=$(echo "$KERNEL_NAMES" | awk "{print \$$((KERNEL_IDX + 1))}")
            COMPLETED_TESTS=$((COMPLETED_TESTS + 1))
            
            echo "  [$COMPLETED_TESTS/$TOTAL_TESTS] Running $KERNEL_NAME kernel..."
            
            OUTPUT_DIR="benchmark_results/l1_${L1_NAME}k_vlen_${VLEN}_k${KERNEL_ID}_${KERNEL_NAME}"
            mkdir -p "$OUTPUT_DIR"
            
            # Run the simulation with SPMV_KERNEL environment variable
            srun bash -c "export SPMV_KERNEL=$KERNEL_ID; apptainer exec $GEM5_WORKSPACE/gem5_rv.sif $GEM5_PATH/gem5.opt --outdir=\"$OUTPUT_DIR\" cpu_benchmark.py --vlen=\"$VLEN\" --l1-size=\"$L1_SIZE\" --kernel=\"$KERNEL_ID\""
            
            if [ $? -eq 0 ]; then
                echo "    ✓ Completed successfully"
            else
                echo "    ✗ FAILED"
            fi
            
            KERNEL_IDX=$((KERNEL_IDX + 1))
        done
        echo ""
    done
done

# ============================================================================
# Results Analysis
# ============================================================================
echo ""
echo "=========================================="
echo "Analyzing Results"
echo "=========================================="
echo ""

# Function to extract metrics from stats.txt
extract_cpi_and_l1_misses() {
    local stats_file="$1"
    
    if [ ! -f "$stats_file" ]; then
        return
    fi
    
    # Extract metrics using the new GEM5 naming convention
    # CPI = simTicks / simInsts
    local sim_ticks=$(grep "^simTicks" "$stats_file" | awk '{print $2}')
    local sim_insts=$(grep "^simInsts" "$stats_file" | awk '{print $2}')
    local cpi="N/A"
    
    if [ -n "$sim_ticks" ] && [ -n "$sim_insts" ] && [ "$sim_insts" -gt 0 ]; then
        cpi=$(echo "scale=4; $sim_ticks / $sim_insts" | bc)
    fi
    
    # L1 read misses using new naming
    local l1_misses=$(grep "board.cache_hierarchy.l1dcaches.ReadReq.misses::total" "$stats_file" | tail -1 | awk '{print $2}')
    
    echo "$cpi|$l1_misses"
}

# Create CSV files for easy import to spreadsheets
CSV_FILE_8K="$SUMMARY_FILE"
CSV_FILE_DETAILED="benchmark_results/detailed_metrics.csv"

{
    echo "L1_Cache_Size,VLEN_bits,Kernel_ID,Kernel_Name,CPI,L1_Read_Misses,Total_Cycles,Total_Instructions"
} > "$CSV_FILE_DETAILED"

# Generate detailed results
echo "Detailed Performance Report:" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

for L1_SIZE in $L1_SIZES; do
    L1_NAME=$(echo "$L1_SIZE" | sed 's/[KiB]//g')
    
    echo "L1 Cache: $L1_SIZE" >> "$SUMMARY_FILE"
    echo "================================" >> "$SUMMARY_FILE"
    
    for VLEN in $VLEN_VALUES; do
        echo "" >> "$SUMMARY_FILE"
        echo "VLEN = $VLEN bits:" >> "$SUMMARY_FILE"
        echo "────────────────────" >> "$SUMMARY_FILE"
        
        KERNEL_IDX=0
        for KERNEL_ID in $KERNEL_IDS; do
            KERNEL_NAME=$(echo "$KERNEL_NAMES" | awk "{print \$$((KERNEL_IDX + 1))}")
            OUTPUT_DIR="benchmark_results/l1_${L1_NAME}k_vlen_${VLEN}_k${KERNEL_ID}_${KERNEL_NAME}"
            STATS_FILE="$OUTPUT_DIR/stats.txt"
            
            if [ -f "$STATS_FILE" ]; then
                echo "" >> "$SUMMARY_FILE"
                echo "  Kernel: $KERNEL_NAME (ID=$KERNEL_ID)" >> "$SUMMARY_FILE"
                
                SIM_TICKS=$(grep "^simTicks" "$STATS_FILE" | tail -1 | awk '{print $2}')
                SIM_INSTS=$(grep "^simInsts" "$STATS_FILE" | tail -1 | awk '{print $2}')
                CPI="N/A"
                if [ -n "$SIM_TICKS" ] && [ -n "$SIM_INSTS" ] && [ "$SIM_INSTS" -gt 0 ]; then
                    CPI=$(echo "scale=4; $SIM_TICKS / $SIM_INSTS" | bc)
                fi
                L1_MISSES=$(grep "board.cache_hierarchy.l1dcaches.ReadReq.misses::total" "$STATS_FILE" | tail -1 | awk '{print $2}')
                NUM_CYCLES=$SIM_TICKS
                NUM_INSTRS=$SIM_INSTS
                
                if [ -n "$CPI" ]; then
                    printf "    CPI:              %s\n" "$CPI" >> "$SUMMARY_FILE"
                fi
                if [ -n "$L1_MISSES" ]; then
                    printf "    L1 Read Misses:   %s\n" "$L1_MISSES" >> "$SUMMARY_FILE"
                fi
                if [ -n "$NUM_CYCLES" ]; then
                    printf "    Total Cycles:     %s\n" "$NUM_CYCLES" >> "$SUMMARY_FILE"
                fi
                if [ -n "$NUM_INSTRS" ]; then
                    printf "    Total Instructions: %s\n" "$NUM_INSTRS" >> "$SUMMARY_FILE"
                fi
                
                # Add to CSV
                printf "%s,%s,%s,%s,%s,%s,%s,%s\n" \
                    "$L1_NAME" "$VLEN" "$KERNEL_ID" "$KERNEL_NAME" \
                    "$CPI" "$L1_MISSES" "$NUM_CYCLES" "$NUM_INSTRS" >> "$CSV_FILE_DETAILED"
            fi
            
            KERNEL_IDX=$((KERNEL_IDX + 1))
        done
    done
    
    echo "" >> "$SUMMARY_FILE"
done

# Display console output summary tables
echo ""
echo "=========================================="
echo "Performance Summary Tables (Console Output)"
echo "=========================================="
echo ""

for L1_SIZE in $L1_SIZES; do
    L1_NAME=$(echo "$L1_SIZE" | sed 's/[KiB]//g')
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "L1 Cache Size: $L1_SIZE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    for VLEN in $VLEN_VALUES; do
        echo ""
        echo "VLEN = $VLEN bits"
        echo "───────────────────────────────────────────────────────────"
        echo "Kernel           | CPI        | L1 Read Misses"
        echo "─────────────────────────────────────────────────────────────"
        
        KERNEL_IDX=0
        for KERNEL_ID in $KERNEL_IDS; do
            KERNEL_NAME=$(echo "$KERNEL_NAMES" | awk "{print \$$((KERNEL_IDX + 1))}")
            OUTPUT_DIR="benchmark_results/l1_${L1_NAME}k_vlen_${VLEN}_k${KERNEL_ID}_${KERNEL_NAME}"
            STATS_FILE="$OUTPUT_DIR/stats.txt"
            
            if [ -f "$STATS_FILE" ]; then
                SIM_TICKS=$(grep "^simTicks" "$STATS_FILE" | tail -1 | awk '{print $2}')
                SIM_INSTS=$(grep "^simInsts" "$STATS_FILE" | tail -1 | awk '{print $2}')
                CPI="N/A"
                if [ -n "$SIM_TICKS" ] && [ -n "$SIM_INSTS" ] && [ "$SIM_INSTS" -gt 0 ]; then
                    CPI=$(echo "scale=4; $SIM_TICKS / $SIM_INSTS" | bc)
                fi
                L1_MISSES=$(grep "board.cache_hierarchy.l1dcaches.ReadReq.misses::total" "$STATS_FILE" | tail -1 | awk '{print $2}')
                
                if [ -n "$CPI" ] && [ -n "$L1_MISSES" ]; then
                    printf "%-16s | %-10s | %s\n" "$KERNEL_NAME" "$CPI" "$L1_MISSES"
                fi
            fi
            
            KERNEL_IDX=$((KERNEL_IDX + 1))
        done
    done
    echo ""
done

# Generate markdown analysis report
echo ""
echo "=========================================="
echo "Generating ANALYSIS.md report..."
echo "=========================================="
python3 aggregate_results.py
if [ $? -eq 0 ]; then
    echo "✓ Report generation successful"
else
    echo "⚠ Report generation encountered an issue (but benchmarks completed)"
fi
echo ""

# Summary
echo ""
echo "=========================================="
echo "Analysis Complete"
echo "=========================================="
echo "Results saved in:"
echo "  - ANALYSIS.md (generated analysis report)"
echo "  - benchmark_results/ (detailed stats for each configuration)"
echo "  - benchmark_results/performance_summary.txt (text summary)"
echo "  - benchmark_results/detailed_metrics.csv (CSV export)"
echo ""
echo "Directory structure:"
echo "  benchmark_results/"
echo "  ├── l1_8k_vlen_256_k1_unit_stride/"
echo "  ├── l1_8k_vlen_256_k2_strided/"
echo "  ├── l1_8k_vlen_256_k3_gather_sorted/"
echo "  ├── l1_8k_vlen_256_k4_gather_random/"
echo "  ├── ... (and so on for other VLEN and L1 sizes)"
echo "  ├── performance_summary.txt"
echo "  └── detailed_metrics.csv"
echo ""
echo "Each result directory contains:"
echo "  - config.ini (GEM5 configuration)"
echo "  - stats.txt (detailed performance metrics)"
echo ""
echo "Completed at: $(date)"
echo "=========================================="
