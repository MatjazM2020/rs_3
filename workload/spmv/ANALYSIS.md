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
| 8 | 256 | 2.5533 | 104 | 49885.96 | 98.80% |
| 8 | 512 | 2.6950 | 108 | 52191.58 | 97.89% |
| 8 | 1024 | 2.8838 | 121 | 54069.84 | 96.62% |
| 64 | 256 | 2.4723 | 71 | 52393.56 | 99.18% |
| 64 | 512 | 2.5547 | 75 | 67119.48 | 98.52% |
| 64 | 1024 | 2.6339 | 86 | 55363.19 | 97.56% |

### Strided (k2)

| L1 (KiB) | VLEN | CPI | L1D Read Misses | L1D Avg Latency | L1D Hit Rate |
|----------|------|-----|-----------------|-----------------|-------------|
| 8 | 256 | 2.6128 | 167 | 60791.44 | 98.30% |
| 8 | 512 | 3.4765 | 673 | 64228.92 | 88.98% |
| 8 | 1024 | 4.2753 | 908 | 92588.67 | 79.94% |
| 64 | 256 | 2.5858 | 163 | 60904.27 | 98.34% |
| 64 | 512 | 3.3971 | 650 | 66816.71 | 89.36% |
| 64 | 1024 | 4.0599 | 877 | 92080.01 | 80.63% |

### Gather Sorted (k3)

| L1 (KiB) | VLEN | CPI | L1D Read Misses | L1D Avg Latency | L1D Hit Rate |
|----------|------|-----|-----------------|-----------------|-------------|
| 8 | 256 | 2.5297 | 112 | 59862.70 | 98.93% |
| 8 | 512 | 2.6715 | 123 | 56174.12 | 98.14% |
| 8 | 1024 | 2.8849 | 164 | 56540.96 | 96.65% |
| 64 | 256 | 2.4469 | 79 | 51745.67 | 99.24% |
| 64 | 512 | 2.5254 | 88 | 54865.53 | 98.66% |
| 64 | 1024 | 2.6163 | 120 | 64751.85 | 97.53% |

### Gather Random (k4)

| L1 (KiB) | VLEN | CPI | L1D Read Misses | L1D Avg Latency | L1D Hit Rate |
|----------|------|-----|-----------------|-----------------|-------------|
| 8 | 256 | 3.1423 | 631 | 55887.00 | 93.88% |
| 8 | 512 | 3.4057 | 656 | 63494.88 | 90.08% |
| 8 | 1024 | 3.9142 | 698 | 72138.39 | 85.74% |
| 64 | 256 | 2.6070 | 163 | 57210.63 | 98.41% |
| 64 | 512 | 2.7370 | 170 | 65260.16 | 97.41% |
| 64 | 1024 | 2.9265 | 197 | 72693.73 | 95.94% |

## Detailed Analysis by Configuration

### L1 Cache Size: 8 KiB

#### VLEN = 256 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 2.5533 | 8586 | 104 | 98.80% | 49885.96 |
| strided | 2.6128 | 9646 | 167 | 98.30% | 60791.44 |
| gather_sorted | 2.5297 | 10336 | 112 | 98.93% | 59862.70 |
| gather_random | 3.1423 | 9680 | 631 | 93.88% | 55887.00 |

#### VLEN = 512 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 2.6950 | 4999 | 108 | 97.89% | 52191.58 |
| strided | 3.4765 | 5435 | 673 | 88.98% | 64228.92 |
| gather_sorted | 2.6715 | 6490 | 123 | 98.14% | 56174.12 |
| gather_random | 3.4057 | 5956 | 656 | 90.08% | 63494.88 |

#### VLEN = 1024 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 2.8838 | 3455 | 121 | 96.62% | 54069.84 |
| strided | 4.2753 | 3619 | 908 | 79.94% | 92588.67 |
| gather_sorted | 2.8849 | 4734 | 164 | 96.65% | 56540.96 |
| gather_random | 3.9142 | 4198 | 698 | 85.74% | 72138.39 |

### L1 Cache Size: 64 KiB

#### VLEN = 256 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 2.4723 | 8562 | 71 | 99.18% | 52393.56 |
| strided | 2.5858 | 9650 | 163 | 98.34% | 60904.27 |
| gather_sorted | 2.4469 | 10336 | 79 | 99.24% | 51745.67 |
| gather_random | 2.6070 | 10114 | 163 | 98.41% | 57210.63 |

#### VLEN = 512 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 2.5547 | 4977 | 75 | 98.52% | 67119.48 |
| strided | 3.3971 | 5459 | 650 | 89.36% | 66816.71 |
| gather_sorted | 2.5254 | 6492 | 88 | 98.66% | 54865.53 |
| gather_random | 2.7370 | 6401 | 170 | 97.41% | 65260.16 |

#### VLEN = 1024 bits

| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |
|--------|-----|----------|------------|----------|--------------------|
| unit_stride | 2.6339 | 3432 | 86 | 97.56% | 55363.19 |
| strided | 4.0599 | 3651 | 877 | 80.63% | 92080.01 |
| gather_sorted | 2.6163 | 4740 | 120 | 97.53% | 64751.85 |
| gather_random | 2.9265 | 4661 | 197 | 95.94% | 72693.73 |

## Key Observations

- **Best CPI**: gather_sorted with VLEN=256, L1=64KiB (CPI=2.4469)
- **Worst CPI**: strided with VLEN=1024, L1=8KiB (CPI=4.2753)
- **Best L1 Hit Rate**: gather_sorted with VLEN=256, L1=64KiB (99.24%)
- **Worst L1 Hit Rate**: strided with VLEN=1024, L1=8KiB (79.94%)

### Performance Patterns by Kernel

- **unit_stride**: Avg CPI=2.6322, Avg Hit Rate=98.09%
- **strided**: Avg CPI=3.4013, Avg Hit Rate=89.26%
- **gather_sorted**: Avg CPI=2.6125, Avg Hit Rate=98.19%
- **gather_random**: Avg CPI=3.1221, Avg Hit Rate=93.58%

