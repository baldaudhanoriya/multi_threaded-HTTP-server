#!/bin/bash

# Run load test experiments across multiple load levels
# Usage: ./run_experiments.sh <workload_type> <server_host> <server_port>

WORKLOAD=${1:-"get_all"}
SERVER_HOST=${2:-"127.0.0.1"}
SERVER_PORT=${3:-8080}
DURATION=60  # 5 minutes per test

# Load levels to test
LOAD_LEVELS=(1 5 10 20 40)

echo "=========================================="
echo "Running Load Test Experiments"
echo "=========================================="
echo "Workload:    $WORKLOAD"
echo "Server:      $SERVER_HOST:$SERVER_PORT"
echo "Duration:    $DURATION seconds per test"
echo "Load levels: ${LOAD_LEVELS[@]}"
echo "=========================================="
echo ""

# Create results directory
RESULTS_DIR="results_${WORKLOAD}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "Results will be saved to: $RESULTS_DIR"
echo ""

# Get MySQL and Server PIDs for monitoring
MYSQL_PID=$(pgrep -f mysqld | head -1)
if [ -z "$MYSQL_PID" ]; then
    echo "Warning: MySQL process not found. Using PID 0."
    MYSQL_PID=0
fi

SERVER_PID=$(pgrep -f kv-server | head -1)
if [ -z "$SERVER_PID" ]; then
    echo "Error: Server (kv-server) not found. Please start the server first."
    exit 1
fi

echo "Server PID: $SERVER_PID"
echo "MySQL PID: $MYSQL_PID"
echo ""

# Run experiments at each load level
for THREADS in "${LOAD_LEVELS[@]}"; do
    echo "=========================================="
    echo "Running test: $THREADS threads"
    echo "=========================================="
    
    OUTPUT_FILE="$RESULTS_DIR/test_${THREADS}threads.log"
    RESOURCE_FILE="$RESULTS_DIR/resources_${THREADS}threads.csv"
    
    # Start resource monitoring in background
    echo "Starting resource monitoring..."
    ./monitor_resources.sh $SERVER_PID $MYSQL_PID "$RESOURCE_FILE" &
    MONITOR_PID=$!
    
    sleep 2  # Give monitor time to start
    
    # Run load generator and save output
    taskset -c 9-11 ./load-generator -h "$SERVER_HOST" -p "$SERVER_PORT" \
        -t "$THREADS" -d "$DURATION" -w "$WORKLOAD" | tee "$OUTPUT_FILE"
    
    # Stop resource monitoring
    echo ""
    echo "Stopping resource monitoring..."
    kill $MONITOR_PID 2>/dev/null
    wait $MONITOR_PID 2>/dev/null
    
    echo ""
    echo "Results saved to: $OUTPUT_FILE"
    echo "Resources saved to: $RESOURCE_FILE"
    echo ""
    
    # Wait a bit between tests to let server recover
    echo "Waiting 10 seconds before next test..."
    sleep 10
    echo ""
done

echo "=========================================="
echo "All experiments completed!"
echo "=========================================="
echo "Results directory: $RESULTS_DIR"
echo ""
echo "Analyzing results and generating plots..."
python3 plot_results.py "$RESULTS_DIR"
echo ""
echo "Done! Check $RESULTS_DIR for:"
echo "  - performance_vs_load.png (throughput & response time)"
echo "  - resource_utilization.png (CPU, memory, disk I/O)"
echo "  - combined_analysis.png (performance + resources)"
echo "  - summary.txt (detailed metrics)"
