#!/usr/bin/env python3
"""
Advanced results extraction and analysis script for heat stencil benchmarks.

Extracts detailed performance metrics from GEM5 statistics files:
- Cycles and Instructions
- CPI (Cycles Per Instruction)
- L1-D cache metrics (hits, misses, miss rate)

Generates:
- CSV file with all metrics
- Comparison analysis between cache sizes
- Performance improvement tables
"""

import os
import sys
import csv
import re
from pathlib import Path
from collections import defaultdict


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


def extract_metrics(sec):
    """Extract key performance metrics from a single stats section."""
    def get(key):
        return sec.get(key)

    cycles = get('board.processor.cores.core.numCycles')
    instructions = get('simInsts')
    cpi = get('board.processor.cores.core.cpi')
    l1d_misses = get('board.cache_hierarchy.l1dcaches.overallMisses::total')
    l1d_miss_rate = get('board.cache_hierarchy.l1dcaches.overallMissRate::processor.cores.core.data')

    return {
        'cycles': cycles,
        'instructions': instructions,
        'cpi': cpi,
        'l1d_misses': l1d_misses,
        'l1d_miss_rate': l1d_miss_rate,
    }


def fmt_int(v):
    return f"{int(v)}" if v is not None else "N/A"

def fmt_float(v, precision=6):
    return f"{v:.{precision}f}" if v is not None else "N/A"


