# KV Store Server with Load Generator

## Project Structure

This project consists of two main components:

1. **KV Store Server** - Multi-tier HTTP server (root directory)
2. **Load Generator** - Load testing tool (`load_generator/` directory)

---

## 📁 Directory Structure

```
multi_threaded-HTTP-server/
├── server/              # Server implementation
├── cache/               # Cache implementation
├── db/                  # Database layer
├── include/             # Headers and config
├── build/               # Server build directory
├── load_generator/      # Load generator (all testing tools)
│   ├── load_generator.cpp
│   ├── build.sh
│   ├── run_experiments.sh
│   ├── monitor_resources.sh
│   ├── parse_results.py
│   ├── plot_results.py
│   ├── README.md
│   ├── QUICK_START.md
│   ├── README_LOAD_TESTING.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── REPORT_TEMPLATE.md
│   └── DEMO_CHECKLIST.md
└── README.md            # This file
```

---

## 🚀 Quick Start

### 1. Build KV Store Server

```bash
# Build server
mkdir -p build
cd build
cmake ..
make
```

### 2. Build Load Generator

```bash
# Go to load generator directory
cd load_generator

# Build
./build.sh
# Or manually:
g++ -std=c++17 -pthread -O3 -o load-generator load_generator.cpp
```

### 3. Run Server

```bash
cd build
./kv-server
```

### 4. Run Load Tests

```bash
cd load_generator

# Single test
./load-generator -h 127.0.0.1 -p 8080 -t 10 -d 60 -w get_all

# Full experiment suite
./run_experiments.sh get_all 127.0.0.1 8080
```

For detailed instructions, see `load_generator/QUICK_START.md`

---

## 📦 Components

### KV Store Server

- **Multi-threaded HTTP server** using httplib
- **LRU cache** for fast key-value access
- **MySQL database** backend with connection pooling
- **Endpoints**:
  - `POST /kv/create` - Create/update key-value pairs
  - `GET /kv/read` - Read key-value pairs
  - `DELETE /kv/delete` - Delete key-value pairs
  - `GET /compute/prime` - Compute prime numbers
  - `GET /compute/hash` - Compute text hash
  - `GET /status` - Server statistics

### Load Generator

- **Closed-loop multi-threaded** design
- **4 workload types**: get_all, put_all, get_popular, mixed
- **Automatic request generation**
- **Comprehensive metrics**: throughput, latency, percentiles
- **Analysis tools**: result parsing and graph generation

See `load_generator/README.md` for details

---

## ✅ Requirements Checklist

### Load Generator Requirements

- ✅ **Closed-loop**: Each thread waits for response before next request
- ✅ **Multi-threaded**: Configurable number of client threads
- ✅ **Zero think time**: Immediate next request after response
- ✅ **Configurable**: Command-line args for threads, duration, workload
- ✅ **Auto-generated requests**: No user input or file reading
- ✅ **Multiple workloads**: Put all, Get all, Get popular, Mixed
- ✅ **Failure handling**: Socket timeouts, connection errors handled
- ✅ **Metrics**: Throughput, response time, percentiles

### Experiment Requirements

- ✅ **5+ load levels**: Script tests at 1, 5, 10, 20, 40 threads
- ✅ **5+ minutes per test**: Default 300 seconds (configurable)
- ✅ **Resource separation**: Instructions for two machines or CPU pinning
- ✅ **Steady state**: Warm-up and stability monitoring
- ✅ **2+ workloads**: Can easily run all 4 workload types
- ✅ **Different bottlenecks**: Get all (disk) vs Get popular (CPU)

### Metrics Collection

- ✅ **Average throughput**: Requests per second
- ✅ **Average response time**: Milliseconds
- ✅ **Percentiles**: P50, P95, P99
- ✅ **Success rate**: Percentage of successful requests
- ✅ **Resource utilization**: Scripts to monitor CPU, disk, memory

### Deliverables

- ✅ **Graphs**: Automated plotting script
- ✅ **Report template**: Complete structure provided
- ✅ **Analysis tools**: Scripts to parse and analyze results
- ✅ **Documentation**: Step-by-step guides

---

## 🚀 Running Load Tests

All scripts and documentation are in the `load_generator/` directory.

