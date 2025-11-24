#!/usr/bin/env python3

"""
Plot load test results from CSV file
Usage: python3 plot_results.py <summary.csv>
Requires: matplotlib, pandas
Install: pip install matplotlib pandas
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def plot_results(csv_file):
    """Generate throughput and response time plots"""
    
    # Read data
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    # Check required columns
    required_cols = ['threads', 'throughput', 'avg_response_time']
    if not all(col in df.columns for col in required_cols):
        print(f"Error: CSV must contain columns: {required_cols}")
        sys.exit(1)
    
    # Sort by threads
    df = df.sort_values('threads')
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Throughput vs Load Level
    ax1.plot(df['threads'], df['throughput'], 'b-o', linewidth=2, markersize=8)
    ax1.set_xlabel('Number of Client Threads (Load Level)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Throughput (requests/sec)', fontsize=12, fontweight='bold')
    ax1.set_title('Throughput vs Load Level', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(left=0)
    ax1.set_ylim(bottom=0)
    
    # Annotate data points
    for i, row in df.iterrows():
        ax1.annotate(f"{row['throughput']:.1f}", 
                    (row['threads'], row['throughput']),
                    textcoords="offset points", 
                    xytext=(0,10), 
                    ha='center',
                    fontsize=9)
    
    # Plot 2: Response Time vs Load Level
    ax2.plot(df['threads'], df['avg_response_time'], 'r-o', linewidth=2, markersize=8, label='Average')
    
    # Also plot percentiles if available
    if 'p95' in df.columns:
        ax2.plot(df['threads'], df['p95'], 'g--s', linewidth=1.5, markersize=6, label='P95')
    if 'p99' in df.columns:
        ax2.plot(df['threads'], df['p99'], 'm--^', linewidth=1.5, markersize=6, label='P99')
    
    ax2.set_xlabel('Number of Client Threads (Load Level)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Response Time (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('Response Time vs Load Level', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='best')
    ax2.set_xlim(left=0)
    ax2.set_ylim(bottom=0)
    
    # Annotate average response time data points
    for i, row in df.iterrows():
        ax2.annotate(f"{row['avg_response_time']:.1f}", 
                    (row['threads'], row['avg_response_time']),
                    textcoords="offset points", 
                    xytext=(0,-15), 
                    ha='center',
                    fontsize=9)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    output_dir = Path(csv_file).parent
    output_file = output_dir / f"load_test_results_{Path(csv_file).stem}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_file}")
    
    # Show plot
    plt.show()
    
    # Additional plot: Combined view showing saturation
    fig2, ax = plt.subplots(figsize=(10, 6))
    
    # Normalize values to show on same scale
    max_throughput = df['throughput'].max()
    max_response_time = df['avg_response_time'].max()
    
    norm_throughput = df['throughput'] / max_throughput * 100
    norm_response_time = df['avg_response_time'] / max_response_time * 100
    
    ax.plot(df['threads'], norm_throughput, 'b-o', linewidth=2, markersize=8, label='Throughput (normalized)')
    ax.plot(df['threads'], norm_response_time, 'r-o', linewidth=2, markersize=8, label='Response Time (normalized)')
    
    ax.set_xlabel('Number of Client Threads (Load Level)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Normalized Value (%)', fontsize=12, fontweight='bold')
    ax.set_title('Normalized Throughput and Response Time vs Load', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    ax.set_xlim(left=0)
    ax.set_ylim(0, 110)
    
    # Add shaded region to show saturation point
    if len(df) >= 3:
        # Find where throughput stops increasing significantly
        throughput_deltas = df['throughput'].diff()
        if throughput_deltas.iloc[-1] < throughput_deltas.iloc[1] * 0.1:
            saturation_point = df.iloc[-2]['threads']
            ax.axvline(x=saturation_point, color='gray', linestyle='--', alpha=0.5, label='Approx. Saturation')
            ax.legend(loc='best')
    
    plt.tight_layout()
    
    output_file2 = output_dir / f"normalized_view_{Path(csv_file).stem}.png"
    plt.savefig(output_file2, dpi=300, bbox_inches='tight')
    print(f"Normalized plot saved to: {output_file2}")
    
    plt.show()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 plot_results.py <summary.csv>")
        print("Example: python3 plot_results.py results_get_all_20241124/summary.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not Path(csv_file).exists():
        print(f"Error: File '{csv_file}' does not exist")
        sys.exit(1)
    
    print("Generating plots...")
    plot_results(csv_file)
    print("Done!")

if __name__ == "__main__":
    main()
