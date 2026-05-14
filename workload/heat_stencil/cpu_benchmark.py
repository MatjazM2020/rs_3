"""
Benchmark script for 1D Heat Stencil kernel vectorization analysis.

Configurable parameters:
  - VLEN: Vector length in bits (128, 256, 512, 1024, 2048, 4096)
  - L1 cache size: 8KB or 64KB

Usage:
  gem5.opt --outdir=results_8k_128 cpu_benchmark.py --vlen=128 --l1-size=8KiB
  gem5.opt --outdir=results_8k_256 cpu_benchmark.py --vlen=256 --l1-size=8KiB
  gem5.opt --outdir=results_64k_128 cpu_benchmark.py --vlen=128 --l1-size=64KiB
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

if len(sys.argv) > 1:
    try:
        for arg in sys.argv[1:]:
            if arg.startswith('--vlen='):
                VLEN = int(arg.split('=')[1])
            elif arg.startswith('--l1-size='):
                L1_SIZE = arg.split('=')[1]
    except Exception as e:
        print(f"Warning: Error parsing arguments: {e}")

print(f"[heat_stencil] Configuring GEM5 with:")
print(f"  VLEN = {VLEN} bits")
print(f"  L1 cache size = {L1_SIZE}")

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

# Load the binary
binary = CustomResource("./heat_stencil.bin")
board.set_se_binary_workload(binary)

# Run simulation
print(f"[heat_stencil] Starting GEM5 simulation...")
simulator = Simulator(board=board)
simulator.run()

print(f"[heat_stencil] Simulation completed for VLEN={VLEN}, L1={L1_SIZE}")
