// Load Generator for KV Store Server
// Closed-loop multi-threaded load generator with configurable workloads

#include <iostream>
#include <thread>
#include <vector>
#include <atomic>
#include <chrono>
#include <random>
#include <mutex>
#include <iomanip>
#include <cstring>
#include <algorithm>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <sstream>

using namespace std;
using namespace chrono;

// Configuration
struct Config
{
    string server_host = "127.0.0.1";
    int server_port = 8080;
    int num_threads = 1;
    int duration_seconds = 60;
    string workload_type = "get_all"; // get_all, put_all, get_popular, mixed
    int timeout_ms = 5000;            // socket timeout
};

// Metrics collection
struct Metrics
{
    atomic<uint64_t> total_requests{0};
    atomic<uint64_t> successful_requests{0};
    atomic<uint64_t> failed_requests{0};
    atomic<uint64_t> total_response_time_ms{0};

    mutex mtx;
    vector<double> response_times; // for detailed stats
};

// Simple HTTP client
class HTTPClient
{
private:
    string host;
    int port;
    int timeout_ms;

public:
    HTTPClient(const string &h, int p, int timeout)
        : host(h), port(p), timeout_ms(timeout) {}

    bool send_request(const string &method, const string &path,
                      const string &query_params, string &response,
                      double &response_time_ms)
    {
        auto start = high_resolution_clock::now();

        // Create socket
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0)
        {
            response_time_ms = 0;
            return false;
        }

        // Set timeout
        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

        // Connect
        struct sockaddr_in server_addr;
        memset(&server_addr, 0, sizeof(server_addr));
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(port);

        if (inet_pton(AF_INET, host.c_str(), &server_addr.sin_addr) <= 0)
        {
            close(sock);
            response_time_ms = 0;
            return false;
        }

        if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0)
        {
            close(sock);
            response_time_ms = 0;
            return false;
        }

        // Build HTTP request
        stringstream request;
        request << method << " " << path;
        if (!query_params.empty())
        {
            request << "?" << query_params;
        }
        request << " HTTP/1.1\r\n";
        request << "Host: " << host << "\r\n";
        request << "Connection: close\r\n";
        request << "Content-Length: 0\r\n";
        request << "\r\n";

        string req_str = request.str();

        // Send request
        ssize_t sent = send(sock, req_str.c_str(), req_str.length(), 0);
        if (sent < 0)
        {
            close(sock);
            response_time_ms = 0;
            return false;
        }

        // Receive response
        char buffer[4096];
        string full_response;
        ssize_t received;

        while ((received = recv(sock, buffer, sizeof(buffer) - 1, 0)) > 0)
        {
            buffer[received] = '\0';
            full_response += buffer;
        }

        close(sock);

        auto end = high_resolution_clock::now();
        response_time_ms = duration_cast<microseconds>(end - start).count() / 1000.0;

        if (full_response.empty())
        {
            return false;
        }

        response = full_response;

        // Check if response indicates success (2xx or 404 for gets is acceptable)
        if (full_response.find("HTTP/1.1 2") != string::npos ||
            (method == "GET" && full_response.find("HTTP/1.1 404") != string::npos))
        {
            return true;
        }

        return false;
    }
};

// Workload generators
class WorkloadGenerator
{
private:
    int thread_id;

public:
    mt19937 rng;

    WorkloadGenerator(int tid) : thread_id(tid)
    {
        rng.seed(thread_id + time(nullptr));
    }

    // Generate random key
    string random_key(int min_id = 0, int max_id = 1000000)
    {
        uniform_int_distribution<int> dist(min_id, max_id);
        return "key_" + to_string(dist(rng));
    }

