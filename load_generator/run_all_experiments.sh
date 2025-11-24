#!/bin/bash

# Run all workload experiments and generate comprehensive analysis
# This script runs experiments for all 7 workload types to identify different bottlenecks

SERVER_HOST=${1:-"127.0.0.1"}
SERVER_PORT=${2:-8080}
DURATION=60  # 60 seconds per test for stable results

# All workload types
WORKLOADS=(
       # Disk-bound (DB reads, cache misses)
            # Disk-bound (DB writes)
    "get_popular"       # CPU/Memory-bound (cache hits)
    "mixed"             # Mixed KV operations
    "compute_prime"     # CPU-bound (prime computation)
    "compute_hash"      # CPU-bound (hash computation)
    "compute_mixed"     # CPU-bound (mixed compute)
)

WORKLOAD_DESCRIPTIONS=(
    "Disk-bound (DB reads, cache misses)"
    "Disk-bound (DB writes)"
    "CPU/Memory-bound (cache hits)"
    "Mixed KV operations"
    "CPU-bound (prime computation)"
    "CPU-bound (hash computation)"
    "CPU-bound (mixed compute)"
)

echo "=========================================="
echo "  COMPREHENSIVE LOAD TEST SUITE"
echo "=========================================="
echo "Server:      $SERVER_HOST:$SERVER_PORT"
echo "Duration:    $DURATION seconds per test"
echo "Workloads:   ${#WORKLOADS[@]} workload types"
echo "=========================================="
echo ""

# Check if server is running
if ! curl -s http://$SERVER_HOST:$SERVER_PORT/status > /dev/null 2>&1; then
    echo "Error: Server is not responding at http://$SERVER_HOST:$SERVER_PORT"
    echo "Please start the server first with: ./run_server.sh"
    exit 1
fi

echo "✓ Server is running"
echo ""

# Create master results directory
MASTER_DIR="results_all_workloads_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$MASTER_DIR"

echo "Results directory: $MASTER_DIR"
echo ""
echo "=========================================="
echo "Starting experiments..."
echo "=========================================="
echo ""

# Counter for progress
TOTAL=${#WORKLOADS[@]}
CURRENT=0

# Run experiments for each workload
for i in "${!WORKLOADS[@]}"; do
    WORKLOAD="${WORKLOADS[$i]}"
    DESCRIPTION="${WORKLOAD_DESCRIPTIONS[$i]}"
    CURRENT=$((CURRENT + 1))
    
    echo ""
    echo "=========================================="
    echo "[$CURRENT/$TOTAL] Workload: $WORKLOAD"
    echo "Description: $DESCRIPTION"
    echo "=========================================="
    echo ""
    
    # Run experiment for this workload
    ./run_experiments.sh "$WORKLOAD" "$SERVER_HOST" "$SERVER_PORT"
    
    # Find the most recent results directory for this workload
    WORKLOAD_DIR=$(ls -td results_${WORKLOAD}_* 2>/dev/null | head -1)
    
    if [ -n "$WORKLOAD_DIR" ] && [ -d "$WORKLOAD_DIR" ]; then
        echo ""
        echo "Generating graphs for $WORKLOAD..."
        python3 plot_results_new.py "$WORKLOAD_DIR"
        
        # Copy results to master directory
        cp -r "$WORKLOAD_DIR" "$MASTER_DIR/"
        
        echo "✓ $WORKLOAD completed"
    else
        echo "⚠ Warning: Results directory not found for $WORKLOAD"
    fi
    
    # Wait between workloads to let system stabilize
    if [ $CURRENT -lt $TOTAL ]; then
        echo ""
        echo "Waiting 30 seconds before next workload..."
        sleep 30
    fi
done

echo ""
echo "=========================================="
echo "  ALL EXPERIMENTS COMPLETED!"
echo "=========================================="
echo ""
echo "Results location: $MASTER_DIR"
echo ""

# Generate comparative analysis
echo "Generating comparative analysis across all workloads..."
python3 compare_workloads.py "$MASTER_DIR"

echo ""
echo "=========================================="
echo "  SUMMARY"
echo "=========================================="
echo ""
echo "Master results directory: $MASTER_DIR"
echo ""
echo "Individual workload results:"
for i in "${!WORKLOADS[@]}"; do
    WORKLOAD="${WORKLOADS[$i]}"
    DESCRIPTION="${WORKLOAD_DESCRIPTIONS[$i]}"
    echo "  [$((i+1))] $WORKLOAD - $DESCRIPTION"
    echo "      → $MASTER_DIR/results_${WORKLOAD}_*/"
done
echo ""
echo "Comparative analysis:"
echo "  → $MASTER_DIR/workload_comparison.png"
echo "  → $MASTER_DIR/bottleneck_analysis.txt"
echo ""
echo "=========================================="
echo ""
echo "To view results:"
echo "  cd $MASTER_DIR"
echo "  ls -lh"
echo ""
echo "Done! 🎉"
