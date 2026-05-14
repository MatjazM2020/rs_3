# Heat Stencil Benchmark Analysis
## Overview
This report aggregates simulation results from GEM5 runs with different RISC-V Vector Processing Unit sizes (VPU) and different L1 cache size.
VPU sizes: 128, 256, 512, 1024, 2048, and 4096 bits
L1 sizes: 8 and 64 KB

## Summary Statistics

=== L1 cache: 8KB ===
 VPU  | impl   |      CPI |    L1 misses  
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
 VPU  | impl   |      CPI |    L1 misses
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
The benchmark operates on two `8KB` buffers (`16KB` total), exceeding the capacity of the `8KB` L1 cache, increasing cache pressure. Because of this the `8KB` cache has substantially higher L1 misses than the `64KB` cache, where the working set fits into the cache. Higher cache misses for the vector implementation are likley due to the vector kernel boundary lookahead that loads (`u[i+vl]`) causing additional cache misses.

The vector implementation achives lower CPI than the scalar version and its CPI decreases with increased VPU width. As a wider VPU processes more elements per instruction, meaning fewer instructions are needed to process the same 1024 elements.

At `L1 64KB` there are barely any cache misses, but  as before with increased VPU size vector CPI drops, as it procesess more data per cycle.

