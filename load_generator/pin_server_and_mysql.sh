#!/bin/bash

# Find PIDs
MYSQL_PID=$(pgrep -f mysqld)
SERVER_PID=$(pgrep -f kv-server)

echo "MySQL PID: $MYSQL_PID"
echo "Server PID: $SERVER_PID"

# Pin processes
sudo taskset -cp 0-2 $MYSQL_PID
sudo taskset -cp 3-9 $SERVER_PID

# Verify
echo "MySQL cores:"
taskset -p $MYSQL_PID
echo "Server cores:"
taskset -p $SERVER_PID