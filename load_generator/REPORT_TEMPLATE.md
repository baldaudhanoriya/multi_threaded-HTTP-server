# Load Test Report Template

## 1. System Architecture

### Overview

[Insert architecture diagram showing: Client → HTTP Server → Cache → Database]

Multi-tier KV Store with:

- **Frontend**: Multi-threaded HTTP server (C++ with httplib)
- **Cache Layer**: LRU cache (1000 entries for KV, 500 for hash)
- **Backend**: MySQL database with connection pooling (10 connections)

### Hardware Specifications

#### Server Machine (Machine 1)

- **CPU**: [e.g., Intel Core i7, 4 cores, 8 threads, 3.6 GHz]
- **RAM**: [e.g., 16 GB DDR4]
- **Disk**: [e.g., 500GB SSD, SATA 6Gb/s]
- **Network**: [e.g., 1 Gbps Ethernet]
- **OS**: [e.g., Ubuntu 22.04 LTS]

#### Load Generator Machine (Machine 2)

- **CPU**: [e.g., Intel Core i5, 4 cores, 4 threads, 3.2 GHz]
- **RAM**: [e.g., 8 GB DDR4]
- **Network**: [e.g., 1 Gbps Ethernet]
- **OS**: [e.g., Ubuntu 22.04 LTS]

### Software Versions

- **Server**: Custom C++ HTTP server with httplib
- **Database**: MySQL 8.0.x
- **Compiler**: g++ 11.x with -std=c++17
- **Network**: TCP/IP over Ethernet

---

## 2. Load Generator Design

### Implementation

- **Type**: Closed-loop, multi-threaded
- **Language**: C++ with pthread
- **Think Time**: Zero (continuous load)
- **Timeout**: 5000ms per request
- **Thread Model**: One thread = one client

### Request Generation

Automatic request generation without external files:

- Random key generation using mt19937 RNG
- Random value generation (50 chars)
- Workload-specific distributions

### Workload Types

#### 1. Get All (Cache Miss Heavy)

- **Requests**: 100% GET on unique keys
- **Expected Bottleneck**: Disk I/O (cache misses)
- **Characteristics**: Every request hits database

#### 2. Put All (Write Heavy)

- **Requests**: 90% POST, 10% DELETE
- **Expected Bottleneck**: Disk write I/O
- **Characteristics**: All requests modify database

#### 3. Get Popular (Cache Hit Heavy)

- **Requests**: 100% GET on 10 popular keys
- **Expected Bottleneck**: CPU/Memory
- **Characteristics**: High cache hit rate (>95%)

#### 4. Mixed Workload

- **Requests**: 70% GET, 20% POST, 10% DELETE
- **Expected Bottleneck**: Balanced
- **Characteristics**: Mix of cache hits and misses

### Metrics Collection

- **Throughput**: Successful requests per second
- **Response Time**: Average, P50, P95, P99 latencies
- **Success Rate**: Percentage of successful requests
- **Per-thread metrics**: Aggregated across all threads

---

## 3. Experiment Setup

### Resource Separation

- **Method**: [Two separate machines / CPU pinning with taskset]
- **Server CPUs**: [Cores 0-3 / Machine 1]
- **Load Generator CPUs**: [Cores 4-7 / Machine 2]
- **Verification**: Monitored with `top` and `mpstat`

### Network Configuration

- **Connection**: [Direct ethernet / Through switch]
- **Latency**: [< 1ms measured with ping]
- **Bandwidth**: [1 Gbps]

### Load Levels Tested

| Test # | Threads | Duration | Workload        |
| ------ | ------- | -------- | --------------- |
| 1      | 1       | 300s     | [workload_name] |
| 2      | 5       | 300s     | [workload_name] |
| 3      | 10      | 300s     | [workload_name] |
| 4      | 20      | 300s     | [workload_name] |
| 5      | 40      | 300s     | [workload_name] |

### Monitoring Tools

- **CPU**: `mpstat`, `top`
- **Disk I/O**: `iostat`
- **Memory**: `free`, `vmstat`
- **Network**: `iftop`, `netstat`
- **Database**: MySQL `SHOW PROCESSLIST`, `SHOW STATUS`
- **Cache**: Server `/status` endpoint

---

## 4. Results - Workload 1: [Workload Name]

### Performance Graphs

[Insert throughput vs load level graph]

[Insert response time vs load level graph]

### Performance Data

| Threads | Throughput (req/s) | Avg RT (ms) | P95 (ms) | P99 (ms) | Success Rate |
| ------- | ------------------ | ----------- | -------- | -------- | ------------ |
| 1       | [value]            | [value]     | [value]  | [value]  | [value]%     |
| 5       | [value]            | [value]     | [value]  | [value]  | [value]%     |
| 10      | [value]            | [value]     | [value]  | [value]  | [value]%     |
| 20      | [value]            | [value]     | [value]  | [value]  | [value]%     |
| 40      | [value]            | [value]     | [value]  | [value]  | [value]%     |

