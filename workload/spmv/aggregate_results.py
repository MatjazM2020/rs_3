#!/usr/bin/env python3
"""
Aggregate benchmark results from GEM5 SpMV runs and generate a markdown analysis report.

This script parses results from all configuration directories (organized by L1 cache size,
VLEN, and kernel type) and generates comprehensive performance analysis.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def parse_stats_file(filepath):
    """Parse a GEM5 stats.txt file and return a dictionary of metrics."""
    metrics = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and headers
                if not line or line.startswith('---'):
                    continue
                # Parse metrics in format: key value # comment
                match = re.match(r'^(\S+)\s+([^\s#]+)\s*(?:#.*)?$', line)
                if match:
                    key, value = match.groups()
                    # Try to convert to float/int
                    try:
                        if '.' in value:
                            metrics[key] = float(value)
                        else:
                            metrics[key] = int(value)
                    except ValueError:
                        metrics[key] = value
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return metrics

def extract_key_metrics(metrics):
    """Extract key performance metrics from parsed stats."""
    sim_ticks = metrics.get('simTicks', 0)
    sim_insts = metrics.get('simInsts', 0)
    
    # Calculate CPI = simTicks / simInsts
    cpi = sim_ticks / sim_insts if sim_insts > 0 else 0
    
    extracted = {
        'simSeconds': metrics.get('simSeconds', 0),
        'simTicks': sim_ticks,
        'simInsts': sim_insts,
        'cpi': cpi,
        'hostSeconds': metrics.get('hostSeconds', 0),
        'l1d_read_hits': metrics.get('board.cache_hierarchy.l1dcaches.ReadReq.hits::total', 0),
        'l1d_read_misses': metrics.get('board.cache_hierarchy.l1dcaches.ReadReq.misses::total', 0),
        'l1d_read_miss_rate': metrics.get('board.cache_hierarchy.l1dcaches.ReadReq.missRate::total', 0),
        'l1d_avg_miss_latency': metrics.get('board.cache_hierarchy.l1dcaches.ReadReq.avgMissLatency::total', 0),
        'l1i_read_hits': metrics.get('board.cache_hierarchy.l1icaches.ReadReq.hits::total', 0),
        'l1i_read_misses': metrics.get('board.cache_hierarchy.l1icaches.ReadReq.misses::total', 0),
    }
    
    return extracted

def aggregate_results(base_path):
    """Aggregate results from all configuration directories."""
    results = {}
    
    results_dir = Path(base_path) / 'benchmark_results'
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return results
    
    # Find all l1_*_vlen_*_k* directories
    config_dirs = sorted([d for d in results_dir.iterdir() 
                         if d.is_dir() and d.name.startswith('l1_')],
                        key=lambda x: x.name)
    
    for config_dir in config_dirs:
        stats_file = config_dir / 'stats.txt'
        if stats_file.exists():
            print(f"Processing {config_dir.name}...")
            metrics = parse_stats_file(stats_file)
            key_metrics = extract_key_metrics(metrics)
            results[config_dir.name] = key_metrics
    
    return results

def parse_config_name(config_name):
    """Parse configuration name to extract L1, VLEN, kernel_id, and kernel_name."""
    # Format: l1_8k_vlen_256_k1_unit_stride
    match = re.match(r'l1_(\d+)k_vlen_(\d+)_k(\d+)_(.+)', config_name)
    if match:
        return {
            'l1_size': int(match.group(1)),
            'vlen': int(match.group(2)),
            'kernel_id': int(match.group(3)),
            'kernel_name': match.group(4)
        }
    return None

def generate_markdown_report(results, output_file):
    """Generate a markdown analysis report from aggregated results."""
    
    if not results:
        print("No results to analyze")
        return
    
    # Parse all configurations
    parsed_results = {}
    for config_name, metrics in results.items():
        parsed = parse_config_name(config_name)
        if parsed:
            parsed['metrics'] = metrics
            parsed_results[config_name] = parsed
    
    # Extract unique values
    l1_sizes = sorted(set(p['l1_size'] for p in parsed_results.values()))
    vlens = sorted(set(p['vlen'] for p in parsed_results.values()))
    kernels = sorted(set((p['kernel_id'], p['kernel_name']) for p in parsed_results.values()))
    kernel_names = {kid: kname for kid, kname in kernels}
    
    report = []
    report.append("# SpMV Benchmark Analysis\n\n")
    report.append("## Overview\n\n")
    report.append("This report aggregates simulation results from GEM5 runs with different RISC-V vector lengths (VLEN),\n")
    report.append("L1 cache sizes, and SpMV kernel access patterns.\n\n")
    report.append("### Test Configuration\n\n")
    report.append(f"- **Vector Lengths (VLEN)**: {', '.join(map(str, vlens))} bits\n")
    report.append(f"- **L1 Cache Sizes**: {', '.join(str(s) + ' KiB' for s in l1_sizes)}\n")
    report.append(f"- **Kernels Tested**:\n")
    for kid in sorted(kernel_names.keys()):
        report.append(f"  - k{kid}: {kernel_names[kid]}\n")
    report.append(f"- **Total Configurations**: {len(parsed_results)}\n\n")
    
    # Summary table by kernel
    report.append("## Summary by Kernel (all L1 sizes and VLENs)\n\n")
    
    for kid in sorted(kernel_names.keys()):
        kernel_name = kernel_names[kid]
        report.append(f"### {kernel_name.replace('_', ' ').title()} (k{kid})\n\n")
        
        # Get all results for this kernel, organized by L1 and VLEN
        kernel_results = {name: data for name, data in parsed_results.items() 
                         if data['kernel_id'] == kid}
        
        report.append("| L1 (KiB) | VLEN | CPI | L1D Read Misses | L1D Avg Latency | L1D Hit Rate |\n")
        report.append("|----------|------|-----|-----------------|-----------------|-------------|\n")
        
        for l1_size in l1_sizes:
            for vlen in vlens:
                # Find matching config
                matching = [data for name, data in kernel_results.items()
                           if data['l1_size'] == l1_size and data['vlen'] == vlen]
                
                if matching:
                    data = matching[0]['metrics']
                    cpi = data['cpi']
                    misses = data['l1d_read_misses']
                    latency = data['l1d_avg_miss_latency']
                    hits = data['l1d_read_hits']
                    total_accesses = hits + misses
                    hit_rate = (hits / total_accesses * 100) if total_accesses > 0 else 0
                    
                    report.append(f"| {l1_size} | {vlen} | {cpi:.4f} | {misses} | {latency:.2f} | {hit_rate:.2f}% |\n")
        
        report.append("\n")
    
    # Detailed analysis by L1 and VLEN
    report.append("## Detailed Analysis by Configuration\n\n")
    
    for l1_size in l1_sizes:
        report.append(f"### L1 Cache Size: {l1_size} KiB\n\n")
        
        for vlen in vlens:
            report.append(f"#### VLEN = {vlen} bits\n\n")
            
            report.append("| Kernel | CPI | L1D Hits | L1D Misses | Hit Rate | Avg Latency (ticks) |\n")
            report.append("|--------|-----|----------|------------|----------|--------------------|\n")
            
            for kid in sorted(kernel_names.keys()):
                kernel_name = kernel_names[kid]
                # Find matching config
                matching = [data for name, data in parsed_results.items()
                           if data['kernel_id'] == kid and data['l1_size'] == l1_size and data['vlen'] == vlen]
                
                if matching:
                    data = matching[0]['metrics']
                    cpi = data['cpi']
                    hits = data['l1d_read_hits']
                    misses = data['l1d_read_misses']
                    total = hits + misses
                    hit_rate = (hits / total * 100) if total > 0 else 0
                    latency = data['l1d_avg_miss_latency']
                    
                    report.append(f"| {kernel_name} | {cpi:.4f} | {hits} | {misses} | {hit_rate:.2f}% | {latency:.2f} |\n")
            
            report.append("\n")
    
    # Observations and trends
    report.append("## Key Observations\n\n")
    
    # Find best and worst performers
    best_cpi_config = min(parsed_results.items(), key=lambda x: x[1]['metrics']['cpi'])
    worst_cpi_config = max(parsed_results.items(), key=lambda x: x[1]['metrics']['cpi'])
    
    best_hit_config = max(parsed_results.items(), 
                          key=lambda x: (x[1]['metrics']['l1d_read_hits'] / 
                                        (x[1]['metrics']['l1d_read_hits'] + x[1]['metrics']['l1d_read_misses']) 
                                        if (x[1]['metrics']['l1d_read_hits'] + x[1]['metrics']['l1d_read_misses']) > 0 else 0))
    worst_hit_config = min(parsed_results.items(),
                           key=lambda x: (x[1]['metrics']['l1d_read_hits'] / 
                                         (x[1]['metrics']['l1d_read_hits'] + x[1]['metrics']['l1d_read_misses'])
                                         if (x[1]['metrics']['l1d_read_hits'] + x[1]['metrics']['l1d_read_misses']) > 0 else 0))
    
    best_cpi_data = best_cpi_config[1]
    worst_cpi_data = worst_cpi_config[1]
    best_hit_data = best_hit_config[1]
    worst_hit_data = worst_hit_config[1]
    
    report.append(f"- **Best CPI**: {best_cpi_data['kernel_name']} with VLEN={best_cpi_data['vlen']}, L1={best_cpi_data['l1_size']}KiB (CPI={best_cpi_data['metrics']['cpi']:.4f})\n")
    report.append(f"- **Worst CPI**: {worst_cpi_data['kernel_name']} with VLEN={worst_cpi_data['vlen']}, L1={worst_cpi_data['l1_size']}KiB (CPI={worst_cpi_data['metrics']['cpi']:.4f})\n")
    
    best_hit_rate = (best_hit_data['metrics']['l1d_read_hits'] / 
                    (best_hit_data['metrics']['l1d_read_hits'] + best_hit_data['metrics']['l1d_read_misses']) * 100)
    worst_hit_rate = (worst_hit_data['metrics']['l1d_read_hits'] / 
                     (worst_hit_data['metrics']['l1d_read_hits'] + worst_hit_data['metrics']['l1d_read_misses']) * 100)
    
    report.append(f"- **Best L1 Hit Rate**: {best_hit_data['kernel_name']} with VLEN={best_hit_data['vlen']}, L1={best_hit_data['l1_size']}KiB ({best_hit_rate:.2f}%)\n")
    report.append(f"- **Worst L1 Hit Rate**: {worst_hit_data['kernel_name']} with VLEN={worst_hit_data['vlen']}, L1={worst_hit_data['l1_size']}KiB ({worst_hit_rate:.2f}%)\n")
    
    report.append("\n### Performance Patterns by Kernel\n\n")
    
    for kid in sorted(kernel_names.keys()):
        kernel_name = kernel_names[kid]
        kernel_results = {name: data for name, data in parsed_results.items() 
                         if data['kernel_id'] == kid}
        
        avg_cpi = sum(data['metrics']['cpi'] for data in kernel_results.values()) / len(kernel_results)
        avg_hit_rate = sum((data['metrics']['l1d_read_hits'] / 
                           (data['metrics']['l1d_read_hits'] + data['metrics']['l1d_read_misses']))
                          for data in kernel_results.values() 
                          if (data['metrics']['l1d_read_hits'] + data['metrics']['l1d_read_misses']) > 0) / len(kernel_results)
        
        report.append(f"- **{kernel_name}**: Avg CPI={avg_cpi:.4f}, Avg Hit Rate={avg_hit_rate*100:.2f}%\n")
    
    report.append("\n")
    
    # Write report to file
    with open(output_file, 'w') as f:
        f.writelines(report)
    
    print(f"Report generated: {output_file}")

if __name__ == '__main__':
    base_path = Path(__file__).parent.absolute()
    
    print(f"Aggregating results from: {base_path}")
    results = aggregate_results(str(base_path))
    
    if results:
        output_file = base_path / 'ANALYSIS.md'
        generate_markdown_report(results, str(output_file))
    else:
        print("No results found to analyze")
