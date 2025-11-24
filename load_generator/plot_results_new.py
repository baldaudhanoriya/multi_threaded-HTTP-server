#!/usr/bin/env python3
"""
Comprehensive Load Test Results Plotter
Generates combined graphs showing performance metrics and resource utilization
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import glob
import re

def parse_load_generator_output(log_file):
    """Extract metrics from load generator log file"""
    metrics = {
        'threads': 0,
        'throughput': 0,
        'avg_response_time': 0,
        'p50': 0,
        'p95': 0,
        'p99': 0,
        'success_rate': 0
    }
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
            
            # Extract number of threads from filename
            match = re.search(r'test_(\d+)threads\.log', log_file)
            if match:
                metrics['threads'] = int(match.group(1))
            
            # Extract throughput
            match = re.search(r'Average Throughput:\s+([\d.]+)\s+req/s', content)
            if match:
                metrics['throughput'] = float(match.group(1))
            
            # Extract average response time
            match = re.search(r'Average Response Time:\s+([\d.]+)\s+ms', content)
            if match:
                metrics['avg_response_time'] = float(match.group(1))
            
            # Extract percentiles
            match = re.search(r'P50:\s+([\d.]+)\s+ms', content)
            if match:
                metrics['p50'] = float(match.group(1))
            
            match = re.search(r'P95:\s+([\d.]+)\s+ms', content)
            if match:
                metrics['p95'] = float(match.group(1))
            
            match = re.search(r'P99:\s+([\d.]+)\s+ms', content)
            if match:
                metrics['p99'] = float(match.group(1))
            
            # Extract success rate
            match = re.search(r'Success Rate:\s+([\d.]+)%', content)
            if match:
                metrics['success_rate'] = float(match.group(1))
    
    except Exception as e:
        print(f"Warning: Error parsing {log_file}: {e}")
    
    return metrics

def parse_resource_csv(csv_file):
    """Parse resource monitoring CSV and calculate averages"""
    try:
        df = pd.read_csv(csv_file)
        
        # Calculate averages (skip first 5 seconds for warm-up)
        if len(df) > 5:
            df = df.iloc[5:]
        
        return {
            'server_cpu_avg': df['server_cpu'].mean(),
            'server_cpu_max': df['server_cpu'].max(),
            'mysql_cpu_avg': df['mysql_cpu'].mean(),
            'mysql_cpu_max': df['mysql_cpu'].max(),
            'system_cpu_used_avg': 100 - df['system_cpu_idle'].mean(),
            'system_cpu_used_max': 100 - df['system_cpu_idle'].min(),
            'server_mem_avg': df['server_mem_mb'].mean(),
            'mysql_mem_avg': df['mysql_mem_mb'].mean(),
            'disk_read_avg': df['disk_read_kb'].mean(),
            'disk_write_avg': df['disk_write_kb'].mean(),
            'disk_read_max': df['disk_read_kb'].max(),
            'disk_write_max': df['disk_write_kb'].max(),
        }
    except Exception as e:
        print(f"Warning: Error parsing {csv_file}: {e}")
        return None

def plot_combined_results(results_dir):
    """Generate comprehensive plots combining performance and resource metrics"""
    
    # Find all log and resource files
    log_files = sorted(glob.glob(os.path.join(results_dir, 'test_*threads.log')))
    
    if not log_files:
        print(f"Error: No test log files found in {results_dir}")
        return
    
    # Collect all data
    data = []
    for log_file in log_files:
        perf_metrics = parse_load_generator_output(log_file)
        
        # Find corresponding resource file
        threads = perf_metrics['threads']
        resource_file = os.path.join(results_dir, f'resources_{threads}threads.csv')
        
        if os.path.exists(resource_file):
            resource_metrics = parse_resource_csv(resource_file)
            if resource_metrics:
                data.append({**perf_metrics, **resource_metrics})
        else:
            print(f"Warning: Resource file not found for {threads} threads")
            data.append(perf_metrics)
    
    if not data:
        print("Error: No data collected")
        return
    
    # Convert to DataFrame and sort by threads
    df = pd.DataFrame(data)
    df = df.sort_values('threads')
    
    print(f"\nCollected data for {len(df)} load levels: {df['threads'].tolist()}")
    
    # Create comprehensive plot with 6 subplots
    fig = plt.figure(figsize=(18, 12))
    
    # Define color scheme
    colors = {
        'throughput': '#2E86AB',
        'response_time': '#A23B72',
        'server': '#2E86AB',
        'mysql': '#A23B72',
        'system': '#F18F01',
        'disk_read': '#06A77D',
        'disk_write': '#D62246'
    }
    
    # 1. Throughput vs Load
    ax1 = plt.subplot(2, 3, 1)
    ax1.plot(df['threads'], df['throughput'], marker='o', linewidth=2, 
             markersize=8, color=colors['throughput'], label='Throughput')
    ax1.set_xlabel('Number of Threads (Load)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Throughput (req/s)', fontsize=11, fontweight='bold')
    ax1.set_title('Throughput vs Load', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xticks(df['threads'])
    
    # 2. Response Time vs Load
    ax2 = plt.subplot(2, 3, 2)
    ax2.plot(df['threads'], df['avg_response_time'], marker='o', linewidth=2,
             markersize=8, color=colors['response_time'], label='Avg Response Time')
    ax2.plot(df['threads'], df['p95'], marker='s', linewidth=1.5, linestyle='--',
             markersize=6, color='orange', label='P95', alpha=0.7)
    ax2.set_xlabel('Number of Threads (Load)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Response Time (ms)', fontsize=11, fontweight='bold')
    ax2.set_title('Response Time vs Load', fontsize=13, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xticks(df['threads'])
    
    # 3. CPU Utilization vs Load
    ax3 = plt.subplot(2, 3, 3)
    if 'server_cpu_avg' in df.columns:
        ax3.plot(df['threads'], df['server_cpu_avg'], marker='o', linewidth=2,
                 markersize=8, color=colors['server'], label='Server CPU')
        ax3.plot(df['threads'], df['mysql_cpu_avg'], marker='s', linewidth=2,
                 markersize=8, color=colors['mysql'], label='MySQL CPU')
        ax3.plot(df['threads'], df['system_cpu_used_avg'], marker='^', linewidth=1.5,
                 markersize=7, color=colors['system'], label='System CPU', linestyle='--')
        ax3.axhline(y=100, color='red', linestyle=':', alpha=0.5, linewidth=1)
        ax3.set_ylim([0, 110])
    ax3.set_xlabel('Number of Threads (Load)', fontsize=11, fontweight='bold')
    ax3.set_ylabel('CPU Usage (%)', fontsize=11, fontweight='bold')
    ax3.set_title('CPU Utilization vs Load', fontsize=13, fontweight='bold')
    ax3.legend(loc='best', fontsize=9)
    ax3.grid(True, alpha=0.3, linestyle='--')
    ax3.set_xticks(df['threads'])
    
    # 4. Throughput + Server CPU (Dual Y-axis)
    ax4 = plt.subplot(2, 3, 4)
    ax4_twin = ax4.twinx()
    
    line1 = ax4.plot(df['threads'], df['throughput'], marker='o', linewidth=2.5,
                     markersize=8, color=colors['throughput'], label='Throughput')
    ax4.set_xlabel('Number of Threads (Load)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Throughput (req/s)', fontsize=11, fontweight='bold', color=colors['throughput'])
    ax4.tick_params(axis='y', labelcolor=colors['throughput'])
    
    if 'server_cpu_avg' in df.columns:
        line2 = ax4_twin.plot(df['threads'], df['server_cpu_avg'], marker='s', linewidth=2.5,
                              markersize=8, color='red', label='Server CPU', linestyle='--')
        ax4_twin.set_ylabel('Server CPU Usage (%)', fontsize=11, fontweight='bold', color='red')
        ax4_twin.tick_params(axis='y', labelcolor='red')
        ax4_twin.set_ylim([0, 110])
        
        # Combine legends
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax4.legend(lines, labels, loc='best', fontsize=9)
    
    ax4.set_title('Throughput vs Server CPU', fontsize=13, fontweight='bold')
    ax4.grid(True, alpha=0.3, linestyle='--')
    ax4.set_xticks(df['threads'])
    
    # 5. Response Time + MySQL CPU (Dual Y-axis)
    ax5 = plt.subplot(2, 3, 5)
    ax5_twin = ax5.twinx()
    
    line1 = ax5.plot(df['threads'], df['avg_response_time'], marker='o', linewidth=2.5,
                     markersize=8, color=colors['response_time'], label='Avg Response Time')
    ax5.set_xlabel('Number of Threads (Load)', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Response Time (ms)', fontsize=11, fontweight='bold', color=colors['response_time'])
    ax5.tick_params(axis='y', labelcolor=colors['response_time'])
    
    if 'mysql_cpu_avg' in df.columns:
        line2 = ax5_twin.plot(df['threads'], df['mysql_cpu_avg'], marker='s', linewidth=2.5,
                              markersize=8, color='purple', label='MySQL CPU', linestyle='--')
        ax5_twin.set_ylabel('MySQL CPU Usage (%)', fontsize=11, fontweight='bold', color='purple')
        ax5_twin.tick_params(axis='y', labelcolor='purple')
        ax5_twin.set_ylim([0, 110])
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax5.legend(lines, labels, loc='best', fontsize=9)
    
    ax5.set_title('Response Time vs MySQL CPU', fontsize=13, fontweight='bold')
    ax5.grid(True, alpha=0.3, linestyle='--')
    ax5.set_xticks(df['threads'])
    
    # 6. Disk I/O vs Load
    ax6 = plt.subplot(2, 3, 6)
    if 'disk_read_avg' in df.columns:
        ax6.plot(df['threads'], df['disk_read_avg'], marker='o', linewidth=2,
                 markersize=8, color=colors['disk_read'], label='Disk Read')
        ax6.plot(df['threads'], df['disk_write_avg'], marker='s', linewidth=2,
                 markersize=8, color=colors['disk_write'], label='Disk Write')
    ax6.set_xlabel('Number of Threads (Load)', fontsize=11, fontweight='bold')
    ax6.set_ylabel('Disk I/O (KB/s)', fontsize=11, fontweight='bold')
    ax6.set_title('Disk I/O vs Load', fontsize=13, fontweight='bold')
    ax6.legend(loc='best', fontsize=9)
    ax6.grid(True, alpha=0.3, linestyle='--')
    ax6.set_xticks(df['threads'])
    
    plt.suptitle(f'Load Test Analysis: {os.path.basename(results_dir)}',
                 fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    # Save plot
    output_file = os.path.join(results_dir, 'combined_analysis.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Combined analysis plot saved: {output_file}")
    
    # Generate summary text file
    summary_file = os.path.join(results_dir, 'summary.txt')
    with open(summary_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("LOAD TEST SUMMARY\n")
        f.write("="*70 + "\n\n")
        
        for _, row in df.iterrows():
            f.write(f"\n{'='*70}\n")
            f.write(f"LOAD LEVEL: {int(row['threads'])} threads\n")
            f.write(f"{'='*70}\n")
            
            f.write(f"\nPerformance Metrics:\n")
            f.write(f"  Throughput:         {row['throughput']:.2f} req/s\n")
            f.write(f"  Avg Response Time:  {row['avg_response_time']:.2f} ms\n")
            f.write(f"  P50 Response Time:  {row['p50']:.2f} ms\n")
            f.write(f"  P95 Response Time:  {row['p95']:.2f} ms\n")
            f.write(f"  P99 Response Time:  {row['p99']:.2f} ms\n")
            f.write(f"  Success Rate:       {row['success_rate']:.2f}%\n")
            
            if 'server_cpu_avg' in row:
                f.write(f"\nResource Utilization:\n")
                f.write(f"  Server CPU (avg):   {row['server_cpu_avg']:.2f}%\n")
                f.write(f"  Server CPU (max):   {row['server_cpu_max']:.2f}%\n")
                f.write(f"  MySQL CPU (avg):    {row['mysql_cpu_avg']:.2f}%\n")
                f.write(f"  MySQL CPU (max):    {row['mysql_cpu_max']:.2f}%\n")
                f.write(f"  System CPU (avg):   {row['system_cpu_used_avg']:.2f}%\n")
                f.write(f"  Server Memory:      {row['server_mem_avg']:.2f} MB\n")
                f.write(f"  MySQL Memory:       {row['mysql_mem_avg']:.2f} MB\n")
                f.write(f"  Disk Read (avg):    {row['disk_read_avg']:.2f} KB/s\n")
                f.write(f"  Disk Write (avg):   {row['disk_write_avg']:.2f} KB/s\n")
        
        # Bottleneck analysis
        f.write(f"\n{'='*70}\n")
        f.write("BOTTLENECK ANALYSIS\n")
        f.write(f"{'='*70}\n\n")
        
        # Find highest load level
        max_load_row = df.iloc[-1]
        
        if 'server_cpu_avg' in max_load_row:
            bottlenecks = []
            if max_load_row['server_cpu_avg'] > 80:
                bottlenecks.append(f"Server CPU ({max_load_row['server_cpu_avg']:.1f}% avg)")
            if max_load_row['mysql_cpu_avg'] > 80:
                bottlenecks.append(f"MySQL CPU ({max_load_row['mysql_cpu_avg']:.1f}% avg)")
            if max_load_row['disk_write_avg'] > 10000:
                bottlenecks.append(f"Disk Write I/O ({max_load_row['disk_write_avg']:.1f} KB/s)")
            
            if bottlenecks:
                f.write("⚠ Identified Bottlenecks (at highest load):\n")
                for b in bottlenecks:
                    f.write(f"  - {b}\n")
            else:
                f.write("✓ No clear bottlenecks detected (all resources <80% utilization)\n")
        
        f.write("\n" + "="*70 + "\n")
    
    print(f"✓ Summary text file saved: {summary_file}")
    
    # Print summary to console
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)
    print(f"\n{'Threads':<10} {'Throughput':<15} {'Avg RT (ms)':<15} {'Server CPU':<15} {'MySQL CPU':<15}")
    print("-" * 70)
    for _, row in df.iterrows():
        server_cpu = f"{row['server_cpu_avg']:.1f}%" if 'server_cpu_avg' in row else "N/A"
        mysql_cpu = f"{row['mysql_cpu_avg']:.1f}%" if 'mysql_cpu_avg' in row else "N/A"
        print(f"{int(row['threads']):<10} {row['throughput']:<15.2f} {row['avg_response_time']:<15.2f} {server_cpu:<15} {mysql_cpu:<15}")
    print("="*70 + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 plot_results.py <results_directory>")
        print("Example: python3 plot_results.py results_get_all_20241124_120000/")
        sys.exit(1)
    
    results_dir = sys.argv[1]
    
    if not os.path.isdir(results_dir):
        print(f"Error: Directory {results_dir} not found")
        sys.exit(1)
    
    plot_combined_results(results_dir)
