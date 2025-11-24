#!/bin/bash

# Script to start KV Server pinned to CPU cores 3-9

echo "=========================================="
echo "Starting KV Server (pinned to cores 3-9)"
echo "=========================================="

# Check if server binary exists
if [ ! -f "build/kv-server" ]; then
    echo "Error: Server binary not found at build/kv-server"
    echo "Please build the server first:"
    echo "  cd build && cmake .. && make"
    exit 1
fi

# Check if server is already running
if pgrep -f "kv-server" > /dev/null; then
    echo "Warning: KV Server is already running"
    echo "Existing server PIDs:"
    pgrep -f "kv-server"
    echo ""
    read -p "Kill existing server and start new one? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Killing existing server..."
        pkill -9 -f "kv-server"
        sleep 1
    else
        echo "Exiting..."
        exit 1
    fi
fi

# Start server pinned to cores 3-9
echo "Starting server on cores 3-9..."
echo "Server will run in foreground (press Ctrl+C to stop)"
echo ""

taskset -c 3-9 ./build/kv-server
