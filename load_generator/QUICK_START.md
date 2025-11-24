# Quick Start Guide - Load Testing

## Step 1: Build Everything

```bash
cd multi_threaded-HTTP-server
chmod +x build.sh
./build.sh
```

## Step 2: Setup Database

```bash
# Start MySQL
sudo service mysql start

# Create database (update password if needed)
mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS kvstore_db;
USE kvstore_db;

CREATE TABLE IF NOT EXISTS kv_pairs (
    kv_key VARCHAR(255) PRIMARY KEY,
    kv_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hash_store (
    text_prefix VARCHAR(255) NOT NULL,
    text_hash VARCHAR(64) NOT NULL,
    text TEXT NOT NULL,
    hash_value INT UNSIGNED NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (text_prefix, text_hash),
    INDEX idx_text_hash (text_hash)
);
EOF
```

## Step 3: Start Server

```bash
# Terminal 1 (or Machine 1)
cd multi_threaded-HTTP-server/build
./kv-server
```

## Step 4: Test Connection

```bash
# Quick test
curl "http://localhost:8080/kv/create?key=test&value=hello"
curl "http://localhost:8080/kv/read?key=test"
curl "http://localhost:8080/status"
```

## Step 5: Run Single Load Test

```bash
# Terminal 2 (or Machine 2)
cd multi_threaded-HTTP-server

# Test with 10 threads for 60 seconds, get_all workload
./load-generator -h 127.0.0.1 -p 8080 -t 10 -d 60 -w get_all
```

## Step 6: Run Full Experiment Suite

```bash
# Make scripts executable
chmod +x run_experiments.sh monitor_resources.sh

# Run experiments for a workload
./run_experiments.sh get_all 127.0.0.1 8080

# While running, monitor resources (in another terminal on server machine)
./monitor_resources.sh
```

## Step 7: Analyze Results

```bash
# Parse results and generate summary
python3 parse_results.py results_get_all_*/

# Generate plots (requires matplotlib, pandas)
pip install matplotlib pandas
python3 plot_results.py results_get_all_*/summary.csv
```

## Step 8: Run Different Workloads

```bash
# Get All (disk-bound, cache misses)
./run_experiments.sh get_all 127.0.0.1 8080

# Put All (disk-bound, writes)
./run_experiments.sh put_all 127.0.0.1 8080

# Get Popular (CPU/memory-bound, cache hits)
./run_experiments.sh get_popular 127.0.0.1 8080

# Mixed workload
./run_experiments.sh mixed 127.0.0.1 8080
```

## Two-Machine Setup

### Machine 1 (Server):

```bash
# Update config.h to listen on all interfaces (already set to 0.0.0.0)
cd build
./kv-server

# Monitor in another terminal
cd ..
./monitor_resources.sh
```

### Machine 2 (Load Generator):

```bash
# Replace <server_ip> with actual IP of Machine 1
./run_experiments.sh get_all <server_ip> 8080
```

## Using CPU Pinning (Single Machine)

```bash
# Pin server to cores 0-3
cd build
taskset -c 0-3 ./kv-server &

# Pin load generator to cores 4-7
cd ..
taskset -c 4-7 ./load-generator -h 127.0.0.1 -p 8080 -t 8 -d 300 -w get_all
```

## Monitoring Commands

```bash
# CPU usage
mpstat 1

# Disk I/O
iostat -x 1

# Process CPU
top -d 1

# Network
iftop

# MySQL status
mysql -u root -p -e "SHOW PROCESSLIST;"
mysql -u root -p -e "SHOW STATUS LIKE 'Threads%';"

# Server cache stats
curl http://localhost:8080/status | python3 -m json.tool
```

## Troubleshooting

### Port already in use:

```bash
sudo lsof -i :8080
sudo kill -9 <PID>
```

### Database connection failed:

```bash
sudo service mysql status
sudo service mysql start
mysql -u root -p -e "USE kvstore_db; SHOW TABLES;"
```

### Load generator timeout:

```bash
# Increase timeout
./load-generator -h 127.0.0.1 -p 8080 -t 5 -d 60 -w get_all --timeout 10000
```

### Clear database between tests:

```bash
mysql -u root -p -e "USE kvstore_db; TRUNCATE TABLE kv_pairs; TRUNCATE TABLE hash_store;"
```

## Expected Behavior

### Get All (Disk-Bound):

- Throughput plateaus early
- Disk utilization → 100%
- Low cache hit rate
- Response time increases sharply

### Put All (Disk-Bound):

- Lower throughput than Get All
- Disk write utilization → 100%
- Database is bottleneck

### Get Popular (CPU/Memory-Bound):

- Higher throughput
- CPU utilization → 100%
- High cache hit rate (>95%)
- Low disk utilization

### Mixed:

- Balanced utilization
- Bottleneck depends on mix ratios

## Demo Preparation

1. ✓ Build and test server
2. ✓ Run full experiment suite for 2+ workloads
3. ✓ Generate graphs with plot_results.py
4. ✓ Document hardware specs
5. ✓ Identify bottlenecks with monitoring data
6. ✓ Be ready to reproduce numbers live
7. ✓ Have monitoring commands ready
8. ✓ Know your capacity estimates
