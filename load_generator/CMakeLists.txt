# Load Generator build file
cmake_minimum_required(VERSION 3.10)
project(LoadGenerator)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -pthread")

# Find threads
find_package(Threads REQUIRED)

# Build load generator executable
add_executable(load-generator load_generator.cpp)
target_link_libraries(load-generator Threads::Threads)
