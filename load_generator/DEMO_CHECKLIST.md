# Demo Preparation Checklist

## Pre-Demo Setup (Do Before Meeting TA)

### Environment Setup

- [ ] Both machines (or single with CPU pinning) are ready
- [ ] Server machine has MySQL installed and running
- [ ] Database `kvstore_db` created with both tables
- [ ] Server builds successfully: `make server` or `./build.sh`
- [ ] Load generator builds successfully: `make loadgen`
- [ ] Scripts are executable: `make scripts`
- [ ] Network connectivity verified between machines

### Completed Experiments

- [ ] Ran full experiment suite for Workload 1
- [ ] Ran full experiment suite for Workload 2
- [ ] Have results directories: `results_<workload>_<timestamp>/`
- [ ] Generated summary CSVs for both workloads
- [ ] Created graphs for both workloads using `plot_results.py`
- [ ] Have monitoring logs showing resource utilization
- [ ] Documented hardware specifications

### Report Ready

- [ ] Report written using template
- [ ] Includes system architecture diagram
- [ ] Has throughput graphs for both workloads
- [ ] Has response time graphs for both workloads
- [ ] Has resource utilization data/graphs
- [ ] Bottleneck analysis documented with evidence
- [ ] Capacity estimates calculated
- [ ] Experiment methodology described

---

## During Demo

### Part 1: Show Your Report (3 marks per workload = 6 marks)

**For Each Workload:**

- [ ] Point out throughput graph
  - Show it increases then plateaus
  - Identify capacity (max throughput)
- [ ] Point out response time graph
  - Show it's low then increases sharply
  - Explain at what load it degrades
- [ ] Show resource utilization data
  - Point to bottleneck resource at 100%
  - Show other resources are not saturated
- [ ] Explain the bottleneck
  - Why this resource is the bottleneck
  - Evidence from monitoring

### Part 2: Reproduce Numbers (3 marks per workload = 6 marks)

**Be Ready To:**

```bash
# Start server if not running
cd build
./kv-server

# TA will ask: "Run test with X threads for workload Y"
./load-generator -h <server_ip> -p 8080 -t X -d 300 -w Y

# Show the output matches your graph
# Point to "Average Throughput: XXX req/s"
# Point to "Average Response Time: XXX ms"
```

**TA May Ask:**

- "Show me the throughput at 10 threads for get_all"
- "Reproduce the response time at 20 threads"
- "Run get_popular with 5 threads"

**Your Response:**

1. Run exact command
2. Wait for completion (or stop early if TA says OK)
3. Point to metrics in output
4. Compare with graph: "See, it matches ~XXX req/s in our graph"

### Part 3: Guidelines Verification (4 marks per workload = 8 marks)

**TA Will Check:**

1. **Load Generator Implementation** (1 mark)

   - [ ] Show `load_generator.cpp` code
   - [ ] Point to closed-loop: thread sends → waits → sends next
   - [ ] Show zero think time: no sleep between requests
   - [ ] Show automatic request generation: no files, random keys
   - [ ] Show it generates enough load: monitor shows it's not bottleneck

2. **Resource Separation** (1 mark)

   - [ ] Show two different machines OR
   - [ ] Show taskset CPU pinning:
     ```bash
     # Show server pinned to cores 0-3
     taskset -p <server_pid>
     # Show load gen can pin to cores 4-7
     ```

3. **Load Levels** (1 mark)

   - [ ] Show you tested 5+ load levels
   - [ ] Point to results directories or log files
   - [ ] Show `run_experiments.sh` with load levels array

4. **Duration and Steady State** (1 mark)
   - [ ] Show test duration: 300 seconds (5 minutes)
   - [ ] Show steady state achieved:
     - Point to progress logs showing stable throughput
     - Show last 2-3 minutes have < 5% variation
   - [ ] Explain warm-up period excluded

---

## Commands to Have Ready

### Show Server Running

```bash
# Server status
curl http://localhost:8080/status | python3 -m json.tool

# Process info
ps aux | grep kv-server
```

### Show Resource Monitoring

```bash
# CPU
mpstat 1 5

# Disk I/O
iostat -x 1 5

# Process CPU
top -d 1

# MySQL
mysql -u root -p -e "SHOW PROCESSLIST;"
```

### Show Load Generator Not Bottleneck

```bash
# While load gen is running
ssh <loadgen_machine>
top  # Show CPU usage < 80%
```

### Show Experiment Logs

```bash
# List all experiments
ls -lh results_*/

# Show specific test output
cat results_get_all_*/test_10threads.log

# Show summary
python3 parse_results.py results_get_all_*/
```

