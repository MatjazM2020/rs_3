"""
Benchmark script for scaled dot-product attention kernel vectorization.

Runs ONE simulation with a configurable VLEN value.
To test multiple VLEN values, invoke this script multiple times with different VLEN.

Usage:
  gem5.opt --outdir=results_128 cpu_benchmark.py --vlen=128
  gem5.opt --outdir=results_256 cpu_benchmark.py --vlen=256
  etc.
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

# Get VLEN from command line (default: 512)
VLEN = 512
if len(sys.argv) > 1:
    try:
        # Parse --vlen=VALUE format
        for arg in sys.argv[1:]:
            if arg.startswith('--vlen='):
                VLEN = int(arg.split('=')[1])
                break
    except:
        pass

print(f"[cpu_benchmark] Configuring GEM5 with VLEN = {VLEN} bits")

# Set up cache hierarchy with 8KB L1 caches
cache_hierarchy = PrivateL1CacheHierarchy(
    l1d_size="8KiB",
    l1i_size="8KiB"
)

# Set up memory system
memory = SingleChannelDDR3_1600("7GiB")

# Create processor with O3 CPU
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
binary = CustomResource("./scaled_dot_product.bin")
board.set_se_binary_workload(binary)

# Run simulation
print(f"[cpu_benchmark] Starting GEM5 simulation...")
simulator = Simulator(board=board)
simulator.run()

print(f"[cpu_benchmark] Simulation completed for VLEN={VLEN}")

