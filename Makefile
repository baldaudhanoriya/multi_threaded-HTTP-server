# Makefile for KV Store Server and Load Generator

.PHONY: all server loadgen clean test help

# Compiler settings
CXX = g++
CXXFLAGS = -std=c++17 -Wall -O3 -pthread

# MySQL settings
MYSQL_CONFIG = mysql_config
MYSQL_CFLAGS = $(shell $(MYSQL_CONFIG) --include 2>/dev/null)
MYSQL_LIBS = $(shell $(MYSQL_CONFIG) --libs 2>/dev/null)

# Targets
all: server loadgen

server:
	@echo "Building KV Store Server..."
	@mkdir -p build
	@cd build && cmake .. && make
	@echo "✓ Server built: build/kv-server"

loadgen:
	@echo "Building Load Generator..."
	@cd load_generator && $(CXX) $(CXXFLAGS) -o load-generator load_generator.cpp
	@echo "✓ Load generator built: load_generator/load-generator"

clean:
	@echo "Cleaning build files..."
	@rm -rf build load_generator/load-generator
	@rm -rf load_generator/results_*
	@echo "✓ Clean complete"

test: loadgen
	@echo "Running quick test (10 threads, 30 seconds)..."
	@cd load_generator && ./load-generator -h 127.0.0.1 -p 8080 -t 10 -d 30 -w get_all

scripts:
	@echo "Making scripts executable..."
	@chmod +x load_generator/build.sh load_generator/run_experiments.sh load_generator/monitor_resources.sh
	@echo "✓ Scripts are now executable"

help:
	@echo "KV Store Project - Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make all       - Build server and load generator"
	@echo "  make server    - Build KV store server only"
	@echo "  make loadgen   - Build load generator only"
	@echo "  make clean     - Remove all build files"
	@echo "  make test      - Run quick load test"
	@echo "  make scripts   - Make shell scripts executable"
	@echo "  make help      - Show this help message"
	@echo ""
	@echo "After building:"
	@echo "  1. Start server:    cd build && ./kv-server"
	@echo "  2. Run load test:   cd load_generator && ./load-generator -t 10 -d 60 -w get_all"
	@echo "  3. Full experiments: cd load_generator && ./run_experiments.sh get_all 127.0.0.1 8080"
