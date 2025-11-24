#!/bin/bash

# Build script for Load Generator

echo "=========================================="
echo "Building Load Generator"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Build Load Generator
echo -e "${YELLOW}Building Load Generator...${NC}"
if g++ -std=c++17 -pthread -O3 -o load-generator load_generator.cpp; then
    echo -e "${GREEN}✓ Load generator built successfully: load-generator${NC}"
else
    echo -e "${RED}✗ Load generator build failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Build Complete!"
echo "==========================================${NC}"
echo "Load generator:       ./load-generator"
echo ""
echo "Usage:"
echo "  ./load-generator -h 127.0.0.1 -p 8080 -t 10 -d 60 -w get_all"
echo "  ./run_experiments.sh get_all 127.0.0.1 8080"