```bash
# Navigate to load generator
cd load_generator

# Run experiments
./run_experiments.sh get_all 127.0.0.1 8080

# Monitor resources (in another terminal)
./monitor_resources.sh

# Analyze results
python3 parse_results.py results_get_all_*/
python3 plot_results.py results_get_all_*/summary.csv
```

For complete instructions, see:

- `load_generator/QUICK_START.md` - Step-by-step guide
- `load_generator/README_LOAD_TESTING.md` - Full documentation
- `load_generator/DEMO_CHECKLIST.md` - Demo preparation

---

## 🎯 For Your Demo (20 Marks)

### Workload 1: Get All (10 marks) - Disk Bottleneck

```bash
cd load_generator

# Run experiments
./run_experiments.sh get_all <server_ip> 8080

# Generate graphs
python3 plot_results.py results_get_all_*/summary.csv
```

**Expected Results:**

- Throughput plateaus at ~500-1000 req/s (depends on disk)
- Disk utilization → 100%
- Cache hit rate < 5%
- Response time increases sharply at saturation

### Workload 2: Get Popular (10 marks) - CPU Bottleneck

```bash
cd load_generator

# Run experiments
./run_experiments.sh get_popular <server_ip> 8080

# Generate graphs
python3 plot_results.py results_get_popular_*/summary.csv
```

```bash
# Run experiments
./run_experiments.sh get_popular <server_ip> 8080

# Generate graphs
python3 plot_results.py results_get_popular_*/summary.csv
```

**Expected Results:**

- Much higher throughput (2000-5000 req/s depending on CPU)
- CPU utilization → 100%
- Cache hit rate > 95%
- Low disk utilization

### Grading Breakdown

**3 marks - Graphs:**

- ✅ Throughput vs load (shows plateau)
- ✅ Response time vs load (shows increase)
- ✅ Utilization graphs (show bottleneck)

**3 marks - Reproduce Numbers:**

- ✅ Run: `./load-generator -h <ip> -p 8080 -t X -d 300 -w <workload>`
- ✅ Show it matches your graph data point

**4 marks - Proper Guidelines:**

- ✅ Load generator generates enough load (monitor shows capacity)
- ✅ Resources separated (two machines or taskset)
- ✅ 5+ different load levels (1, 5, 10, 20, 40)
- ✅ 5+ minutes per test (300 seconds default)
- ✅ Steady state reached (script includes warm-up)

---

## 📊 Workload Characteristics

### 1. Get All (Cache Miss Heavy)

```bash
./load-generator -w get_all -t 10 -d 300
```

- **Requests**: 100% reads with unique keys
- **Cache**: Miss on every request
- **Database**: Read on every request
- **Bottleneck**: Disk I/O (reads)
- **Expected Throughput**: Low (disk limited)

### 2. Put All (Write Heavy)

```bash
./load-generator -w put_all -t 10 -d 300
```

- **Requests**: 90% creates, 10% deletes
- **Cache**: Write-through
- **Database**: Write on every request
- **Bottleneck**: Disk I/O (writes)
- **Expected Throughput**: Very low (writes slower)

### 3. Get Popular (Cache Hit Heavy)

```bash
./load-generator -w get_popular -t 10 -d 300
```

- **Requests**: 100% reads, 10 popular keys only
- **Cache**: Hit on >95% of requests
- **Database**: Rarely accessed
- **Bottleneck**: CPU / Memory
- **Expected Throughput**: High (cache fast)

### 4. Mixed (Realistic)

```bash
./load-generator -w mixed -t 10 -d 300
```

- **Requests**: 70% reads, 20% creates, 10% deletes
- **Cache**: Mix of hits and misses
- **Database**: Moderate access
- **Bottleneck**: Varies
- **Expected Throughput**: Medium

---

## 🔧 Customization

### Modify Workload Distribution

Edit `load_generator.cpp`:

```cpp
// Example: Change mixed workload to 50% reads, 40% creates, 10% deletes
else if (config.workload_type == "mixed") {
    double rand = wg.random_double();
    if (rand < 0.50) {      // Changed from 0.70
        // reads
    } else if (rand < 0.90) { // Now 40% creates
        // creates
    } else {
        // deletes
    }
}
```

### Add New Workload

```cpp
else if (config.workload_type == "custom") {
    // Your custom workload logic
}
```

