"""
Benchmark script for heat stencil kernel.

Runs ONE simulation with a configurable VLEN and cache size.
Usage:
  gem5.opt --outdir=results_128_8kb cpu_benchmark.py --vlen=128 --l1d=8KiB
  gem5.opt --outdir=results_256_64kb cpu_benchmark.py --vlen=256 --l1d=64KiB
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

VLEN = 512
L1D_SIZE = "8KiB"

for arg in sys.argv[1:]:
    if arg.startswith('--vlen='):
        VLEN = int(arg.split('=')[1])
    elif arg.startswith('--l1d='):
        L1D_SIZE = arg.split('=')[1]

print(f"[cpu_benchmark] VLEN={VLEN} bits, L1D={L1D_SIZE}")

cache_hierarchy = PrivateL1CacheHierarchy(
    l1d_size=L1D_SIZE,
    l1i_size="8KiB"
)

memory = SingleChannelDDR3_1600("7GiB")

processor = SimpleProcessor(
    cpu_type=CPUTypes.O3,
    num_cores=1,
    isa=ISA.RISCV
)

for core in processor.get_cores():
    core.get_simobject().isa[0].vlen = VLEN

board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy
)

binary = CustomResource("./heat_stencil.bin")
board.set_se_binary_workload(binary)

print(f"[cpu_benchmark] Starting GEM5 simulation...")
simulator = Simulator(board=board)
simulator.run()

print(f"[cpu_benchmark] Simulation completed for VLEN={VLEN}, L1D={L1D_SIZE}")
