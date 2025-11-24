# Load Generator Architecture

## Overview

The load generator is a **closed-loop, multi-threaded** system designed to stress-test the HTTP server by generating continuous requests without think time.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Load Generator Process                       │
│                                                                   │
│  ┌─────────────┐                                                │
│  │   Main      │                                                │
│  │   Thread    │                                                │
│  └──────┬──────┘                                                │
│         │                                                        │
│         │ Creates & manages                                     │
│         │                                                        │
│         ├────────────┬────────────┬────────────┬───────────┐   │
│         ▼            ▼            ▼            ▼           ▼   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   ...   │
│  │ Worker   │ │ Worker   │ │ Worker   │ │ Worker   │          │
│  │ Thread 1 │ │ Thread 2 │ │ Thread 3 │ │ Thread N │          │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
│       │            │            │            │                 │
│       │            │            │            │                 │
│       │  ┌─────────┴────────────┴────────────┴──────┐         │
│       │  │                                            │         │
│       │  │      Shared Metrics (Thread-Safe)         │         │
│       │  │  - Total Requests                         │         │
│       │  │  - Successful Requests                    │         │
│       │  │  - Failed Requests                        │         │
│       │  │  - Response Times (for percentiles)       │         │
│       │  │                                            │         │
│       │  └────────────────────────────────────────────┘         │
│       │                                                         │
│       │ Each worker has:                                       │
│       │ • HTTPClient (socket-based)                            │
│       │ • WorkloadGenerator (request patterns)                 │
│       │ • Metrics collector                                    │
│       │                                                         │
└───────┼─────────────────────────────────────────────────────────┘
        │
        │ HTTP Requests
        │ (socket connections)
        ▼
┌───────────────────┐
│   HTTP Server     │
│   (port 8080)     │
└───────────────────┘
```

## Component Details

### Main Thread

- **Responsibilities:**
  - Parse command-line arguments (host, port, threads, duration, workload)
  - Create worker threads
  - Monitor progress and display real-time statistics
  - Wait for test duration to complete
  - Signal workers to stop
  - Calculate final metrics (percentiles, averages)

### Worker Threads

Each worker thread runs independently in a closed loop:

```cpp
while (!should_stop) {
    1. Generate request (method, path, params) based on workload type
    2. Send HTTP request via socket
    3. Measure response time
    4. Record metrics (success/failure, latency)
    5. Immediately repeat (no think time)
}
```

### HTTPClient (Per Worker)

```
┌─────────────────┐
│  HTTPClient     │
├─────────────────┤
│ • create_socket │──┐
│ • connect       │  │
│ • send_request  │  │── Raw socket operations
│ • recv_response │  │   (HTTP/1.1 protocol)
│ • close_socket  │──┘
└─────────────────┘
```

### WorkloadGenerator (Per Worker)

```
┌──────────────────────┐
│ WorkloadGenerator    │
├──────────────────────┤
│ • random_key()       │─── Generate random key_123456
│ • random_value()     │─── Generate random 50-char value
│ • popular_key()      │─── Pick from 10 hot keys
│ • random_double()    │─── For operation selection
└──────────────────────┘
```

### Shared Metrics (Thread-Safe)

```
┌────────────────────────────────┐
│  Metrics (mutex-protected)     │
├────────────────────────────────┤
│ • atomic<int> total_requests   │
│ • atomic<int> success_count    │
│ • atomic<int> failed_count     │
│ • vector<double> response_times│ (mutex-protected)
└────────────────────────────────┘
```

## Request Flow

```
Worker Thread
    │
    ├─► WorkloadGenerator.generate_request()
    │       │
    │       ├─► Based on workload_type:
    │       │   • get_all      → GET /kv/read?key=key_123
    │       │   • put_all      → POST /kv/create?key=key_456&value=abc...
    │       │   • get_popular  → GET /kv/read?key=popular_key_5
    │       │   • mixed         → Random mix of GET/POST/DELETE
    │       │   • compute_prime → GET /compute/prime?n=100000
    │       │   • compute_hash  → GET /compute/hash?data=abc...
    │       │   • compute_mixed → Random compute operations
    │       │
    │       └─► Return (method, path, query_params)
    │
    ├─► HTTPClient.send_request(method, path, params)
    │       │
    │       ├─► socket() → Create TCP socket
    │       ├─► connect() → Connect to server:port
    │       ├─► send() → Send HTTP request:
    │       │            "GET /kv/read?key=key_123 HTTP/1.1\r\n"
    │       │            "Host: 127.0.0.1\r\n"
    │       │            "Connection: close\r\n\r\n"
    │       │
    │       ├─► recv() → Receive HTTP response
    │       ├─► close() → Close socket
    │       │
    │       └─► Return (success, response_time_ms)
    │
    └─► Metrics.record(success, response_time)
            │
            └─► Update counters + append to response_times vector
```

## Workload Types

| Workload          | Operations                         | Request Pattern            |
| ----------------- | ---------------------------------- | -------------------------- |
| **get_all**       | 100% reads                         | Random keys (cache misses) |
| **put_all**       | 90% writes, 10% deletes            | Random keys                |
| **get_popular**   | 100% reads                         | 10 hot keys (cache hits)   |
| **mixed**         | 50% reads, 30% writes, 20% deletes | Random keys                |
| **compute_prime** | 100% prime computation             | n=100000                   |
| **compute_hash**  | 100% hash computation              | Random 100-char strings    |
| **compute_mixed** | 50% prime, 50% hash                | Mixed compute              |

## Metrics Collection

### Real-Time Metrics (Per Second)

```
Main Thread (every 1 second):
    current_throughput = (total_requests - last_count) / 1.0
    Display: "[5s] Success: 1234 | Failed: 5 | Throughput: 1234.00 req/s"
```

### Final Metrics (End of Test)

```
Calculate:
    • Total duration
    • Average throughput = total_requests / duration
    • Average response time = sum(response_times) / count
    • Success rate = (success_count / total_requests) * 100
    • Percentiles (P50, P95, P99):
        - Sort response_times
        - P50 = response_times[50% index]
        - P95 = response_times[95% index]
        - P99 = response_times[99% index]
```

## Key Design Features

1. **Closed-Loop Design**

   - No think time between requests
   - Simulates maximum load
   - Each thread continuously sends requests

2. **Thread Independence**

   - Each thread has its own HTTP client
   - No shared connection pools
   - Prevents thread contention

3. **Socket-Based HTTP**

   - Raw TCP sockets (no library dependencies)
   - Manual HTTP/1.1 protocol implementation
   - Connection: close (new connection per request)

4. **Configurable Parameters**

   ```bash
   ./load-generator -h HOST -p PORT -t THREADS -d DURATION -w WORKLOAD
   ```

5. **Resource Isolation**
   - Load generator pinned to separate CPU cores
   - Prevents interference with server measurement

## Performance Characteristics

- **Scalability**: Linear scaling up to CPU cores
- **Overhead**: Minimal (C++, raw sockets)
- **Accuracy**: Microsecond-precision timing
- **Throughput**: Can generate 10,000+ req/s per core
