#!/usr/bin/env python3
"""
Advanced results extraction and analysis script for heat stencil benchmarks.

Extracts detailed performance metrics from GEM5 statistics files:
- Cycles and Instructions
- CPI (Cycles Per Instruction)
- L1-D cache metrics (hits, misses, miss rate)
- Vector operations statistics
- Branch prediction statistics

Generates:
- CSV file with all metrics
- Comparison analysis between cache sizes
- Performance improvement tables
"""

import os
import sys
import csv
import json
from pathlib import Path
from collections import defaultdict

def parse_stats_file(stats_file):
    """Parse GEM5 stats.txt file and extract all metrics."""
    metrics = {}
    
    try:
        with open(stats_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and separators
                if not line or line.startswith('---') or line.startswith('#'):
                    continue
                
                # Parse lines in format: metric_name value description
                parts = line.split()
                if len(parts) >= 2:
                    metric_name = parts[0]
                    try:
                        # Try to parse as float
                        metric_value = float(parts[1])
                        metrics[metric_name] = metric_value
                    except ValueError:
                        # Skip non-numeric values
                        pass
    except Exception as e:
        print(f"Error parsing {stats_file}: {e}", file=sys.stderr)
    
    return metrics

def find_metric(metrics, possible_names):
    """Find a metric by trying multiple possible names."""
    for name in possible_names:
        if name in metrics:
            return metrics[name]
    return None

def extract_performance_metrics(metrics):
    """Extract key performance metrics from GEM5 statistics."""
    result = {}
    
    # Cycles
    cycles = find_metric(metrics, [
        'simTicks',
        'system.cpu.numCycles',
        'system.cpu_cluster.cpu.numCycles',
        'system.cpu.ticksNotIdling'
    ])
    result['cycles'] = cycles
    
    # Instructions
    instructions = find_metric(metrics, [
        'system.cpu.committedInsts',
        'system.cpu_cluster.cpu.committedInsts',
        'system.cpu.op_class::total'
    ])
    result['instructions'] = instructions
    
    # CPI
    if cycles and instructions and instructions > 0:
        result['cpi'] = cycles / instructions
    else:
        result['cpi'] = None
    
    # L1-D Cache metrics
    l1d_misses = find_metric(metrics, [
        'system.cpu.dcache.overallMisses',
        'system.cpu.dcache.misses',
        'system.cpu_cluster.cpu.dcache.overallMisses',
        'system.cpu_cluster.cpu.dcache.misses'
    ])
    result['l1d_misses'] = l1d_misses
    
    l1d_hits = find_metric(metrics, [
        'system.cpu.dcache.overallHits',
        'system.cpu.dcache.hits',
        'system.cpu_cluster.cpu.dcache.overallHits',
        'system.cpu_cluster.cpu.dcache.hits'
    ])
    result['l1d_hits'] = l1d_hits
    
    l1d_accesses = find_metric(metrics, [
        'system.cpu.dcache.overallAccesses',
        'system.cpu.dcache.accesses',
        'system.cpu_cluster.cpu.dcache.overallAccesses',
        'system.cpu_cluster.cpu.dcache.accesses'
    ])
    result['l1d_accesses'] = l1d_accesses
    
    # Compute L1-D miss rate
    if l1d_misses and l1d_accesses and l1d_accesses > 0:
        result['l1d_miss_rate'] = (l1d_misses / l1d_accesses) * 100
    else:
        result['l1d_miss_rate'] = None
    
    # L1-I Cache metrics
    l1i_misses = find_metric(metrics, [
        'system.cpu.icache.overallMisses',
        'system.cpu.icache.misses',
        'system.cpu_cluster.cpu.icache.overallMisses'
    ])
    result['l1i_misses'] = l1i_misses
    
    return result

def main():
    """Main analysis function."""
    results_dir = Path("benchmark_results")
    
    if not results_dir.exists():
        print(f"Error: Results directory '{results_dir}' not found", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 100)
    print("Heat Stencil Performance Analysis - Detailed Results")
    print("=" * 100)
    print()
    
    # Organize results by L1 cache size
    results_by_l1 = defaultdict(list)
    all_results = []
    
    # Discover all result directories
    for result_dir in sorted(results_dir.iterdir()):
        if not result_dir.is_dir():
            continue
        
        dir_name = result_dir.name
        if not dir_name.startswith('l1_'):
            continue
        
        # Parse directory name: l1_<size>_vlen_<vlen>
        try:
            # Extract L1 size and VLEN from directory name
            parts = dir_name.replace('l1_', '').split('_vlen_')
            l1_size = parts[0]
            vlen = int(parts[1])
        except (IndexError, ValueError):
            print(f"Warning: Cannot parse directory name: {dir_name}", file=sys.stderr)
            continue
        
        stats_file = result_dir / "stats.txt"
        if not stats_file.exists():
            print(f"Warning: stats.txt not found in {result_dir}", file=sys.stderr)
            continue
        
        # Parse metrics
        raw_metrics = parse_stats_file(str(stats_file))
        perf_metrics = extract_performance_metrics(raw_metrics)
        
        result_entry = {
            'l1_size': l1_size,
            'vlen': vlen,
            'dir': result_dir.name,
            **perf_metrics
        }
        
        results_by_l1[l1_size].append(result_entry)
        all_results.append(result_entry)
    
    # Sort by VLEN within each L1 size
    for l1_size in results_by_l1:
        results_by_l1[l1_size].sort(key=lambda x: x['vlen'])
    
    # ========================================================================
    # Print detailed results for each L1 cache size
    # ========================================================================
    
    for l1_size in sorted(results_by_l1.keys()):
        print()
        print("╔" + "═" * 98 + "╗")
        print(f"║ L1 Cache Size: {l1_size:<84}║")
        print("╚" + "═" * 98 + "╝")
        print()
        
        # Print table header
        print(f"{'VLEN':<12} {'Cycles':<18} {'Instructions':<18} {'CPI':<12} {'L1-D Misses':<18} {'Miss Rate':<12}")
        print("-" * 100)
        
        # Print data rows
        for result in results_by_l1[l1_size]:
            vlen_str = f"{result['vlen']} bits"
            cycles_str = f"{int(result['cycles'])}" if result['cycles'] is not None else "N/A"
            instr_str = f"{int(result['instructions'])}" if result['instructions'] is not None else "N/A"
            cpi_str = f"{result['cpi']:.6f}" if result['cpi'] is not None else "N/A"
            misses_str = f"{int(result['l1d_misses'])}" if result['l1d_misses'] is not None else "N/A"
            rate_str = f"{result['l1d_miss_rate']:.2f}%" if result['l1d_miss_rate'] is not None else "N/A"
            
            print(f"{vlen_str:<12} {cycles_str:>17} {instr_str:>17} {cpi_str:>11} {misses_str:>17} {rate_str:>11}")
        
        print()
    
    # ========================================================================
    # Comparison: 64KiB vs 8KiB cache
    # ========================================================================
    
    print()
    print("╔" + "═" * 98 + "╗")
    print("║ Performance Comparison: 64KiB vs 8KiB L1 Cache                                              ║")
    print("╚" + "═" * 98 + "╝")
    print()
    
    l1_sizes = sorted(results_by_l1.keys())
    if len(l1_sizes) >= 2:
        # Find 8KiB and 64KiB results
        results_8k = None
        results_64k = None
        
        for size, results_list in results_by_l1.items():
            if '8' in size and 'K' in size:
                results_8k = results_list
            elif '64' in size and 'K' in size:
                results_64k = results_list
        
        if results_8k and results_64k:
            results_8k_dict = {r['vlen']: r for r in results_8k}
            results_64k_dict = {r['vlen']: r for r in results_64k}
            
            print(f"{'VLEN':<12} {'CPI (8KiB)':<18} {'CPI (64KiB)':<18} {'CPI Improvement':<18} {'Miss Rate (8KiB)':<18} {'Miss Rate (64KiB)':<18}")
            print("-" * 100)
            
            for vlen in sorted(results_8k_dict.keys()):
                if vlen in results_64k_dict:
                    r8k = results_8k_dict[vlen]
                    r64k = results_64k_dict[vlen]
                    
                    vlen_str = f"{vlen} bits"
                    cpi_8k_str = f"{r8k['cpi']:.6f}" if r8k['cpi'] is not None else "N/A"
                    cpi_64k_str = f"{r64k['cpi']:.6f}" if r64k['cpi'] is not None else "N/A"
                    
                    if r8k['cpi'] and r64k['cpi'] and r64k['cpi'] > 0:
                        improvement = ((r8k['cpi'] - r64k['cpi']) / r8k['cpi']) * 100
                        improvement_str = f"{improvement:+.2f}%"
                    else:
                        improvement_str = "N/A"
                    
                    rate_8k_str = f"{r8k['l1d_miss_rate']:.2f}%" if r8k['l1d_miss_rate'] is not None else "N/A"
                    rate_64k_str = f"{r64k['l1d_miss_rate']:.2f}%" if r64k['l1d_miss_rate'] is not None else "N/A"
                    
                    print(f"{vlen_str:<12} {cpi_8k_str:>17} {cpi_64k_str:>17} {improvement_str:>17} {rate_8k_str:>17} {rate_64k_str:>17}")
        
        print()
    
    # ========================================================================
    # Save to CSV
    # ========================================================================
    
    csv_file = results_dir / "performance_summary.csv"
    try:
        with open(csv_file, 'w', newline='') as f:
            fieldnames = [
                'L1_Size', 'VLEN', 'Cycles', 'Instructions', 'CPI',
                'L1D_Misses', 'L1D_Miss_Rate', 'L1I_Misses'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in sorted(all_results, key=lambda x: (x['l1_size'], x['vlen'])):
                writer.writerow({
                    'L1_Size': result['l1_size'],
                    'VLEN': result['vlen'],
                    'Cycles': int(result['cycles']) if result['cycles'] else '',
                    'Instructions': int(result['instructions']) if result['instructions'] else '',
                    'CPI': f"{result['cpi']:.6f}" if result['cpi'] else '',
                    'L1D_Misses': int(result['l1d_misses']) if result['l1d_misses'] else '',
                    'L1D_Miss_Rate': f"{result['l1d_miss_rate']:.2f}" if result['l1d_miss_rate'] else '',
                    'L1I_Misses': int(result['l1i_misses']) if result['l1i_misses'] else '',
                })
        
        print(f"Results saved to: {csv_file}")
    except Exception as e:
        print(f"Error saving CSV: {e}", file=sys.stderr)
    
    print()
    print("=" * 100)
    print("Analysis complete!")
    print("=" * 100)

if __name__ == "__main__":
    main()
