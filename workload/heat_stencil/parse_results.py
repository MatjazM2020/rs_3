#!/usr/bin/env python3
"""
Parse GEM5 stats.txt files from heat_stencil benchmark runs.

Usage:
  python3 parse_results.py
  python3 parse_results.py --results-dir ./benchmark_results
"""

import sys
import re
import argparse
from pathlib import Path


def parse_stats(filepath):
    """Return list of sections, each a dict of key->float (last value wins)."""
    sections = []
    current = {}
    in_section = False
    with open(filepath) as f:
        for line in f:
            if line.startswith('---------- Begin'):
                current = {}
                in_section = True
            elif line.startswith('---------- End'):
                if in_section:
                    sections.append(current)
                in_section = False
            elif in_section:
                m = re.match(r'^(\S+)\s+(\S+)', line)
                if m:
                    try:
                        current[m.group(1)] = float(m.group(2))
                    except ValueError:
                        current[m.group(1)] = m.group(2)
    return sections


def extract(sec, key):
    return sec.get(key)


def print_table(results_dir):
    base = Path(results_dir)
    VLENS = [128, 256, 512, 1024, 2048, 4096]

    for cache in ['8kb', '64kb']:
        print(f"\n=== L1 cache: {cache} ===")
        print(f"{'VLEN':>5} | {'impl':6} | {'CPI':>8} | {'L1 misses':>12}")
        print(f"{'-----':>5}-+-{'------':6}-+-{'--------':>8}-+-{'------------':>12}")

        for vlen in VLENS:
            stats_file = base / cache / f'vlen_{vlen}' / 'stats.txt'
            if not stats_file.exists():
                print(f"{vlen:>5} | {'?':6} | {'no file':>8} | {'?':>12}")
                continue

            sections = parse_stats(stats_file)
            # section 0 = GEM5 init overhead, section 1 = scalar, section 2 = vector
            labels = ['scalar', 'vector']
            for i, label in enumerate(labels):
                idx = i + 1
                if idx >= len(sections):
                    print(f"{vlen:>5} | {label:6} | {'no data':>8} | {'?':>12}")
                    continue
                sec = sections[idx]
                cpi    = extract(sec, 'board.processor.cores.core.cpi')
                misses = extract(sec, 'board.cache_hierarchy.l1dcaches.overallMisses::total')
                cpi_str  = f"{cpi:.4f}" if cpi is not None else "?"
                miss_str = f"{int(misses)}" if misses is not None else "?"
                print(f"{vlen:>5} | {label:6} | {cpi_str:>8} | {miss_str:>12}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir', default='./benchmark_results',
                        help='Path to benchmark_results directory')
    args = parser.parse_args()
    print_table(args.results_dir)
