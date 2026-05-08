#!/usr/bin/env python3
"""
Aggregate benchmark results from GEM5 scaled_dot_product runs
and generate a markdown analysis report.
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import json

def parse_stats_file(filepath):
    """Parse a GEM5 stats.txt file and return a dictionary of metrics.
    Takes the LAST occurrence of each metric (for checkpoint simulations)."""
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
    extracted = {
        'simSeconds': metrics.get('simSeconds', 0),
        'simTicks': metrics.get('simTicks', 0),
        'simInsts': metrics.get('simInsts', 0),
        'hostSeconds': metrics.get('hostSeconds', 0),
        'hostTickRate': metrics.get('hostTickRate', 0),
        'l1_demand_hits': metrics.get('board.cache_hierarchy.l1dcaches.demandHits::total', 0),
        'l1_demand_misses': metrics.get('board.cache_hierarchy.l1dcaches.demandMisses::total', 0),
        'l1_miss_rate': metrics.get('board.cache_hierarchy.l1dcaches.demandMissRate::total', 0),
        'l1_avg_miss_latency': metrics.get('board.cache_hierarchy.l1dcaches.demandAvgMissLatency::total', 0),
    }
    
    # Calculate derived metrics
    if extracted['simSeconds'] > 0:
        extracted['ips'] = extracted['simInsts'] / extracted['simSeconds']  # Instructions per second
    if extracted['hostSeconds'] > 0:
        extracted['sim_speedup'] = extracted['simSeconds'] / extracted['hostSeconds']
    
    return extracted

def aggregate_results(base_path):
    """Aggregate results from all vector length directories."""
    results = {}
    
    results_dir = Path(base_path) / 'benchmark_results'
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return results
    
    # Find all vlen_* directories
    vlen_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith('vlen_')],
                       key=lambda x: int(x.name.split('_')[1]))
    
    for vlen_dir in vlen_dirs:
        stats_file = vlen_dir / 'stats.txt'
        if stats_file.exists():
            print(f"Processing {vlen_dir.name}...")
            metrics = parse_stats_file(stats_file)
            key_metrics = extract_key_metrics(metrics)
            vlen = int(vlen_dir.name.split('_')[1])
            results[vlen] = key_metrics
    
    return results

def generate_markdown_report(results, output_file):
    """Generate a markdown analysis report from aggregated results."""
    
    if not results:
        print("No results to analyze")
        return
    
    # Sort by vector length
    sorted_vlens = sorted(results.keys())
    
    report = []
    report.append("# Scaled Dot Product Benchmark Analysis\n")
    report.append("## Overview\n")
    report.append(f"This report aggregates simulation results from GEM5 runs with different RISC-V vector lengths (VLEN).\n")
    report.append(f"Vector lengths tested: {', '.join(map(str, sorted_vlens))}\n\n")
    
    # Summary Table
    report.append("## Summary Statistics\n\n")
    report.append("| VLEN | Sim Time (s) | Instructions | Sim Freq (GHz) | IPS | L1 Hit Rate | Avg Miss Latency |\n")
    report.append("|------|--------------|--------------|----------------|-----|-------------|------------------|\n")
    
    for vlen in sorted_vlens:
        data = results[vlen]
        sim_time = data.get('simSeconds', 0)
        insts = data.get('simInsts', 0)
        sim_freq = data.get('hostTickRate', 0) / 1e9
        ips = data.get('ips', 0)
        l1_hits = data.get('l1_demand_hits', 0)
        l1_misses = data.get('l1_demand_misses', 0)
        l1_total = l1_hits + l1_misses
        hit_rate = (l1_hits / l1_total * 100) if l1_total > 0 else 0
        miss_latency = data.get('l1_avg_miss_latency', 0)
        
        report.append(f"| {vlen} | {sim_time:.6f} | {insts} | {sim_freq:.2f} | {ips:.2e} | {hit_rate:.2f}% | {miss_latency:.0f} |\n")
    
    report.append("\n")
    
    # Detailed Analysis by Metric
    report.append("## Detailed Analysis\n\n")
    
    # Simulation Performance
    report.append("### Simulation Performance\n\n")
    report.append("**Simulation Time (seconds)**: Time simulated in the GEM5 simulator\n\n")
    report.append("| VLEN | Sim Time (s) |\n")
    report.append("|------|-------------|\n")
    for vlen in sorted_vlens:
        report.append(f"| {vlen} | {results[vlen]['simSeconds']:.6e} |\n")
    report.append("\n")
    
    # Instruction Metrics
    report.append("### Instruction Metrics\n\n")
    report.append("| VLEN | Instructions | Instructions/Second |\n")
    report.append("|------|--------------|---------------------|\n")
    for vlen in sorted_vlens:
        data = results[vlen]
        ips = data.get('ips', 0)
        report.append(f"| {vlen} | {data['simInsts']} | {ips:.2e} |\n")
    report.append("\n")
    
    # Cache Performance
    report.append("### L1 Data Cache Performance\n\n")
    report.append("| VLEN | Hits | Misses | Hit Rate | Miss Rate | Avg Miss Latency (ticks) |\n")
    report.append("|------|------|--------|----------|-----------|------------------------|\n")
    
    for vlen in sorted_vlens:
        data = results[vlen]
        hits = data.get('l1_demand_hits', 0)
        misses = data.get('l1_demand_misses', 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0
        miss_rate = data.get('l1_miss_rate', 0) * 100
        miss_latency = data.get('l1_avg_miss_latency', 0)
        
        report.append(f"| {vlen} | {hits} | {misses} | {hit_rate:.2f}% | {miss_rate:.4f}% | {miss_latency:.0f} |\n")
    report.append("\n")
    
    # Observations
    report.append("## Observations\n\n")
    
    # Find trends
    min_sim_time_vlen = min(sorted_vlens, key=lambda v: results[v]['simSeconds'])
    max_sim_time_vlen = max(sorted_vlens, key=lambda v: results[v]['simSeconds'])
    
    min_miss_rate_vlen = min(sorted_vlens, key=lambda v: results[v].get('l1_miss_rate', 0))
    max_miss_rate_vlen = max(sorted_vlens, key=lambda v: results[v].get('l1_miss_rate', 0))
    
    report.append(f"- **Fastest simulation**: VLEN {min_sim_time_vlen} with {results[min_sim_time_vlen]['simSeconds']:.6e} seconds\n")
    report.append(f"- **Slowest simulation**: VLEN {max_sim_time_vlen} with {results[max_sim_time_vlen]['simSeconds']:.6e} seconds\n")
    report.append(f"- **Best L1 cache hit rate**: VLEN {min_miss_rate_vlen} with {(1-results[min_miss_rate_vlen].get('l1_miss_rate', 0))*100:.2f}% hit rate\n")
    report.append(f"- **Worst L1 cache hit rate**: VLEN {max_miss_rate_vlen} with {(1-results[max_miss_rate_vlen].get('l1_miss_rate', 0))*100:.2f}% hit rate\n")
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
