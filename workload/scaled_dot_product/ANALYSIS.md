# Scaled Dot Product Benchmark Analysis
## Overview
This report aggregates simulation results from GEM5 runs with different RISC-V vector lengths (VLEN).
Vector lengths tested: 128, 256, 512, 1024, 2048, 4096

## Summary Statistics

| VLEN | Sim Time (s) | Instructions | Sim Freq (GHz) | IPS | L1 Hit Rate | Avg Miss Latency |
|------|--------------|--------------|----------------|-----|-------------|------------------|
| 128 | 0.000124 | 160832 | 0.11 | 1.30e+09 | 99.29% | 58153 |
| 256 | 0.000088 | 117047 | 0.11 | 1.33e+09 | 99.06% | 61516 |
| 512 | 0.000087 | 116539 | 0.11 | 1.34e+09 | 99.37% | 56679 |
| 1024 | 0.000087 | 116564 | 0.11 | 1.34e+09 | 99.56% | 50191 |
| 2048 | 0.000167 | 152510 | 0.15 | 9.13e+08 | 97.02% | 25018 |
| 4096 | 0.000610 | 141146 | 0.19 | 2.31e+08 | 64.25% | 65459 |

## Detailed Analysis

### Simulation Performance

**Simulation Time (seconds)**: Time simulated in the GEM5 simulator

| VLEN | Sim Time (s) |
|------|-------------|
| 128 | 1.240000e-04 |
| 256 | 8.800000e-05 |
| 512 | 8.700000e-05 |
| 1024 | 8.700000e-05 |
| 2048 | 1.670000e-04 |
| 4096 | 6.100000e-04 |

### Instruction Metrics

| VLEN | Instructions | Instructions/Second |
|------|--------------|---------------------|
| 128 | 160832 | 1.30e+09 |
| 256 | 117047 | 1.33e+09 |
| 512 | 116539 | 1.34e+09 |
| 1024 | 116564 | 1.34e+09 |
| 2048 | 152510 | 9.13e+08 |
| 4096 | 141146 | 2.31e+08 |

### L1 Data Cache Performance

| VLEN | Hits | Misses | Hit Rate | Miss Rate | Avg Miss Latency (ticks) |
|------|------|--------|----------|-----------|------------------------|
| 128 | 59729 | 430 | 99.29% | 0.7148% | 58153 |
| 256 | 39194 | 371 | 99.06% | 0.9377% | 61516 |
| 512 | 54164 | 342 | 99.37% | 0.6275% | 56679 |
| 1024 | 70297 | 314 | 99.56% | 0.4447% | 50191 |
| 2048 | 112118 | 3448 | 97.02% | 2.9836% | 25018 |
| 4096 | 115858 | 64457 | 64.25% | 35.7469% | 65459 |

## Observations

- **Fastest simulation**: VLEN 512 with 8.700000e-05 seconds
- **Slowest simulation**: VLEN 4096 with 6.100000e-04 seconds
- **Best L1 cache hit rate**: VLEN 1024 with 99.56% hit rate
- **Worst L1 cache hit rate**: VLEN 4096 with 64.25% hit rate

