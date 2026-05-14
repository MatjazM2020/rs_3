"""
Benchmark script for Sparse Matrix-Vector Multiplication (SpMV) kernel analysis.

Configurable parameters:
  - VLEN: Vector length in bits (256, 512, 1024)
  - L1 cache size: 8KiB or 64KiB
  - Kernel: 1=unit-stride, 2=strided, 3=gather_sorted, 4=gather_random (0=all)

The binary can run all four SpMV kernels or just a specific one:
  1. Unit-stride: Contiguous memory access pattern
  2. Strided: Fixed stride-8 memory access pattern
  3. Gather (sorted): Predictable gather pattern (sorted indices)
  4. Gather (random): Unpredictable gather pattern (random indices)

Usage:
  gem5.opt --outdir=results_8k_256_us cpu_benchmark.py --vlen=256 --l1-size=8KiB --kernel=1
  gem5.opt --outdir=results_8k_512_st cpu_benchmark.py --vlen=512 --l1-size=8KiB --kernel=2
  gem5.opt --outdir=results_64k_1024_gs cpu_benchmark.py --vlen=1024 --l1-size=64KiB --kernel=3
  gem5.opt --outdir=results_64k_1024_gr cpu_benchmark.py --vlen=1024 --l1-size=64KiB --kernel=4
"""

from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import PrivateL1CacheHierarchy
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import CustomResource
from gem5.simulate.simulator import Simulator
import sys
import os

# Parse command line arguments
VLEN = 512
L1_SIZE = "8KiB"
KERNEL = 0  # 0=all, 1=unit-stride, 2=strided, 3=gather_sorted, 4=gather_random

if len(sys.argv) > 1:
    try:
        for arg in sys.argv[1:]:
            if arg.startswith('--vlen='):
                VLEN = int(arg.split('=')[1])
            elif arg.startswith('--l1-size='):
                L1_SIZE = arg.split('=')[1]
            elif arg.startswith('--kernel='):
                KERNEL = int(arg.split('=')[1])
    except Exception as e:
        print(f"Warning: Error parsing arguments: {e}")

# Kernel names for reference
KERNEL_NAMES = {
    0: "all kernels",
    1: "unit-stride",
    2: "strided",
    3: "gather (sorted)",
    4: "gather (random)"
}

print(f"[spmv_benchmark] Configuring GEM5 with:")
print(f"  VLEN = {VLEN} bits")
print(f"  L1 cache size = {L1_SIZE}")
print(f"  Kernel: {KERNEL_NAMES.get(KERNEL, 'unknown')}")
print(f"  Scalar CPU: O3")

# Set up cache hierarchy with configurable L1 size
cache_hierarchy = PrivateL1CacheHierarchy(
    l1d_size=L1_SIZE,
    l1i_size=L1_SIZE
)

# Set up memory system
memory = SingleChannelDDR3_1600("7GiB")

# Create processor with O3 CPU (scalar processor as specified)
processor = SimpleProcessor(
    cpu_type=CPUTypes.O3,
    num_cores=1,
    isa=ISA.RISCV
)

# Configure VLEN on the core
for core in processor.get_cores():
    core.get_simobject().isa[0].vlen = VLEN

# Create board with configured components
board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy
)

# Load the binary and pass kernel ID as command-line argument
binary = CustomResource("./spmv.bin")
board.set_se_binary_workload(binary, arguments=[str(KERNEL)])

# Run simulation
print(f"[spmv_benchmark] Starting GEM5 simulation with kernel {KERNEL}...")
simulator = Simulator(board=board)
simulator.run()

print(f"[spmv_benchmark] Simulation completed for VLEN={VLEN}, L1={L1_SIZE}, kernel={KERNEL}")
