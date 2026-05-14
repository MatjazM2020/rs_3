#!/usr/bin/env python3
"""
Analysis script to extract and compare performance metrics from GEM5 simulations.

Extracts:
  - CPI (Cycles Per Instruction)
  - L1 cache miss events
  - L1 cache miss rate

Usage:
  python3 analyze_results.py
"""

import os
import sys
import json
from pathlib import Path

def parse_stats_file(stats_file):
    """Parse GEM5 stats.txt file and extract relevant metrics."""
    metrics = {}
    
    try:
        with open(stats_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('---'):
                    continue
                
                # Parse lines in format: metric_name metric_value
                parts = line.split()
                if len(parts) >= 2:
                    metric_name = parts[0]
                    try:
                        metric_value = float(parts[1])
                        metrics[metric_name] = metric_value
                    except ValueError:
                        # Skip non-numeric values
                        pass
    except Exception as e:
        print(f"Error parsing {stats_file}: {e}")
    
    return metrics

def calculate_cpi(metrics):
    """Calculate CPI from metrics."""
    # Look for cycles and instructions metrics
    possible_cycle_metrics = [
        'system.cpu.numCycles',
        'system.cpu_cluster.cpu.numCycles',
        'simTicks'
    ]
    
    possible_instr_metrics = [
        'system.cpu.committedInsts',
        'system.cpu_cluster.cpu.committedInsts',
        'system.cpu.op_class::total',
    ]
    
    cycles = None
    instrs = None
    
    for metric in possible_cycle_metrics:
        if metric in metrics:
            cycles = metrics[metric]
            break
    
    for metric in possible_instr_metrics:
        if metric in metrics:
            instrs = metrics[metric]
            break
    
    if cycles is not None and instrs is not None and instrs > 0:
        return cycles / instrs
    return None

def get_l1_stats(metrics):
    """Extract L1 cache statistics."""
    l1_misses = None
    l1_accesses = None
    
    # Look for L1 cache miss metrics
    for key in metrics.keys():
        if 'l1' in key.lower() and 'miss' in key.lower():
            l1_misses = metrics[key]
        if 'l1' in key.lower() and 'access' in key.lower():
            l1_accesses = metrics[key]
    
    miss_rate = None
    if l1_accesses is not None and l1_accesses > 0 and l1_misses is not None:
        miss_rate = (l1_misses / l1_accesses) * 100
    
    return {
        'misses': l1_misses,
        'accesses': l1_accesses,
        'miss_rate': miss_rate
    }

def main():
    """Main analysis function."""
    results_dir = Path("benchmark_results")
    
    if not results_dir.exists():
        print(f"Error: Results directory '{results_dir}' not found")
        sys.exit(1)
    
    print("=" * 80)
    print("Heat Stencil Performance Analysis")
    print("=" * 80)
    print()
    
    # Organize results by L1 cache size
    results_by_l1 = {}
    
    for result_dir in sorted(results_dir.iterdir()):
        if not result_dir.is_dir():
            continue
        
        # Parse directory name: l1_<size>_vlen_<size>
        dir_name = result_dir.name
        if not dir_name.startswith('l1_'):
            continue
        
        try:
            parts = dir_name.split('_')
            l1_size = f"{parts[1]}_{parts[2]}"  # e.g., "8KiB"
            vlen = int(parts[4])
        except (IndexError, ValueError):
            print(f"Warning: Cannot parse directory name: {dir_name}")
            continue
        
        stats_file = result_dir / "stats.txt"
        if not stats_file.exists():
            print(f"Warning: stats.txt not found in {result_dir}")
            continue
        
        # Parse metrics
        metrics = parse_stats_file(str(stats_file))
        cpi = calculate_cpi(metrics)
        l1_stats = get_l1_stats(metrics)
        
        # Organize by L1 size
        if l1_size not in results_by_l1:
            results_by_l1[l1_size] = []
        
        results_by_l1[l1_size].append({
            'vlen': vlen,
            'cpi': cpi,
            'l1_stats': l1_stats,
            'raw_metrics': metrics
        })
    
    # Print results organized by L1 cache size
    for l1_size in sorted(results_by_l1.keys()):
        print()
        print("╔" + "═" * 78 + "╗")
        print(f"║ L1 Cache Size: {l1_size:<67}║")
        print("╚" + "═" * 78 + "╝")
        print()
        
        # Sort by VLEN
        results_by_l1[l1_size].sort(key=lambda x: x['vlen'])
        
        # Print table header
        print(f"{'VLEN (bits)':<15} {'CPI':<15} {'L1 Misses':<20} {'L1 Miss Rate':<15}")
        print("-" * 65)
        
        # Print data rows
        for result in results_by_l1[l1_size]:
            vlen = result['vlen']
            cpi = result['cpi']
            l1_misses = result['l1_stats']['misses']
            miss_rate = result['l1_stats']['miss_rate']
            
            cpi_str = f"{cpi:.6f}" if cpi is not None else "N/A"
            misses_str = f"{int(l1_misses)}" if l1_misses is not None else "N/A"
            rate_str = f"{miss_rate:.2f}%" if miss_rate is not None else "N/A"
            
            print(f"{vlen:<15} {cpi_str:<15} {misses_str:<20} {rate_str:<15}")
        
    # Comparison analysis
    print()
    print("╔" + "═" * 78 + "╗")
    print("║ Comparison: 64KiB vs 8KiB L1 Cache (CPI Improvement)                      ║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    if "8KiB" in results_by_l1 and "64KiB" in results_by_l1:
        results_8k = {r['vlen']: r for r in results_by_l1["8KiB"]}
        results_64k = {r['vlen']: r for r in results_by_l1["64KiB"]}
        
        print(f"{'VLEN (bits)':<15} {'CPI 8KiB':<15} {'CPI 64KiB':<15} {'Improvement':<15}")
        print("-" * 60)
        
        for vlen in sorted(results_8k.keys()):
            if vlen in results_64k:
                cpi_8k = results_8k[vlen]['cpi']
                cpi_64k = results_64k[vlen]['cpi']
                
                if cpi_8k is not None and cpi_64k is not None and cpi_64k > 0:
                    improvement = ((cpi_8k - cpi_64k) / cpi_8k) * 100
                    print(f"{vlen:<15} {cpi_8k:<15.6f} {cpi_64k:<15.6f} {improvement:>13.2f}%")
    
    print()
    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