Then rebuild:

```bash
make loadgen
```

### Change Load Levels

Edit `run_experiments.sh`:

```bash
LOAD_LEVELS=(2 8 16 32 64)  # Your custom load levels
```

---

## 📈 Expected Graph Patterns

### Throughput Graph

```
  ^
  |     ___________________  ← Plateau (capacity)
R |   /
e |  /
q | /
/s|/
  +------------------------->
     Load Level (threads)
```

### Response Time Graph

```
  ^
  |                    /|  ← Sharp increase
m |                  /
s |                /
  |             /
  |___________/         ← Low and stable
  +------------------------->
     Load Level (threads)
```

---

## 🐛 Troubleshooting

### Server Connection Issues

```bash
# Check server is running
curl http://localhost:8080/status

# Check port
sudo lsof -i :8080

# Test connection from load gen machine
ping <server_ip>
curl http://<server_ip>:8080/status
```

### Load Generator Timeouts

```bash
# Increase timeout
./load-generator --timeout 10000 -t 5 -d 60 -w get_all

# Reduce load
./load-generator -t 2 -d 60 -w get_all
```

### MySQL Connection Errors

```bash
# Check MySQL running
sudo service mysql status
sudo service mysql start

# Test connection
mysql -u root -p -e "USE kvstore_db; SHOW TABLES;"

# Check credentials in include/config.h
```

### Low Throughput

```bash
# Check if load generator is bottleneck
# On load gen machine during test:
top  # Should NOT be at 100% CPU

# If load gen is bottleneck:
# 1. Use separate machine
# 2. Increase load gen resources
# 3. Check network latency
```

---

## 📝 Report Writing

Use `REPORT_TEMPLATE.md` and fill in:

1. **System Architecture**: Hardware specs, diagram
2. **Load Generator Design**: How it works, workload logic
3. **Experiment Setup**: Two machines, separation method
4. **Results Workload 1**: Graphs, tables, bottleneck analysis
5. **Results Workload 2**: Graphs, tables, bottleneck analysis
6. **Comparative Analysis**: Compare the two workloads
7. **Conclusions**: Summary, capacity, bottlenecks

### Key Points to Include

- Throughput plateaus → capacity reached
- Response time increases → saturation
- Resource utilization → identifies bottleneck
- Cache hit rate → explains performance difference

---

## ✨ Pro Tips

1. **Always monitor**: Run `./monitor_resources.sh` during tests
2. **Document everything**: Take screenshots, save logs
3. **Practice reproducing**: Try to match graph numbers live
4. **Clear state**: Reset database between workload types if needed
5. **Check load gen**: Ensure it's not the bottleneck
6. **Warm up**: First 30s should be excluded from analysis
7. **Steady state**: Last 2-3 minutes should be stable
8. **Multiple runs**: Average 2-3 runs for reliability

---

## 📞 Support

If you need help with:

- Understanding any part of the code
- Modifying workloads
- Debugging issues
- Interpreting results
- Writing the report

Just ask! The implementation is modular and well-documented.

---

## 🎓 Learning Outcomes

By using this implementation, you'll understand:

- **Closed-loop load testing**: How clients behave realistically
- **Performance bottlenecks**: CPU vs Disk vs Memory vs Network
- **Cache effectiveness**: Impact on throughput and latency
- **System capacity**: Finding saturation points
- **Resource monitoring**: Identifying bottlenecks
- **Performance analysis**: Interpreting graphs and metrics

---

## ✅ Final Checklist

Before Demo:

- [ ] Server builds and runs successfully
- [ ] Load generator builds and runs successfully
- [ ] Can connect from load gen to server
- [ ] Ran experiments for 2+ workloads
- [ ] Generated graphs for each workload
- [ ] Have monitoring data showing bottlenecks
- [ ] Report written with template
- [ ] Can reproduce any data point from graphs
- [ ] Understand why bottlenecks are different
- [ ] Know system capacity for each workload

---

## 🎉 You're Ready!

You now have everything needed for Part B:

- ✅ Fully functional load generator
- ✅ Automated experiment scripts
- ✅ Analysis and plotting tools
- ✅ Complete documentation
- ✅ Report template
- ✅ Demo preparation guide

**Next step**: Run your experiments and write the report!

Good luck with your demo! 🚀
