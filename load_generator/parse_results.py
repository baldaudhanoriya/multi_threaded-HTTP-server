#!/usr/bin/env python3

"""
Parse load test results and generate summary
Usage: python3 parse_results.py <results_directory>
"""

import sys
import os
import re
from pathlib import Path

def parse_log_file(filepath):
    """Extract metrics from a log file"""
    metrics = {
        'threads': None,
        'duration': None,
        'total_requests': None,
        'successful_requests': None,
        'failed_requests': None,
        'success_rate': None,
        'throughput': None,
        'avg_response_time': None,
        'p50': None,
        'p95': None,
        'p99': None
    }
    
    with open(filepath, 'r') as f:
        content = f.read()
        
        # Extract threads from filename
        match = re.search(r'test_(\d+)threads', str(filepath))
        if match:
            metrics['threads'] = int(match.group(1))
        
        # Parse metrics
        patterns = {
            'duration': r'Actual Duration:\s+(\d+\.?\d*)',
            'total_requests': r'Total Requests:\s+(\d+)',
            'successful_requests': r'Successful Requests:\s+(\d+)',
            'failed_requests': r'Failed Requests:\s+(\d+)',
            'success_rate': r'Success Rate:\s+(\d+\.?\d*)%',
            'throughput': r'Average Throughput:\s+(\d+\.?\d*)',
            'avg_response_time': r'Average Response Time:\s+(\d+\.?\d*)',
            'p50': r'P50 \(median\):\s+(\d+\.?\d*)',
            'p95': r'P95:\s+(\d+\.?\d*)',
            'p99': r'P99:\s+(\d+\.?\d*)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1)
                if key == 'threads':
                    metrics[key] = int(value)
                elif key in ['total_requests', 'successful_requests', 'failed_requests']:
                    metrics[key] = int(value)
                else:
                    metrics[key] = float(value)
    
    return metrics

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 parse_results.py <results_directory>")
        sys.exit(1)
    
    results_dir = Path(sys.argv[1])
    
    if not results_dir.exists() or not results_dir.is_dir():
        print(f"Error: Directory '{results_dir}' does not exist")
        sys.exit(1)
    
    # Find all log files
    log_files = sorted(results_dir.glob("test_*threads.log"))
    
    if not log_files:
        print(f"No log files found in {results_dir}")
        sys.exit(1)
    
    print("=" * 80)
    print(f"Load Test Results Summary - {results_dir.name}")
    print("=" * 80)
    print()
    
    # Parse all files
    results = []
    for log_file in log_files:
        metrics = parse_log_file(log_file)
        if metrics['threads'] is not None:
            results.append(metrics)
    
    # Sort by number of threads
    results.sort(key=lambda x: x['threads'] or 0)
    
    # Print table header
    print(f"{'Threads':<10} {'Throughput':<15} {'Avg RT (ms)':<15} {'P95 (ms)':<12} {'P99 (ms)':<12} {'Success %':<12}")
    print("-" * 80)
    
    # Print results
    for r in results:
        threads = r['threads'] or 'N/A'
        throughput = f"{r['throughput']:.2f}" if r['throughput'] else 'N/A'
        avg_rt = f"{r['avg_response_time']:.2f}" if r['avg_response_time'] else 'N/A'
        p95 = f"{r['p95']:.2f}" if r['p95'] else 'N/A'
        p99 = f"{r['p99']:.2f}" if r['p99'] else 'N/A'
        success = f"{r['success_rate']:.2f}" if r['success_rate'] else 'N/A'
        
        print(f"{threads:<10} {throughput:<15} {avg_rt:<15} {p95:<12} {p99:<12} {success:<12}")
    
    print()
    print("=" * 80)
    
    # Generate CSV for plotting
    csv_file = results_dir / "summary.csv"
    with open(csv_file, 'w') as f:
        f.write("threads,throughput,avg_response_time,p50,p95,p99,success_rate\n")
        for r in results:
            f.write(f"{r['threads']},{r['throughput']},{r['avg_response_time']},")
            f.write(f"{r['p50']},{r['p95']},{r['p99']},{r['success_rate']}\n")
    
    print(f"CSV file generated: {csv_file}")
    print()
    print("To plot results, use the CSV file with your plotting tool (Excel, Python, R, etc.)")
    print()
    
    # Print analysis
    print("Quick Analysis:")
    print("-" * 80)
    
    if len(results) >= 2:
        max_throughput = max(r['throughput'] for r in results if r['throughput'])
        max_throughput_threads = next(r['threads'] for r in results if r['throughput'] == max_throughput)
        
        print(f"Maximum throughput: {max_throughput:.2f} req/s at {max_throughput_threads} threads")
        
        # Check if throughput is plateauing
        if len(results) >= 3:
            last_three = [r['throughput'] for r in results[-3:] if r['throughput']]
            if len(last_three) == 3:
                variation = (max(last_three) - min(last_three)) / max(last_three) * 100
                if variation < 10:
                    print(f"Throughput appears to be plateauing (variation < 10%)")
                    print(f"Estimated capacity: ~{max_throughput:.2f} req/s")
        
        # Check response time trend
        first_rt = next((r['avg_response_time'] for r in results if r['avg_response_time']), None)
        last_rt = next((r['avg_response_time'] for r in reversed(results) if r['avg_response_time']), None)
        
        if first_rt and last_rt:
            rt_increase = ((last_rt - first_rt) / first_rt) * 100
            print(f"Response time increased by {rt_increase:.1f}% from lowest to highest load")
            
            if rt_increase > 100:
                print("⚠ Significant response time degradation detected - server may be saturated")
    
    print()

if __name__ == "__main__":
    main()
