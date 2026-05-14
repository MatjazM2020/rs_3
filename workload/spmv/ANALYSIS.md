# SpMV Benchmark Analysis

## Overview

This report aggregates simulation results from GEM5 runs with different RISC-V vector lengths (VLEN),
L1 cache sizes, and SpMV kernel access patterns.

### Test Configuration

- **Vector Lengths (VLEN)**: 256, 512, 1024 bits
- **L1 Cache Sizes**: 8 KiB, 64 KiB
- **Kernels Tested**:
  - k1: unit_stride
  - k2: strided
  - k3: gather_sorted
  - k4: gather_random
- **Total Configurations**: 24

## Summary by Kernel (all L1 sizes and VLENs)

### Unit Stride (k1)

| L1 (KiB) | VLEN | CPI | L1D Read Misses | L1D Avg Latency | L1D Hit Rate |
|----------|------|-----|-----------------|-----------------|-------------|
| 8 | 256 | 850.2641 | 104 | 49885.96 | 98.80% |
| 8 | 512 | 897.4339 | 108 | 52191.58 | 97.89% |
| 8 | 1024 | 960.2961 | 121 | 54069.84 | 96.62% |
| 64 | 256 | 823.2717 | 71 | 52393.56 | 99.18% |
| 64 | 512 | 850.7079 | 75 | 67119.48 | 98.52% |
| 64 | 1024 | 877.0736 | 86 | 55363.19 | 97.56% |

### Strided (k2)

| L1 (KiB) | VLEN | CPI | L1D Read Misses | L1D Avg Latency | L1D Hit Rate |
|----------|------|-----|-----------------|-----------------|-------------|
| 8 | 256 | 870.0629 | 167 | 60791.44 | 98.30% |
| 8 | 512 | 1157.6849 | 673 | 64228.92 | 88.98% |
| 8 | 1024 | 1423.6868 | 908 | 92588.67 | 79.94% |
| 64 | 256 | 861.0772 | 163 | 60904.27 | 98.34% |
| 64 | 512 | 1131.2488 | 650 | 66816.71 | 89.36% |
| 64 | 1024 | 1351.9629 | 877 | 92080.01 | 80.63% |

### Gather Sorted (k3)

| L1 (KiB) | VLEN | CPI | L1D Read Misses | L1D Avg Latency | L1D Hit Rate |
|----------|------|-----|-----------------|-----------------|-------------|
| 8 | 256 | 842.4009 | 112 | 59862.70 | 98.93% |
| 8 | 512 | 889.6006 | 123 | 56174.12 | 98.14% |
| 8 | 1024 | 960.6835 | 164 | 56540.96 | 96.65% |
| 64 | 256 | 814.8180 | 79 | 51745.67 | 99.24% |
| 64 | 512 | 840.9653 | 88 | 54865.53 | 98.66% |
| 64 | 1024 | 871.2231 | 120 | 64751.85 | 97.53% |

### Gather Random (k4)

| L1 (KiB) | VLEN | CPI | L1D Read Misses | L1D Avg Latency | L1D Hit Rate |
|----------|------|-----|-----------------|-----------------|-------------|
| 8 | 256 | 1046.3798 | 631 | 55887.00 | 93.88% |
| 8 | 512 | 1134.1026 | 656 | 63494.88 | 90.08% |
| 8 | 1024 | 1303.4311 | 698 | 72138.39 | 85.74% |
| 64 | 256 | 868.1458 | 163 | 57210.63 | 98.41% |
| 64 | 512 | 911.4266 | 170 | 65260.16 | 97.41% |
| 64 | 1024 | 974.5313 | 197 | 72693.73 | 95.94% |

## Detailed Analysis by Configuration

### L1 Cache Size: 8 KiB

#### VLEN = 256 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 850.2641 | 8586 | 104 | 98.80% | 49885.96 |
| strided | 870.0629 | 9646 | 167 | 98.30% | 60791.44 |
| gather_sorted | 842.4009 | 10336 | 112 | 98.93% | 59862.70 |
| gather_random | 1046.3798 | 9680 | 631 | 93.88% | 55887.00 |

#### VLEN = 512 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 897.4339 | 4999 | 108 | 97.89% | 52191.58 |
| strided | 1157.6849 | 5435 | 673 | 88.98% | 64228.92 |
| gather_sorted | 889.6006 | 6490 | 123 | 98.14% | 56174.12 |
| gather_random | 1134.1026 | 5956 | 656 | 90.08% | 63494.88 |

#### VLEN = 1024 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 960.2961 | 3455 | 121 | 96.62% | 54069.84 |
| strided | 1423.6868 | 3619 | 908 | 79.94% | 92588.67 |
| gather_sorted | 960.6835 | 4734 | 164 | 96.65% | 56540.96 |
| gather_random | 1303.4311 | 4198 | 698 | 85.74% | 72138.39 |

### L1 Cache Size: 64 KiB

#### VLEN = 256 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 823.2717 | 8562 | 71 | 99.18% | 52393.56 |
| strided | 861.0772 | 9650 | 163 | 98.34% | 60904.27 |
| gather_sorted | 814.8180 | 10336 | 79 | 99.24% | 51745.67 |
| gather_random | 868.1458 | 10114 | 163 | 98.41% | 57210.63 |

#### VLEN = 512 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 850.7079 | 4977 | 75 | 98.52% | 67119.48 |
| strided | 1131.2488 | 5459 | 650 | 89.36% | 66816.71 |
| gather_sorted | 840.9653 | 6492 | 88 | 98.66% | 54865.53 |
| gather_random | 911.4266 | 6401 | 170 | 97.41% | 65260.16 |

#### VLEN = 1024 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 877.0736 | 3432 | 86 | 97.56% | 55363.19 |
| strided | 1351.9629 | 3651 | 877 | 80.63% | 92080.01 |
| gather_sorted | 871.2231 | 4740 | 120 | 97.53% | 64751.85 |
| gather_random | 974.5313 | 4661 | 197 | 95.94% | 72693.73 |

## Key Observations

- **Best CPI**: gather_sorted with VLEN=256, L1=64KiB (CPI=814.8180)
- **Worst CPI**: strided with VLEN=1024, L1=8KiB (CPI=1423.6868)
- **Best L1 Hit Rate**: gather_sorted with VLEN=256, L1=64KiB (99.24%)
- **Worst L1 Hit Rate**: strided with VLEN=1024, L1=8KiB (79.94%)

### Performance Patterns by Kernel

- **unit_stride**: Avg CPI=876.5079, Avg Hit Rate=98.09%
- **strided**: Avg CPI=1132.6206, Avg Hit Rate=89.26%
- **gather_sorted**: Avg CPI=869.9486, Avg Hit Rate=98.19%
- **gather_random**: Avg CPI=1039.6695, Avg Hit Rate=93.58%

