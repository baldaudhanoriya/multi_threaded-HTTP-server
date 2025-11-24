# Load Generator for KV Store Server

This directory contains all the files needed to run load tests on the KV Store server.

## Contents

### Core Files

- **load_generator.cpp** - Multi-threaded closed-loop load generator
- **CMakeLists.txt** - Build configuration for load generator

### Scripts

- **build.sh** - Build script for load generator
- **run_experiments.sh** - Automated experiment runner for multiple load levels
- **monitor_resources.sh** - Resource monitoring during tests

### Analysis Tools

- **parse_results.py** - Parse test logs and generate summary
- **plot_results.py** - Generate graphs from results

### Documentation

- **QUICK_START.md** - Quick reference guide
- **README_LOAD_TESTING.md** - Complete load testing guide
- **IMPLEMENTATION_SUMMARY.md** - Implementation details
- **REPORT_TEMPLATE.md** - Report template for submission
- **DEMO_CHECKLIST.md** - Demo preparation checklist

## Quick Start

### Build

```bash
cd load_generator
./build.sh
# Or
g++ -std=c++17 -pthread -O3 -o load-generator load_generator.cpp
```

### Run

```bash
./load-generator -h 127.0.0.1 -p 8080 -t 10 -d 60 -w get_all
```

### Options

- `-h HOST` - Server hostname/IP
- `-p PORT` - Server port
- `-t THREADS` - Number of client threads
- `-d DURATION` - Test duration in seconds
- `-w WORKLOAD` - Workload type: get_all, put_all, get_popular, mixed
- `--timeout MS` - Socket timeout in milliseconds

## Workload Types

1. **get_all** - Cache miss heavy (disk-bound)
2. **put_all** - Write heavy (disk-bound)
3. **get_popular** - Cache hit heavy (CPU-bound)
4. **mixed** - 70% reads, 20% creates, 10% deletes

## Running Experiments

```bash
# Automated experiments at 5 load levels
./run_experiments.sh get_all 127.0.0.1 8080

# Parse results
python3 parse_results.py results_get_all_*/

# Generate graphs
python3 plot_results.py results_get_all_*/summary.csv
```

## Documentation

- See **QUICK_START.md** for step-by-step instructions
- See **README_LOAD_TESTING.md** for comprehensive guide
- See **DEMO_CHECKLIST.md** for demo preparation

## Requirements

- C++17 compiler (g++)
- Python 3 (for analysis scripts)
- matplotlib, pandas (for plotting): `pip install matplotlib pandas`
