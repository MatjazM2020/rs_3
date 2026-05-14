# Heat Stencil Kernel - Performance Analysis

This benchmark analyzes the performance of a 1D heat diffusion equation stencil kernel using both scalar and vectorized (RVV) implementations on GEM5.

## Problem Description

The heat diffusion equation is solved using a 3-point stencil:

$$u_{new}[i] = u[i] + \alpha \cdot (u[i-1] - 2 \cdot u[i] + u[i+1])$$

Where:
- `u[i-1]`, `u[i]`, `u[i+1]` are three neighboring temperature values
- `alpha` is the diffusion coefficient
- Boundary conditions: `u[0] = u[N-1] = 0.0` (Dirichlet)

## Files

- `heat_stencil.c` - Implementation with scalar and vectorized RVV kernels
- `Makefile` - Compilation rules for RISC-V target
- `cpu_benchmark.py` - GEM5 configuration script with configurable VLEN and L1 cache size
- `run_slurm.sh` - SLURM job script that runs all benchmark configurations
- `analyze_results.py` - Analysis script to extract and compare results
- `benchmark_results/` - Directory containing simulation outputs

## Compilation

The kernel is compiled using the RISC-V GCC compiler with RVV extensions:

```bash
make clean && make
```

This generates `heat_stencil.bin`, the executable for GEM5 simulation.

## Benchmark Configurations

### Test Matrix

The benchmark runs with the following configurations:

**L1 Cache Sizes:** 8KiB, 64KiB  
**Vector Lengths (VLEN):** 128, 256, 512, 1024, 2048, 4096 bits  
**CPU:** O3 processor (out-of-order execution)  
**Clock Frequency:** 3 GHz  
**Memory:** Single-channel DDR3-1600 (7GiB)

Total number of simulations: 2 × 6 = **12 experiments**

## Running the Benchmark

### Via SLURM (Recommended)

Submit the full benchmark suite:

```bash
sbatch run_slurm.sh
```

This runs all 12 configurations and generates results in `benchmark_results/`.

### Individual Simulation

Run a single configuration directly:

```bash
srun apptainer exec /d/hpc/projects/FRI/GEM5/gem5_workspace/gem5_rv.sif \
    /d/hpc/projects/FRI/GEM5/gem5_workspace/gem5/build/RISCV_ALL_RUBY/gem5.opt \
    --outdir=results_test \
    cpu_benchmark.py --vlen=128 --l1-size=8KiB
```

## Output and Analysis

After the SLURM job completes, results are organized in:

```
benchmark_results/
├── l1_8KiB_vlen_128/
│   ├── stats.txt          # GEM5 statistics
│   ├── config.json        # Configuration snapshot
│   └── ...
├── l1_8KiB_vlen_256/
├── ...
├── l1_64KiB_vlen_4096/
└── performance_summary.txt
```

### Extract Results

To analyze all results and generate comparison tables:

```bash
python3 analyze_results.py
```

This script:
1. Parses `stats.txt` from each simulation
2. Calculates CPI (Cycles Per Instruction)
3. Extracts L1 cache miss statistics
4. Generates side-by-side comparison tables
5. Computes cache size impact on performance

### Key Metrics Reported

- **CPI:** Cycles per instruction (lower is better)
- **L1 Misses:** Total number of L1 cache misses
- **L1 Miss Rate:** Percentage of L1 cache accesses that miss
- **Improvement:** Performance gain with 64KiB vs 8KiB cache (%)

## Expected Results

### Performance Trends

1. **VLEN Effect:** Larger VLEN values generally reduce CPI for memory-bound workloads
2. **Cache Effect:** 64KiB L1 cache should show better performance (lower CPI) than 8KiB
3. **Cache Miss Rate:** Smaller caches typically have higher miss rates

### Example Output

```
========================================
L1 Cache Size: 8KiB
========================================

VLEN (bits)  | CPI           | L1 Misses        | L1 Miss Rate
-----------  | ---           | ---------        | -----------
128          | 2.450321      | 15234            | 12.45%
256          | 2.120456      | 12567            | 10.23%
512          | 1.890234      | 9876             | 8.34%
...

Comparison: 64KiB vs 8KiB L1 Cache (CPI Improvement)

VLEN (bits)  | CPI 8KiB      | CPI 64KiB        | Improvement
-----------  | --------      | --------         | -----------
128          | 2.450321      | 2.120456         | 13.44%
256          | 2.120456      | 1.890234         | 10.85%
...
```

## Implementation Notes

### Scalar Kernel

```c
void heat_step_scalar(const double * restrict u,
                      double       * restrict u_new,
                      int N, double alpha)
{
    u_new[0] = 0.0;
    u_new[N - 1] = 0.0;
    
    for (int i = 1; i < N - 1; i++) {
        double left   = u[i - 1];
        double center = u[i];
        double right  = u[i + 1];
        u_new[i] = center + alpha * (left - 2.0 * center + right);
    }
}
```

### Vectorized Kernel (RVV)

Uses strip-mining with RVV intrinsics:
- `vsetvl_e64m1()` - Configure vector length for 64-bit elements
- `vle64_v_f64m1()` - Load 64-bit floating-point values
- `vfslide1up/down_vf_f64m1()` - Gather left/right neighbors
- `vfmacc_vf_f64m1()` - Fused multiply-add for stencil computation
- `vse64_v_f64m1()` - Store results back to memory

## Verification

The program verifies vectorized results match scalar results with a tolerance of 1e-10:

```
Verification: max |scalar - vector| = 1.234e-15  [PASS]
```

## References

- RISC-V Vector Extension (RVV) Specification
- GEM5 Simulator Documentation
- Heat Equation Stencil Kernel - Classic finite difference method

## Questions / Issues

For questions about the benchmark, refer to the `GEM5_RVV.md` documentation or contact the course instructor.