### Resource Utilization

[Insert resource utilization graphs]

| Threads | CPU (%) | Disk Util (%) | Memory (%) | Cache Hit Rate (%) |
| ------- | ------- | ------------- | ---------- | ------------------ |
| 1       | [value] | [value]       | [value]    | [value]            |
| 5       | [value] | [value]       | [value]    | [value]            |
| 10      | [value] | [value]       | [value]    | [value]            |
| 20      | [value] | [value]       | [value]    | [value]            |
| 40      | [value] | [value]       | [value]    | [value]            |

### Bottleneck Analysis

**Identified Bottleneck**: [e.g., Disk I/O]

**Evidence**:

1. [Observation 1: e.g., Disk utilization reached 98-100% at 20+ threads]
2. [Observation 2: e.g., Throughput plateaued at ~500 req/s]
3. [Observation 3: e.g., CPU utilization remained below 40%]
4. [Observation 4: e.g., Cache hit rate was < 5%]

**Capacity**: [e.g., Maximum sustainable throughput: ~500 req/s]

**Saturation Point**: [e.g., 20 threads]

---

## 5. Results - Workload 2: [Workload Name]

### Performance Graphs

[Insert throughput vs load level graph]

[Insert response time vs load level graph]

### Performance Data

[Same table structure as Workload 1]

### Resource Utilization

[Same table structure as Workload 1]

### Bottleneck Analysis

**Identified Bottleneck**: [e.g., CPU]

**Evidence**:
[List observations with data]

**Capacity**: [Maximum sustainable throughput]

**Saturation Point**: [Thread count at saturation]

---

## 6. Comparative Analysis

### Workload Comparison

| Metric               | Workload 1 | Workload 2 |
| -------------------- | ---------- | ---------- |
| Max Throughput       | [value]    | [value]    |
| Bottleneck           | [resource] | [resource] |
| Saturation Point     | [threads]  | [threads]  |
| Cache Hit Rate (avg) | [value]%   | [value]%   |

### Key Observations

1. **Different Bottlenecks**:

   - [Workload 1] was limited by [resource] achieving [X] req/s
   - [Workload 2] was limited by [resource] achieving [Y] req/s

2. **Cache Impact**:

   - [Workload with high cache hits] showed [X]x better throughput
   - Cache effectiveness crucial for [workload type]

3. **Scalability**:

   - [Analysis of how each workload scales with load]

4. **Resource Trade-offs**:
   - [Discussion of resource utilization patterns]

---

## 7. Methodology Validation

### Load Generator Capacity

- **Verification**: Monitored load generator CPU during tests
- **CPU Usage**: Remained below [X]% indicating sufficient capacity
- **Network**: No packet loss or network saturation observed

### Steady State Achievement

- **Warm-up**: First 30 seconds excluded from measurements
- **Duration**: Each test ran for 5 minutes (300s)
- **Stability**: Throughput variance in final 3 minutes < 5%

### Resource Separation

- **Method**: [Two machines / taskset pinning verified]
- **Validation**: Process affinity confirmed with `taskset -p <PID>`

### Repeatability

- **Runs**: [X] runs per load level
- **Variance**: Standard deviation < [Y]%

---

## 8. Conclusions

### Summary

- Successfully implemented and tested multi-tier KV store
- Identified distinct bottlenecks for different workloads
- Measured system capacity at [X] req/s for [workload] and [Y] req/s for [workload]

### Bottlenecks Identified

1. **[Workload 1]**: [Bottleneck resource] - saturated at [X] req/s
2. **[Workload 2]**: [Bottleneck resource] - saturated at [Y] req/s

### Performance Characteristics

- Cache significantly improves throughput ([X]x improvement)
- Disk I/O is limiting factor for cache-miss-heavy workloads
- CPU becomes bottleneck for cache-hit-heavy workloads

### Lessons Learned

- [Key insight 1]
- [Key insight 2]
- [Key insight 3]

---

## Appendix A: Detailed Configuration

### Server Configuration (config.h)

```cpp
const std::string HOST = "0.0.0.0";
const int PORT = 8080;
const int THREADS = 8;
const int CACHE_SIZE = 1000;
const int HASH_CACHE_SIZE = 500;
const int DB_POOL = 10;
```

### Database Schema

[Include CREATE TABLE statements]

### Sample Commands

[Include actual commands used for experiments]

---

## Appendix B: Raw Data

[Include links to or excerpts from raw log files]

---

## Appendix C: Monitoring Screenshots

[Include screenshots of resource monitoring during tests]
