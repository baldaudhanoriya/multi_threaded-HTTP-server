# Simple build file
cmake_minimum_required(VERSION 3.10)
project(KVStore)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")

# find mysql
find_program(MYSQL_CONFIG mysql_config)
if(NOT MYSQL_CONFIG)
    message(FATAL_ERROR "mysql_config not found")
endif()

execute_process(COMMAND ${MYSQL_CONFIG} --include OUTPUT_VARIABLE MYSQL_INC OUTPUT_STRIP_TRAILING_WHITESPACE)
execute_process(COMMAND ${MYSQL_CONFIG} --libs OUTPUT_VARIABLE MYSQL_LIBS OUTPUT_STRIP_TRAILING_WHITESPACE)

string(REPLACE "-I" "" MYSQL_INC_DIR "${MYSQL_INC}")
include_directories(${MYSQL_INC_DIR})
include_directories(${PROJECT_SOURCE_DIR}/include)

# find threads
find_package(Threads REQUIRED)

# build executable
add_executable(kv-server main.cpp)
target_link_libraries(kv-server ${MYSQL_LIBS} Threads::Threads)