### Quick Reproduction

```bash
# Have this ready to copy-paste for quick demo
./load-generator -h <server_ip> -p 8080 -t 10 -d 60 -w get_all
```

---

## Questions TAs Might Ask

### About Load Generator

**Q: How does your load generator work?**
A: "It's closed-loop multi-threaded. Each thread sends a request, waits for response, then immediately sends next request with zero think time."

**Q: How do you generate requests?**
A: "Automatically with random key generation using mt19937. No external files. Keys like 'key_12345' and random 50-char values."

**Q: What workloads can it generate?**
A: "Four types: get_all (unique keys, cache misses), put_all (writes), get_popular (popular keys, cache hits), and mixed."

### About Experiments

**Q: How did you separate resources?**
A: "We used [two separate machines / CPU pinning with taskset]. Server on [cores/machine], load gen on [cores/machine]."

**Q: How long did you run tests?**
A: "5 minutes (300 seconds) per test at each load level. We excluded first 30 seconds as warm-up."

**Q: How many load levels?**
A: "Five levels: 1, 5, 10, 20, and 40 threads."

### About Bottlenecks

**Q: What's the bottleneck for workload 1?**
A: "[Disk I/O / CPU]. Evidence: [resource] reached 98-100% utilization while throughput plateaued at [X] req/s. Other resources like [Y] were only at [Z]%."

**Q: Why is workload 2 different?**
A: "Workload 2 is [characteristic, e.g., cache-hit heavy], so it doesn't stress [disk] but instead saturates [CPU]. Cache hit rate was >95% vs <5% in workload 1."

**Q: What's your system capacity?**
A: "For workload 1: ~[X] req/s (disk-bound). For workload 2: ~[Y] req/s (CPU-bound). Much higher for workload 2 because cache is in-memory."

### About Graphs

**Q: Why does throughput plateau here?**
A: "That's where we hit capacity. The [disk/CPU] reached 100% utilization and couldn't handle more requests even with more client threads."

**Q: Why does response time increase?**
A: "As we approach capacity, requests start queuing. The server can't process them fast enough, so they wait longer, increasing response time."

---

## Potential Issues & Solutions

### Issue: Can't start server

**Solution:**

```bash
sudo lsof -i :8080
sudo kill -9 <PID>
./build/kv-server
```

### Issue: Load generator times out

**Solution:**

```bash
# Increase timeout or reduce threads
./load-generator --timeout 10000 -t 5 -d 60 -w get_all
```

### Issue: Numbers don't match exactly

**Explanation:** "There's natural variation due to [system load, network, etc.]. The value is within [X]% which shows the same trend and bottleneck."

### Issue: TA asks to run longer

**Solution:**

```bash
# Already prepared with longer duration
./load-generator -h <server_ip> -p 8080 -t 10 -d 600 -w get_all
```

---

## Success Criteria

### You'll Get Full Marks If:

**Graphs (3+3=6 marks):**

- ✅ Throughput clearly increases then plateaus
- ✅ Response time stays low then increases
- ✅ Resource utilization shows bottleneck
- ✅ Two workloads show different bottlenecks

**Reproduction (3+3=6 marks):**

- ✅ Can run load test on command
- ✅ Results match graphs within reasonable variance
- ✅ Can explain any differences

**Guidelines (4+4=8 marks):**

- ✅ Load generator is properly implemented
- ✅ Resources are separated correctly
- ✅ Tested at 5+ load levels
- ✅ Ran for 5+ minutes per test
- ✅ Reached steady state
- ✅ Load gen generates enough load

---

## Final Tips

1. **Be confident**: You have solid implementation
2. **Know your numbers**: Memorize key metrics
3. **Explain clearly**: Practice explaining bottlenecks
4. **Have commands ready**: Copy-paste for speed
5. **Show monitoring**: Proves your claims
6. **Stay calm**: Even if something doesn't work perfectly
7. **Have backup**: Know how to quickly restart/retry

---

## Time Management

Typical demo is 15-20 minutes:

- **5 min**: Show report and graphs
- **5 min**: Reproduce 2-3 data points
- **5 min**: Verify guidelines (show code, setup, logs)
- **5 min**: Questions and discussion

**Practice** running through this checklist beforehand!

---

## Contact Info to Have Ready

- Your name, roll number
- Partner's name (if applicable)
- Report file ready to show
- All graphs in easily accessible folder

---

## Good Luck! 🎯

You're well-prepared with:

- ✅ Complete implementation
- ✅ Thorough documentation
- ✅ Clear results
- ✅ This checklist

You've got this! 💪