    // Generate random value
    string random_value(int length = 50)
    {
        static const char charset[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        string value;
        uniform_int_distribution<int> dist(0, sizeof(charset) - 2);
        for (int i = 0; i < length; ++i)
        {
            value += charset[dist(rng)];
        }
        return value;
    }

    // Generate popular key (from small set)
    string popular_key(int max_popular = 10)
    {
        uniform_int_distribution<int> dist(0, max_popular - 1);
        return "popular_key_" + to_string(dist(rng));
    }

    // Get random number between 0 and 1
    double random_double()
    {
        uniform_real_distribution<double> dist(0.0, 1.0);
        return dist(rng);
    }
};

// Worker thread function
void worker_thread(int thread_id, const Config &config, Metrics &metrics,
                   atomic<bool> &should_stop)
{

    HTTPClient client(config.server_host, config.server_port, config.timeout_ms);
    WorkloadGenerator wg(thread_id);

    cout << "[Thread " << thread_id << "] Started\n";

    while (!should_stop.load())
    {
        metrics.total_requests++;

        string method, path, params, response;
        double response_time_ms;
        bool success = false;

        // Generate request based on workload type
        if (config.workload_type == "put_all")
        {
            // Only create/delete operations
            if (wg.random_double() < 0.9)
            {
                // 90% creates
                method = "POST";
                path = "/kv/create";
                params = "key=" + wg.random_key() + "&value=" + wg.random_value();
            }
            else
            {
                // 10% deletes
                method = "DELETE";
                path = "/kv/delete";
                params = "key=" + wg.random_key();
            }
        }
        else if (config.workload_type == "get_all")
        {
            // Only read operations with unique keys (cache misses)
            method = "GET";
            path = "/kv/read";
            params = "key=" + wg.random_key();
        }
        else if (config.workload_type == "get_popular")
        {
            // Only read operations with popular keys (cache hits)
            method = "GET";
            path = "/kv/read";
            params = "key=" + wg.popular_key(10);
        }
        else if (config.workload_type == "compute_prime")
        {
            // CPU-intensive: compute prime numbers
            method = "GET";
            path = "/compute/prime";
            uniform_int_distribution<int> dist(100, 1000);
            int count = dist(wg.rng);
            params = "count=" + to_string(count);
        }
        else if (config.workload_type == "compute_hash")
        {
            // CPU-intensive: compute hash
            method = "GET";
            path = "/compute/hash";
            params = "text=" + wg.random_value(100);
        }
        else if (config.workload_type == "compute_mixed")
        {
            // Mixed compute workload: 60% hash, 40% prime
            if (wg.random_double() < 0.6)
            {
                method = "GET";
                path = "/compute/hash";
                params = "text=" + wg.random_value(100);
            }
            else
            {
                method = "GET";
                path = "/compute/prime";
                uniform_int_distribution<int> dist(100, 1000);
                int count = dist(wg.rng);
                params = "count=" + to_string(count);
            }
        }
        else if (config.workload_type == "mixed")
        {
            // Mixed workload: 70% reads, 20% creates, 10% deletes
            double rand = wg.random_double();
            if (rand < 0.70)
            {
                // 70% reads
                method = "GET";
                path = "/kv/read";
                // Mix of popular and random keys
                if (wg.random_double() < 0.3)
                {
                    params = "key=" + wg.popular_key(20);
                }
                else
                {
                    params = "key=" + wg.random_key();
                }
            }
            else if (rand < 0.90)
            {
                // 20% creates
                method = "POST";
                path = "/kv/create";
                params = "key=" + wg.random_key() + "&value=" + wg.random_value();
            }
            else
            {
                // 10% deletes
                method = "DELETE";
                path = "/kv/delete";
                params = "key=" + wg.random_key();
            }
        }
        else
        {
            // Default to get_all
            method = "GET";
            path = "/kv/read";
            params = "key=" + wg.random_key();
        }

        // Send request and measure response time
        success = client.send_request(method, path, params, response, response_time_ms);

        if (success)
        {
            metrics.successful_requests++;
            metrics.total_response_time_ms += (uint64_t)response_time_ms;

            // Store individual response time for detailed analysis
            {
                lock_guard<mutex> lock(metrics.mtx);
                metrics.response_times.push_back(response_time_ms);
            }
        }
        else
        {
            metrics.failed_requests++;
        }

        // Zero think time - immediately proceed to next request
    }

    cout << "[Thread " << thread_id << "] Stopped\n";
}

// Print usage
void print_usage(const char *program_name)
{
    cout << "Usage: " << program_name << " [options]\n";
    cout << "Options:\n";
    cout << "  -h HOST          Server host (default: 127.0.0.1)\n";
    cout << "  -p PORT          Server port (default: 8080)\n";
    cout << "  -t THREADS       Number of client threads (default: 1)\n";
    cout << "  -d DURATION      Test duration in seconds (default: 60)\n";
    cout << "  -w WORKLOAD      Workload type (default: get_all)\n";
    cout << "                   Options: get_all, put_all, get_popular, mixed,\n";
    cout << "                            compute_prime, compute_hash, compute_mixed\n";
    cout << "  --timeout MS     Socket timeout in milliseconds (default: 5000)\n";
    cout << "\nWorkload descriptions:\n";
    cout << "  get_all        - Read requests with unique keys (cache misses, disk-bound)\n";
    cout << "  put_all        - Create/delete requests (disk-bound)\n";
    cout << "  get_popular    - Read requests with popular keys (cache hits, CPU/memory-bound)\n";
    cout << "  mixed          - 70% reads, 20% creates, 10% deletes\n";
    cout << "  compute_prime  - CPU-intensive prime number computation\n";
    cout << "  compute_hash   - CPU-intensive hash computation\n";
    cout << "  compute_mixed  - Mixed compute workload (60% hash, 40% prime)\n";
}

// Parse command line arguments
bool parse_args(int argc, char *argv[], Config &config)
{
    for (int i = 1; i < argc; i++)
    {
        string arg = argv[i];

        if (arg == "-h" && i + 1 < argc)
        {
            config.server_host = argv[++i];
        }
        else if (arg == "-p" && i + 1 < argc)
        {
            config.server_port = stoi(argv[++i]);
        }
        else if (arg == "-t" && i + 1 < argc)
        {
            config.num_threads = stoi(argv[++i]);
        }
        else if (arg == "-d" && i + 1 < argc)
        {
            config.duration_seconds = stoi(argv[++i]);
        }
        else if (arg == "-w" && i + 1 < argc)
        {
            config.workload_type = argv[++i];
        }
        else if (arg == "--timeout" && i + 1 < argc)
        {
            config.timeout_ms = stoi(argv[++i]);
        }
        else if (arg == "--help")
        {
            return false;
        }
        else
        {
            cerr << "Unknown argument: " << arg << "\n";
            return false;
        }
    }

    // Validate workload type
    if (config.workload_type != "get_all" &&
        config.workload_type != "put_all" &&
        config.workload_type != "get_popular" &&
        config.workload_type != "mixed" &&
        config.workload_type != "compute_prime" &&
        config.workload_type != "compute_hash" &&
        config.workload_type != "compute_mixed")
    {
        cerr << "Invalid workload type: " << config.workload_type << "\n";
        return false;
    }

    return true;
}

// Calculate percentile
double calculate_percentile(vector<double> &data, double percentile)
{
    if (data.empty())
        return 0.0;

    sort(data.begin(), data.end());
    size_t index = (size_t)(percentile / 100.0 * data.size());
    if (index >= data.size())
        index = data.size() - 1;

    return data[index];
}

int main(int argc, char *argv[])
{
    Config config;

    if (!parse_args(argc, argv, config))
    {
        print_usage(argv[0]);
        return 1;
    }

    cout << "========================================\n";
    cout << "  KV Store Load Generator\n";
    cout << "========================================\n";
    cout << "Server:    " << config.server_host << ":" << config.server_port << "\n";
    cout << "Threads:   " << config.num_threads << "\n";
    cout << "Duration:  " << config.duration_seconds << " seconds\n";
    cout << "Workload:  " << config.workload_type << "\n";
    cout << "Timeout:   " << config.timeout_ms << " ms\n";
    cout << "========================================\n\n";

    // Initialize metrics
    Metrics metrics;
    atomic<bool> should_stop(false);

    // Start worker threads
    vector<thread> threads;
    auto start_time = high_resolution_clock::now();

    cout << "Starting " << config.num_threads << " client threads...\n";

    for (int i = 0; i < config.num_threads; i++)
    {
        threads.emplace_back(worker_thread, i, ref(config), ref(metrics), ref(should_stop));
    }

    cout << "Load test running for " << config.duration_seconds << " seconds...\n";
    cout << "Press Ctrl+C to stop early\n\n";

    // Progress reporting
    int elapsed = 0;
    while (elapsed < config.duration_seconds)
    {
        this_thread::sleep_for(seconds(10));
        elapsed += 10;

        uint64_t current_success = metrics.successful_requests.load();
        uint64_t current_failed = metrics.failed_requests.load();
        double current_throughput = (double)current_success / elapsed;

        cout << "[" << elapsed << "s] "
             << "Success: " << current_success
             << " | Failed: " << current_failed
             << " | Throughput: " << fixed << setprecision(2) << current_throughput << " req/s\n";
    }

    // Signal threads to stop
    cout << "\nStopping threads...\n";
    should_stop.store(true);

    // Wait for all threads to finish
    for (auto &t : threads)
    {
        t.join();
    }

    auto end_time = high_resolution_clock::now();
    double actual_duration = duration_cast<milliseconds>(end_time - start_time).count() / 1000.0;

    // Calculate metrics
    uint64_t total_req = metrics.total_requests.load();
    uint64_t success_req = metrics.successful_requests.load();
    uint64_t failed_req = metrics.failed_requests.load();
    uint64_t total_resp_time = metrics.total_response_time_ms.load();

    double throughput = success_req / actual_duration;
    double avg_response_time = success_req > 0 ? (double)total_resp_time / success_req : 0.0;
    double success_rate = total_req > 0 ? (double)success_req / total_req * 100.0 : 0.0;

    // Calculate percentiles
    vector<double> response_times = metrics.response_times;
    double p50 = calculate_percentile(response_times, 50);
    double p95 = calculate_percentile(response_times, 95);
    double p99 = calculate_percentile(response_times, 99);

    // Print results
    cout << "\n========================================\n";
    cout << "  Load Test Results\n";
    cout << "========================================\n";
    cout << "Actual Duration:       " << fixed << setprecision(2) << actual_duration << " seconds\n";
    cout << "Total Requests:        " << total_req << "\n";
    cout << "Successful Requests:   " << success_req << "\n";
    cout << "Failed Requests:       " << failed_req << "\n";
    cout << "Success Rate:          " << fixed << setprecision(2) << success_rate << "%\n";
    cout << "\n";
    cout << "Average Throughput:    " << fixed << setprecision(2) << throughput << " req/s\n";
    cout << "Average Response Time: " << fixed << setprecision(2) << avg_response_time << " ms\n";
    cout << "\n";
    cout << "Response Time Percentiles:\n";
    cout << "  P50 (median):        " << fixed << setprecision(2) << p50 << " ms\n";
    cout << "  P95:                 " << fixed << setprecision(2) << p95 << " ms\n";
    cout << "  P99:                 " << fixed << setprecision(2) << p99 << " ms\n";
    cout << "========================================\n";

    return 0;
}