def main():
    results_dir = Path("benchmark_results")

    if not results_dir.exists():
        print(f"Error: Results directory '{results_dir}' not found", file=sys.stderr)
        sys.exit(1)

    print("=" * 110)
    print("Heat Stencil Performance Analysis - Detailed Results")
    print("=" * 110)

    # Collect all results: list of dicts with l1_size, vlen, impl, metrics
    results_by_l1 = defaultdict(list)
    all_results = []

    for l1_dir in sorted(results_dir.iterdir()):
        if not l1_dir.is_dir():
            continue
        l1_size = l1_dir.name

        for result_dir in sorted(l1_dir.iterdir()):
            if not result_dir.is_dir() or not result_dir.name.startswith('vlen_'):
                continue

            try:
                vlen = int(result_dir.name.replace('vlen_', ''))
            except ValueError:
                print(f"Warning: Cannot parse vlen from: {result_dir.name}", file=sys.stderr)
                continue

            stats_file = result_dir / "stats.txt"
            if not stats_file.exists():
                print(f"Warning: stats.txt not found in {result_dir}", file=sys.stderr)
                continue

            sections = parse_stats(stats_file)
            # section 0 = GEM5 init overhead, section 1 = scalar, section 2 = vector
            for i, label in enumerate(['scalar', 'vector']):
                idx = i + 1
                if idx >= len(sections):
                    print(f"Warning: No {label} section in {stats_file}", file=sys.stderr)
                    continue
                metrics = extract_metrics(sections[idx])
                entry = {'l1_size': l1_size, 'vlen': vlen, 'impl': label, **metrics}
                results_by_l1[l1_size].append(entry)
                all_results.append(entry)

    for l1_size in results_by_l1:
        results_by_l1[l1_size].sort(key=lambda x: (x['vlen'], x['impl']))

    # ========================================================================
    # Print detailed results for each L1 cache size
    # ========================================================================

    for l1_size in sorted(results_by_l1.keys()):
        print()
        print("╔" + "═" * 108 + "╗")
        print(f"║ L1 Cache Size: {l1_size:<94}║")
        print("╚" + "═" * 108 + "╝")
        print()

        print(f"{'VLEN':<12} {'Impl':<8} {'Cycles':<18} {'Instructions':<18} {'CPI':<12} {'L1-D Misses':<18} {'Miss Rate':<12}")
        print("-" * 110)

        for r in results_by_l1[l1_size]:
            print(
                f"{str(r['vlen']) + ' bits':<12} "
                f"{r['impl']:<8} "
                f"{fmt_int(r['cycles']):>17} "
                f"{fmt_int(r['instructions']):>17} "
                f"{fmt_float(r['cpi']):>11} "
                f"{fmt_int(r['l1d_misses']):>17} "
                f"{fmt_float(r['l1d_miss_rate'], 4):>11}"
            )

        print()

    # ========================================================================
    # Comparison: scalar vs vector within each L1 size and VLEN
    # ========================================================================

    print()
    print("╔" + "═" * 108 + "╗")
    print("║ Scalar vs Vector CPI Comparison                                                                            ║")
    print("╚" + "═" * 108 + "╝")
    print()

    for l1_size in sorted(results_by_l1.keys()):
        print(f"  L1: {l1_size}")
        print(f"  {'VLEN':<12} {'CPI Scalar':<14} {'CPI Vector':<14} {'Speedup':<12}")
        print("  " + "-" * 54)

        entries = results_by_l1[l1_size]
        scalar_dict = {r['vlen']: r for r in entries if r['impl'] == 'scalar'}
        vector_dict = {r['vlen']: r for r in entries if r['impl'] == 'vector'}

        for vlen in sorted(scalar_dict.keys()):
            rs = scalar_dict[vlen]
            rv = vector_dict.get(vlen)
            cpi_s = fmt_float(rs['cpi'])
            cpi_v = fmt_float(rv['cpi']) if rv else "N/A"
            if rv and rs['cpi'] and rv['cpi'] and rv['cpi'] > 0:
                speedup = f"{rs['cpi'] / rv['cpi']:.2f}x"
            else:
                speedup = "N/A"
            print(f"  {str(vlen) + ' bits':<12} {cpi_s:<14} {cpi_v:<14} {speedup:<12}")

        print()

    # ========================================================================
    # Comparison: 64KiB vs 8KiB cache
    # ========================================================================

    results_8k = results_by_l1.get('8kb') or results_by_l1.get('8kib') or results_by_l1.get('8KB')
    results_64k = results_by_l1.get('64kb') or results_by_l1.get('64kib') or results_by_l1.get('64KB')

    if results_8k and results_64k:
        print()
        print("╔" + "═" * 108 + "╗")
        print("║ Cache Size Comparison: 64KiB vs 8KiB L1                                                                    ║")
        print("╚" + "═" * 108 + "╝")
        print()

        for impl in ['scalar', 'vector']:
            print(f"  {impl.capitalize()}")
            print(f"  {'VLEN':<12} {'CPI 8KiB':<14} {'CPI 64KiB':<14} {'Improvement':<14} {'Misses 8KiB':<16} {'Misses 64KiB':<16}")
            print("  " + "-" * 86)

            d8  = {r['vlen']: r for r in results_8k  if r['impl'] == impl}
            d64 = {r['vlen']: r for r in results_64k if r['impl'] == impl}

            for vlen in sorted(d8.keys()):
                r8  = d8[vlen]
                r64 = d64.get(vlen)
                cpi8  = fmt_float(r8['cpi'])
                cpi64 = fmt_float(r64['cpi']) if r64 else "N/A"
                if r64 and r8['cpi'] and r64['cpi'] and r8['cpi'] > 0:
                    impr = f"{((r8['cpi'] - r64['cpi']) / r8['cpi']) * 100:+.2f}%"
                else:
                    impr = "N/A"
                miss8  = fmt_int(r8['l1d_misses'])
                miss64 = fmt_int(r64['l1d_misses']) if r64 else "N/A"
                print(f"  {str(vlen) + ' bits':<12} {cpi8:<14} {cpi64:<14} {impr:<14} {miss8:<16} {miss64:<16}")

            print()

    # ========================================================================
    # Save to CSV
    # ========================================================================

    csv_file = results_dir / "performance_summary.csv"
    try:
        with open(csv_file, 'w', newline='') as f:
            fieldnames = ['L1_Size', 'VLEN', 'Impl', 'Cycles', 'Instructions', 'CPI', 'L1D_Misses', 'L1D_Miss_Rate']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in sorted(all_results, key=lambda x: (x['l1_size'], x['vlen'], x['impl'])):
                writer.writerow({
                    'L1_Size': r['l1_size'],
                    'VLEN': r['vlen'],
                    'Impl': r['impl'],
                    'Cycles': fmt_int(r['cycles']),
                    'Instructions': fmt_int(r['instructions']),
                    'CPI': fmt_float(r['cpi']),
                    'L1D_Misses': fmt_int(r['l1d_misses']),
                    'L1D_Miss_Rate': fmt_float(r['l1d_miss_rate'], 4),
                })
        print(f"Results saved to: {csv_file}")
    except Exception as e:
        print(f"Error saving CSV: {e}", file=sys.stderr)

    print()
    print("=" * 110)
    print("Analysis complete!")
    print("=" * 110)


if __name__ == "__main__":
    main()
