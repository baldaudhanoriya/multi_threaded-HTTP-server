#!/usr/bin/env python3
"""
Workload Comparison Script
Generates comparative analysis across all workload types
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import glob
import re

def extract_metrics_from_summary(summary_file):
    """Extract key metrics from summary.txt file"""
    metrics = {}
    
    try:
        with open(summary_file, 'r') as f:
            content = f.read()
            
            # Extract workload name from path
            workload_match = re.search(r'results_(\w+)_\d+', summary_file)
            if workload_match:
                metrics['workload'] = workload_match.group(1)
            
            # Find highest load section (typically last section)
            sections = content.split('LOAD LEVEL:')
            if len(sections) > 1:
                last_section = sections[-1]
                
                # Extract metrics from the highest load level
                match = re.search(r'Throughput:\s+([\d.]+)\s+req/s', last_section)
                if match:
                    metrics['throughput'] = float(match.group(1))
                
                match = re.search(r'Avg Response Time:\s+([\d.]+)\s+ms', last_section)
                if match:
                    metrics['avg_response_time'] = float(match.group(1))
                
                match = re.search(r'P95 Response Time:\s+([\d.]+)\s+ms', last_section)
                if match:
                    metrics['p95_response_time'] = float(match.group(1))
                
                match = re.search(r'Server CPU \(avg\):\s+([\d.]+)%', last_section)
                if match:
                    metrics['server_cpu'] = float(match.group(1))
                
                match = re.search(r'MySQL CPU \(avg\):\s+([\d.]+)%', last_section)
                if match:
                    metrics['mysql_cpu'] = float(match.group(1))
                
                match = re.search(r'System CPU \(avg\):\s+([\d.]+)%', last_section)
                if match:
                    metrics['system_cpu'] = float(match.group(1))
                
                match = re.search(r'Disk Write \(avg\):\s+([\d.]+)\s+KB/s', last_section)
                if match:
                    metrics['disk_write'] = float(match.group(1))
                
                match = re.search(r'Disk Read \(avg\):\s+([\d.]+)\s+KB/s', last_section)
                if match:
                    metrics['disk_read'] = float(match.group(1))
    
    except Exception as e:
        print(f"Warning: Error parsing {summary_file}: {e}")
    
    return metrics

def generate_comparison(master_dir):
    """Generate comparative analysis across all workloads"""
    
    # Find all summary files
    summary_files = glob.glob(os.path.join(master_dir, 'results_*/summary.txt'))
    
    if not summary_files:
        print(f"Error: No summary.txt files found in {master_dir}")
        return
    
    print(f"Found {len(summary_files)} workload results")
    
    # Extract metrics from all workloads
    data = []
    for summary_file in summary_files:
        metrics = extract_metrics_from_summary(summary_file)
        if metrics and 'workload' in metrics:
            data.append(metrics)
            print(f"  ✓ {metrics['workload']}")
    
    if not data:
        print("Error: No valid metrics extracted")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Sort by workload name for consistent display
    workload_order = ['get_all', 'put_all', 'get_popular', 'mixed', 
                      'compute_prime', 'compute_hash', 'compute_mixed']
    df['workload_cat'] = pd.Categorical(df['workload'], categories=workload_order, ordered=True)
    df = df.sort_values('workload_cat')
    
    # Create comprehensive comparison plot
    fig = plt.figure(figsize=(20, 12))
    
    workloads = df['workload'].tolist()
    x_pos = np.arange(len(workloads))
    
    # Color scheme
    colors = {
        'get_all': '#2E86AB',
        'put_all': '#A23B72',
        'get_popular': '#F18F01',
        'mixed': '#06A77D',
        'compute_prime': '#D62246',
        'compute_hash': '#8B4789',
        'compute_mixed': '#C73E1D'
    }
    bar_colors = [colors.get(w, '#666666') for w in workloads]
    
    # 1. Throughput Comparison
    ax1 = plt.subplot(2, 3, 1)
    bars = ax1.bar(x_pos, df['throughput'], color=bar_colors, alpha=0.8, edgecolor='black')
    ax1.set_xlabel('Workload Type', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Throughput (req/s)', fontsize=12, fontweight='bold')
    ax1.set_title('Throughput Comparison (Max Load)', fontsize=14, fontweight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(workloads, rotation=45, ha='right')
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, df['throughput'])):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                f'{val:.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 2. Response Time Comparison
    ax2 = plt.subplot(2, 3, 2)
    bars = ax2.bar(x_pos, df['avg_response_time'], color=bar_colors, alpha=0.8, edgecolor='black')
    ax2.set_xlabel('Workload Type', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Avg Response Time (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('Response Time Comparison (Max Load)', fontsize=14, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(workloads, rotation=45, ha='right')
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    
    # 3. CPU Utilization Comparison
    ax3 = plt.subplot(2, 3, 3)
    width = 0.25
    x_pos_cpu = np.arange(len(workloads))
    
    if 'server_cpu' in df.columns:
        ax3.bar(x_pos_cpu - width, df['server_cpu'], width, label='Server CPU', 
                color='#2E86AB', alpha=0.8, edgecolor='black')
    if 'mysql_cpu' in df.columns:
        ax3.bar(x_pos_cpu, df['mysql_cpu'], width, label='MySQL CPU',
                color='#A23B72', alpha=0.8, edgecolor='black')
    if 'system_cpu' in df.columns:
        ax3.bar(x_pos_cpu + width, df['system_cpu'], width, label='System CPU',
                color='#F18F01', alpha=0.8, edgecolor='black')
    
    ax3.axhline(y=80, color='red', linestyle='--', alpha=0.5, linewidth=2, label='80% threshold')
    ax3.set_xlabel('Workload Type', fontsize=12, fontweight='bold')
    ax3.set_ylabel('CPU Usage (%)', fontsize=12, fontweight='bold')
    ax3.set_title('CPU Utilization Comparison', fontsize=14, fontweight='bold')
    ax3.set_xticks(x_pos_cpu)
    ax3.set_xticklabels(workloads, rotation=45, ha='right')
    ax3.legend(loc='upper left', fontsize=9)
    ax3.grid(axis='y', alpha=0.3, linestyle='--')
    ax3.set_ylim([0, 110])
    
    # 4. Disk I/O Comparison
    ax4 = plt.subplot(2, 3, 4)
    width = 0.35
    
    if 'disk_read' in df.columns and 'disk_write' in df.columns:
        ax4.bar(x_pos - width/2, df['disk_read'], width, label='Disk Read',
                color='#06A77D', alpha=0.8, edgecolor='black')
        ax4.bar(x_pos + width/2, df['disk_write'], width, label='Disk Write',
                color='#D62246', alpha=0.8, edgecolor='black')
    
    ax4.set_xlabel('Workload Type', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Disk I/O (KB/s)', fontsize=12, fontweight='bold')
    ax4.set_title('Disk I/O Comparison', fontsize=14, fontweight='bold')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(workloads, rotation=45, ha='right')
    ax4.legend(loc='upper left', fontsize=9)
    ax4.grid(axis='y', alpha=0.3, linestyle='--')
    
    # 5. Throughput vs Server CPU Scatter
    ax5 = plt.subplot(2, 3, 5)
    if 'server_cpu' in df.columns:
        for i, row in df.iterrows():
            ax5.scatter(row['server_cpu'], row['throughput'], 
                       s=200, color=colors.get(row['workload'], '#666666'),
                       alpha=0.7, edgecolors='black', linewidth=2)
            ax5.annotate(row['workload'], (row['server_cpu'], row['throughput']),
                        fontsize=8, ha='center', va='bottom')
    
    ax5.set_xlabel('Server CPU Usage (%)', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Throughput (req/s)', fontsize=12, fontweight='bold')
    ax5.set_title('Throughput vs CPU (Bottleneck Analysis)', fontsize=14, fontweight='bold')
    ax5.grid(True, alpha=0.3, linestyle='--')
    
    # 6. Performance Efficiency (Throughput per CPU%)
    ax6 = plt.subplot(2, 3, 6)
    if 'server_cpu' in df.columns:
        efficiency = df['throughput'] / df['server_cpu'].replace(0, 1)
        bars = ax6.bar(x_pos, efficiency, color=bar_colors, alpha=0.8, edgecolor='black')
        ax6.set_xlabel('Workload Type', fontsize=12, fontweight='bold')
        ax6.set_ylabel('Efficiency (req/s per CPU%)', fontsize=12, fontweight='bold')
        ax6.set_title('Performance Efficiency', fontsize=14, fontweight='bold')
        ax6.set_xticks(x_pos)
        ax6.set_xticklabels(workloads, rotation=45, ha='right')
        ax6.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.suptitle('Multi-Workload Performance Analysis & Bottleneck Identification',
                 fontsize=18, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    # Save plot
    output_file = os.path.join(master_dir, 'workload_comparison.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Comparison plot saved: {output_file}")
    
    # Generate text analysis
    analysis_file = os.path.join(master_dir, 'bottleneck_analysis.txt')
    with open(analysis_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("MULTI-WORKLOAD BOTTLENECK ANALYSIS\n")
        f.write("="*80 + "\n\n")
        
        f.write("Performance Summary (at maximum load):\n")
        f.write("-"*80 + "\n")
        f.write(f"{'Workload':<18} {'Throughput':<15} {'Resp Time':<15} {'Server CPU':<15} {'Type':<15}\n")
        f.write("-"*80 + "\n")
        
        workload_types = {
            'get_all': 'Disk-bound',
            'put_all': 'Disk-bound',
            'get_popular': 'Cache-bound',
            'mixed': 'Mixed',
            'compute_prime': 'CPU-bound',
            'compute_hash': 'CPU-bound',
            'compute_mixed': 'CPU-bound'
        }
        
        for _, row in df.iterrows():
            wtype = workload_types.get(row['workload'], 'Unknown')
            cpu_str = f"{row['server_cpu']:.1f}%" if 'server_cpu' in row else "N/A"
            f.write(f"{row['workload']:<18} {row['throughput']:<15.2f} "
                   f"{row['avg_response_time']:<15.2f} {cpu_str:<15} {wtype:<15}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("BOTTLENECK IDENTIFICATION\n")
        f.write("="*80 + "\n\n")
        
        # Identify bottlenecks for each workload
        for _, row in df.iterrows():
            f.write(f"\n{row['workload'].upper()}:\n")
            
            bottlenecks = []
            if 'server_cpu' in row and row['server_cpu'] > 80:
                bottlenecks.append(f"  ⚠ Server CPU saturated ({row['server_cpu']:.1f}%)")
            if 'mysql_cpu' in row and row['mysql_cpu'] > 80:
                bottlenecks.append(f"  ⚠ MySQL CPU saturated ({row['mysql_cpu']:.1f}%)")
            if 'disk_write' in row and row['disk_write'] > 10000:
                bottlenecks.append(f"  ⚠ High disk write I/O ({row['disk_write']:.1f} KB/s)")
            if 'disk_read' in row and row['disk_read'] > 10000:
                bottlenecks.append(f"  ⚠ High disk read I/O ({row['disk_read']:.1f} KB/s)")
            
            if bottlenecks:
                for b in bottlenecks:
                    f.write(b + "\n")
            else:
                f.write("  ✓ No clear bottleneck (balanced resource usage)\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("PERFORMANCE INSIGHTS\n")
        f.write("="*80 + "\n\n")
        
        # Find best/worst performers
        max_throughput = df.loc[df['throughput'].idxmax()]
        min_response = df.loc[df['avg_response_time'].idxmin()]
        
        f.write(f"Best Throughput:    {max_throughput['workload']} ({max_throughput['throughput']:.2f} req/s)\n")
        f.write(f"Best Response Time: {min_response['workload']} ({min_response['avg_response_time']:.2f} ms)\n")
        
        if 'server_cpu' in df.columns:
            efficiency = df['throughput'] / df['server_cpu'].replace(0, 1)
            most_efficient = df.loc[efficiency.idxmax()]
            f.write(f"Most Efficient:     {most_efficient['workload']} ({efficiency.max():.2f} req/s per CPU%)\n")
        
        f.write("\n" + "="*80 + "\n")
    
    print(f"✓ Bottleneck analysis saved: {analysis_file}")
    
    # Print summary to console
    print("\n" + "="*80)
    print("WORKLOAD COMPARISON SUMMARY")
    print("="*80)
    print(f"\n{'Workload':<18} {'Throughput':<15} {'Resp Time':<12} {'Server CPU':<12} {'Bottleneck':<15}")
    print("-"*80)
    
    for _, row in df.iterrows():
        cpu_str = f"{row['server_cpu']:.1f}%" if 'server_cpu' in row else "N/A"
        
        # Identify primary bottleneck
        bottleneck = "None"
        if 'server_cpu' in row and row['server_cpu'] > 80:
            bottleneck = "CPU"
        elif 'disk_write' in row and row['disk_write'] > 10000:
            bottleneck = "Disk I/O"
        elif 'mysql_cpu' in row and row['mysql_cpu'] > 80:
            bottleneck = "MySQL"
        
        print(f"{row['workload']:<18} {row['throughput']:<15.2f} "
              f"{row['avg_response_time']:<12.2f} {cpu_str:<12} {bottleneck:<15}")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 compare_workloads.py <master_results_directory>")
        print("Example: python3 compare_workloads.py results_all_workloads_20241124_120000/")
        sys.exit(1)
    
    master_dir = sys.argv[1]
    
    if not os.path.isdir(master_dir):
        print(f"Error: Directory {master_dir} not found")
        sys.exit(1)
    
    generate_comparison(master_dir)
