#!/bin/bash

# Resource Monitoring Script
# Monitors CPU, Memory, Disk I/O during a single load test

if [ $# -lt 3 ]; then
    echo "Usage: $0 <server_pid> <mysql_pid> <output_csv>"
    exit 1
fi

SERVER_PID=$1
MYSQL_PID=$2
OUTPUT_CSV=$3
INTERVAL=1  # Sample every 1 second

# CSV header
echo "timestamp,server_cpu,server_mem_mb,server_threads,mysql_cpu,mysql_mem_mb,mysql_threads,system_cpu_user,system_cpu_system,system_cpu_idle,disk_read_kb,disk_write_kb" > "$OUTPUT_CSV"

# Get total memory once
TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')

while true; do
    TIMESTAMP=$(date +%s)
    
    # Server metrics
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        SERVER_STATS=$(ps -p $SERVER_PID -o %cpu,%mem,nlwp --no-headers)
        SERVER_CPU=$(echo $SERVER_STATS | awk '{print $1}')
        SERVER_MEM_PCT=$(echo $SERVER_STATS | awk '{print $2}')
        SERVER_THREADS=$(echo $SERVER_STATS | awk '{print $3}')
        SERVER_MEM_MB=$(echo "scale=2; $SERVER_MEM_PCT * $TOTAL_MEM_KB / 102400" | bc)
    else
        SERVER_CPU=0
        SERVER_MEM_MB=0
        SERVER_THREADS=0
    fi
    
    # MySQL metrics
    if [ "$MYSQL_PID" != "0" ] && ps -p $MYSQL_PID > /dev/null 2>&1; then
        MYSQL_STATS=$(ps -p $MYSQL_PID -o %cpu,%mem,nlwp --no-headers)
        MYSQL_CPU=$(echo $MYSQL_STATS | awk '{print $1}')
        MYSQL_MEM_PCT=$(echo $MYSQL_STATS | awk '{print $2}')
        MYSQL_THREADS=$(echo $MYSQL_STATS | awk '{print $3}')
        MYSQL_MEM_MB=$(echo "scale=2; $MYSQL_MEM_PCT * $TOTAL_MEM_KB / 102400" | bc)
    else
        MYSQL_CPU=0
        MYSQL_MEM_MB=0
        MYSQL_THREADS=0
    fi
    
    # System-wide CPU (get average from previous second)
    CPU_STATS=$(mpstat 1 1 | grep "Average:" | awk '{print $(NF-7), $(NF-5), $NF}')
    if [ -z "$CPU_STATS" ]; then
        CPU_USER=0
        CPU_SYS=0
        CPU_IDLE=100
    else
        CPU_USER=$(echo $CPU_STATS | awk '{print $1}')
        CPU_SYS=$(echo $CPU_STATS | awk '{print $2}')
        CPU_IDLE=$(echo $CPU_STATS | awk '{print $3}')
    fi
    
    # Disk I/O (get average from 1 second interval)
    DISK_STATS=$(iostat -d -k 1 2 | grep -A1 "^Device" | tail -1)
    if [ -z "$DISK_STATS" ]; then
        DISK_READ_KB=0
        DISK_WRITE_KB=0
    else
        DISK_READ_KB=$(echo $DISK_STATS | awk '{print $5}')
        DISK_WRITE_KB=$(echo $DISK_STATS | awk '{print $6}')
    fi
    
    # Write to CSV
    echo "$TIMESTAMP,$SERVER_CPU,$SERVER_MEM_MB,$SERVER_THREADS,$MYSQL_CPU,$MYSQL_MEM_MB,$MYSQL_THREADS,$CPU_USER,$CPU_SYS,$CPU_IDLE,$DISK_READ_KB,$DISK_WRITE_KB" >> "$OUTPUT_CSV"
    
    sleep $INTERVAL
done
        echo "MySQL Threads:" | tee -a "$OUTPUT_FILE"
        mysql -u root -e "SHOW STATUS LIKE 'Threads%';" 2>/dev/null | tee -a "$OUTPUT_FILE" || echo "MySQL not accessible" | tee -a "$OUTPUT_FILE"
        echo "" | tee -a "$OUTPUT_FILE"
    fi
    
    # Server cache stats (if server is running)
    if curl -s http://localhost:8080/status &> /dev/null; then
        echo "Server Cache Stats:" | tee -a "$OUTPUT_FILE"
        curl -s http://localhost:8080/status | python3 -m json.tool 2>/dev/null | tee -a "$OUTPUT_FILE" || echo "Server stats not available" | tee -a "$OUTPUT_FILE"
        echo "" | tee -a "$OUTPUT_FILE"
    fi
    
    # Wait before next snapshot
    sleep 10
done
