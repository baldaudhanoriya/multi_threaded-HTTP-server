# KV Store Server - Load Testing Guide

## Project Overview

This project consists of a multi-tier KV Store HTTP server with an LRU cache layer backed by MySQL, and a closed-loop load generator for performance testing.

### Architecture

```
Client (Load Generator) → HTTP Server (Multi-threaded) → Cache (LRU) → Database (MySQL)
```

## Components

### 1. KV Store Server (`kv-server`)

- Multi-threaded HTTP server (using httplib)
- LRU cache for KV pairs and hash computations
- MySQL database backend with connection pooling
- Endpoints:
  - `POST /kv/create` - Create/update key-value pairs
  - `GET /kv/read` - Read key-value pairs
  - `DELETE /kv/delete` - Delete key-value pairs
  - `GET /compute/prime` - Compute prime numbers
  - `GET /compute/hash` - Compute text hash
  - `GET /status` - Server statistics

### 2. Load Generator (`load-generator`)

- Closed-loop multi-threaded client
- Zero think time between requests
- Configurable workload types
- Automatic request generation
- Metrics: throughput, response time, percentiles

## Building the Project

### Prerequisites

```bash
# Install dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install build-essential cmake libmysqlclient-dev mysql-server

# Or on WSL
sudo apt install build-essential cmake default-libmysqlclient-dev mysql-server
```

### Build Server

```bash
cd multi_threaded-HTTP-server
mkdir -p build
cd build
cmake ..
make
```

### Build Load Generator

```bash
cd multi_threaded-HTTP-server
g++ -std=c++17 -pthread -o load-generator load_generator.cpp
# Or using CMake
cmake -S . -B build_loadgen -DCMAKE_BUILD_TYPE=Release
cmake --build build_loadgen
```

## Database Setup

```bash
# Start MySQL
sudo service mysql start

# Create database and tables
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

Update `include/config.h` with your MySQL credentials if needed.

## Running the System

### Start the Server

```bash
cd multi_threaded-HTTP-server/build
./kv-server
```

The server will start on `http://0.0.0.0:8080`

### Run Load Generator

#### Basic Usage

```bash
./load-generator -h <server_host> -p <port> -t <threads> -d <duration> -w <workload>
```

#### Examples

**1. Get All Workload (Disk-bound - Cache Misses)**

```bash
./load-generator -h 127.0.0.1 -p 8080 -t 10 -d 300 -w get_all
```

- Sends read requests with unique keys
- Every request misses cache and hits database
- Tests disk I/O performance

**2. Put All Workload (Disk-bound - Write Heavy)**

```bash
./load-generator -h 127.0.0.1 -p 8080 -t 10 -d 300 -w put_all
```

- Sends create/delete requests (90% create, 10% delete)
- All requests require database writes
- Tests write performance

**3. Get Popular Workload (CPU/Memory-bound - Cache Hits)**

```bash
./load-generator -h 127.0.0.1 -p 8080 -t 10 -d 300 -w get_popular
```

- Sends read requests for small set of popular keys
- Most requests hit cache
- Tests cache and CPU performance

**4. Mixed Workload**

```bash
./load-generator -h 127.0.0.1 -p 8080 -t 10 -d 300 -w mixed
```

- 70% reads (mix of popular and random keys)
- 20% creates
- 10% deletes
- Realistic mixed workload

#### Command Line Options

- `-h HOST` - Server hostname/IP (default: 127.0.0.1)
- `-p PORT` - Server port (default: 8080)
- `-t THREADS` - Number of client threads (default: 1)
- `-d DURATION` - Test duration in seconds (default: 60)
- `-w WORKLOAD` - Workload type: get_all, put_all, get_popular, mixed
- `--timeout MS` - Socket timeout in milliseconds (default: 5000)

## Load Test Experiments

### Experiment Setup

**Two-Machine Setup (Recommended)**

1. **Machine 1**: Run KV server and MySQL database
2. **Machine 2**: Run load generator

**Single-Machine Setup** (if two machines unavailable)

```bash
# Pin server to cores 0-3
taskset -c 0-3 ./kv-server &

# Pin load generator to cores 4-7
taskset -c 4-7 ./load-generator -t 8 -d 300 -w get_all
```

### Running Experiments

For each workload type, run at least 5 experiments with increasing load:

