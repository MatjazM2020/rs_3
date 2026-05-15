#!/bin/bash
# ============================================================================
# Extract and display key metrics from a GEM5 simulation results directory
# ============================================================================
# Usage: 
#   ./extract_metrics.sh <results_directory>
#   ./extract_metrics.sh benchmark_results/l1_8KiB_vlen_512
# ============================================================================

if [ $# -eq 0 ]; then
    echo "Usage: $0 <results_directory>"
    echo ""
    echo "Examples:"
    echo "  $0 benchmark_results/l1_8KiB_vlen_512"
    echo "  $0 benchmark_results/l1_64KiB_vlen_1024"
    exit 1
fi

RESULT_DIR="$1"
STATS_FILE="$RESULT_DIR/stats.txt"

if [ ! -f "$STATS_FILE" ]; then
    echo "Error: stats.txt not found in $RESULT_DIR"
    exit 1
fi

echo "==========================================================================="
echo "GEM5 Simulation Metrics - $(basename $RESULT_DIR)"
echo "==========================================================================="
echo ""

# Extract key metrics using grep and awk
echo "Performance Metrics:"
echo "-------------------"

# Cycles
echo -n "  Cycles (numCycles):          "
grep "system.cpu.numCycles" "$STATS_FILE" | awk '{print $2}'

# Instructions
echo -n "  Instructions (committedInsts):"
grep "system.cpu.committedInsts" "$STATS_FILE" | head -1 | awk '{print $2}'

# CPI calculation
CYCLES=$(grep "system.cpu.numCycles" "$STATS_FILE" | awk '{print $2}')
INSTRS=$(grep "system.cpu.committedInsts" "$STATS_FILE" | head -1 | awk '{print $2}')

if [ -n "$CYCLES" ] && [ -n "$INSTRS" ] && [ "$INSTRS" != "0" ]; then
    CPI=$(echo "scale=6; $CYCLES / $INSTRS" | bc 2>/dev/null)
    echo "  CPI (computed):              $CPI"
fi

echo ""
echo "L1-D Cache Metrics:"
echo "-------------------"

# L1-D Cache stats
echo -n "  L1-D Accesses:               "
grep "system.cpu.dcache" "$STATS_FILE" | grep "overallAccesses\|accesses" | head -1 | awk '{print $2}'

echo -n "  L1-D Hits:                   "
grep "system.cpu.dcache" "$STATS_FILE" | grep "overallHits\|hits" | head -1 | awk '{print $2}'

echo -n "  L1-D Misses:                 "
grep "system.cpu.dcache" "$STATS_FILE" | grep "overallMisses\|misses" | head -1 | awk '{print $2}'

# Calculate miss rate
ACCESSES=$(grep "system.cpu.dcache" "$STATS_FILE" | grep "overallAccesses\|accesses" | head -1 | awk '{print $2}')
MISSES=$(grep "system.cpu.dcache" "$STATS_FILE" | grep "overallMisses\|misses" | head -1 | awk '{print $2}')

if [ -n "$ACCESSES" ] && [ -n "$MISSES" ] && [ "$ACCESSES" != "0" ]; then
    MISS_RATE=$(echo "scale=4; 100 * $MISSES / $ACCESSES" | bc 2>/dev/null)
    echo "  L1-D Miss Rate:              $MISS_RATE%"
fi

echo ""
echo "L1-I Cache Metrics:"
echo "-------------------"

echo -n "  L1-I Accesses:               "
grep "system.cpu.icache" "$STATS_FILE" | grep "overallAccesses\|accesses" | head -1 | awk '{print $2}'

echo -n "  L1-I Hits:                   "
grep "system.cpu.icache" "$STATS_FILE" | grep "overallHits\|hits" | head -1 | awk '{print $2}'

echo -n "  L1-I Misses:                 "
grep "system.cpu.icache" "$STATS_FILE" | grep "overallMisses\|misses" | head -1 | awk '{print $2}'

echo ""
echo "Branch Prediction:"
echo "-------------------"

echo -n "  Branches:                    "
grep "system.cpu.branchPred.*Branches" "$STATS_FILE" | head -1 | awk '{print $2}' || echo "N/A"

echo -n "  Correct Predictions:         "
grep "system.cpu.branchPred.*correct" "$STATS_FILE" | head -1 | awk '{print $2}' || echo "N/A"

echo ""
echo "Memory System:"
echo "----------------"

echo -n "  Memory Reads:                "
grep "system.mem" "$STATS_FILE" | grep "totMemoryReads" | awk '{print $2}' || echo "N/A"

echo -n "  Memory Writes:               "
grep "system.mem" "$STATS_FILE" | grep "totMemoryWrites" | awk '{print $2}' || echo "N/A"

echo ""
echo "==========================================================================="
echo ""
