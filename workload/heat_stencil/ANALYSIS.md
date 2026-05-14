# Heat Stencil Benchmark Analysis
## Overview
This report aggregates simulation results from GEM5 runs with different RISC-V Vector Processing Unit sizes (VPU) and different L1 cache size.
VPU sizes: 128, 256, 512, 1024, 2048, and 4096 bits
L1 sizes: 8 and 64 KB

## Summary Statistics

=== L1 cache: 8KB ===
 VLEN | impl   |      CPI |    L1 misses  
------|--------|----------|-------------
  128 | scalar |   2.5472 |           47
  128 | vector |   2.4678 |          282
  256 | scalar |   2.5731 |           50
  256 | vector |   2.4260 |          278
  512 | scalar |   2.6184 |           53
  512 | vector |   2.3465 |          281
 1024 | scalar |   2.6903 |           66
 1024 | vector |   2.2230 |          306
 2048 | scalar |   2.8411 |           59
 2048 | vector |   2.1026 |          289
 4096 | scalar |   3.9975 |          348
 4096 | vector |   2.2063 |          581

=== L1 cache: 64KB ===
 VLEN | impl   |      CPI |    L1 misses
------|--------|----------|-------------
  128 | scalar |   2.5370 |            0
  128 | vector |   2.4451 |           44
  256 | scalar |   2.5516 |            0
  256 | vector |   2.3763 |           44
  512 | scalar |   2.5769 |            0
  512 | vector |   2.2593 |           44
 1024 | scalar |   2.6085 |            1
 1024 | vector |   2.0936 |           45
 2048 | scalar |   2.6712 |            5
 2048 | vector |   1.9188 |           49
 4096 | scalar |   2.7973 |           10
 4096 | vector |   1.7267 |           52

## Analysis
The key parameter is `N = 1024` doubles. Each array is `1024 × 8 = 8KB`and the code uses two buffers in a ping pong pattern (`buf_a, buf_b`). Meaning so the total working set is `8KB` and it doesn't fit into the 8KB L1 cache. That is why L1 misses are much higher at `L1 8KB`. But we do see that the vector implementation CPI decreases with increased VLEN. As a larger VLEN means that each vector instruction covers more elements, so fewer instructions are needed to process the same 1024 elements.

At `L1 64KB` there are barely any cache misses, but with increased VLEN size vector CPI drops, as it procesess more data per cycle.