```bash
# Example: Get All workload at different load levels
./load-generator -h <server_ip> -p 8080 -t 1 -d 300 -w get_all    # Low load
./load-generator -h <server_ip> -p 8080 -t 5 -d 300 -w get_all    # Medium-low
./load-generator -h <server_ip> -p 8080 -t 10 -d 300 -w get_all   # Medium
./load-generator -h <server_ip> -p 8080 -t 20 -d 300 -w get_all   # Medium-high
./load-generator -h <server_ip> -p 8080 -t 40 -d 300 -w get_all   # High load
```

### Monitoring Resource Utilization

**During load tests, monitor:**

```bash
# CPU utilization
top -d 1

# Or more detailed
mpstat 1

# Disk I/O
iostat -x 1

# Network
iftop

# MySQL performance
mysql -u root -p -e "SHOW PROCESSLIST;"
mysql -u root -p -e "SHOW STATUS LIKE 'Threads%';"

# Check cache hit rates
curl http://localhost:8080/status
```

### Expected Results

**Get All (Disk-bound)**

- Throughput plateaus at disk I/O limit
- Disk utilization → 100%
- Response time increases sharply at saturation
- Low cache hit rate

**Put All (Disk-bound)**

- Similar to Get All but lower throughput (writes are slower)
- Disk write utilization → 100%
- Database becomes bottleneck

**Get Popular (CPU/Memory-bound)**

- High throughput (cache hits are fast)
- High CPU utilization
- Low disk utilization
- High cache hit rate (>95%)
- Response time stays low longer

**Mixed Workload**

- Bottleneck depends on mix ratios
- More balanced resource utilization

## Data Collection

### Metrics to Record

1. **Throughput** (req/s) at each load level
2. **Average Response Time** (ms) at each load level
3. **P50, P95, P99 latencies**
4. **CPU utilization** (%)
5. **Disk I/O utilization** (%)
6. **Memory usage**
7. **Cache hit rate** (from `/status` endpoint)
8. **Network bandwidth**

### Plotting Results

Create graphs with:

- **X-axis**: Number of client threads (load level)
- **Y-axis**: Performance metrics

Expected graph patterns:

- **Throughput**: Increases linearly, then plateaus at capacity
- **Response Time**: Low and stable, then sharp increase at saturation
- **Utilization**: Bottleneck resource → 100% at capacity

## Troubleshooting

### Server won't start

```bash
# Check if port is in use
sudo lsof -i :8080
# Kill existing process
sudo kill -9 <PID>
```

### Database connection errors

```bash
# Check MySQL is running
sudo service mysql status
sudo service mysql start

# Test connection
mysql -u root -p -e "USE kvstore_db; SHOW TABLES;"
```

### Load generator timeouts

- Increase timeout: `--timeout 10000`
- Reduce number of threads
- Check network connectivity
- Ensure server is not overloaded

### Low throughput

- Check if load generator is the bottleneck (monitor its CPU)
- Increase load generator resources
- Run on separate machine

## Tips for Load Testing

1. **Warm-up period**: Run for 30s before measuring to reach steady state
2. **Long duration**: Run each test for 5+ minutes for stable results
3. **Resource separation**: Use separate machines or CPU pinning
4. **Consistent workload**: Use same workload for comparison across load levels
5. **Multiple runs**: Average results from 3 runs at each load level
6. **Monitor continuously**: Watch resource utilization throughout test
7. **Reset state**: Clear cache/db between tests if needed:
   ```sql
   TRUNCATE TABLE kv_pairs;
   TRUNCATE TABLE hash_store;
   ```

## Example Report Structure

### 1. System Architecture

- Diagram of components
- Hardware specifications
- Software versions

### 2. Load Generator Design

- Closed-loop implementation
- Workload generation logic
- Metrics collection

### 3. Experiment Setup

- Two-machine configuration
- Resource allocation
- Network setup

### 4. Results

For each workload:

- **Throughput vs Load** graph
- **Response Time vs Load** graph
- **Resource Utilization** graphs
- **Cache Hit Rate** data
- Analysis of bottleneck

### 5. Analysis

- Identification of bottlenecks
- Capacity estimation
- Performance characteristics
- Comparison between workloads

## Demo Checklist

- [ ] Build server and load generator successfully
- [ ] Database properly configured
- [ ] Can run server and show it's listening
- [ ] Can run load generator with different workloads
- [ ] Reproduce throughput numbers from report
- [ ] Show resource utilization during test
- [ ] Explain bottleneck identification
- [ ] Show graphs in report match experiments
- [ ] Run for sufficient duration (5+ minutes)
- [ ] Separate resources (load gen vs server)

## Contact

For issues or questions, refer to the project documentation or course materials.
