#ifndef CONFIG_H
#define CONFIG_H

#include <string>

// basic config stuff
namespace Config
{
    const std::string HOST = "0.0.0.0";
    const int PORT = 8080;
    const int THREADS = 8;

    const std::string DB_HOST = "localhost";
    const int DB_PORT = 3306;
    const std::string DB_USER = "root";
    const std::string DB_PASS = "";
    const std::string DB_NAME = "kvstore_db";
    const int DB_POOL = 10;

    const int CACHE_SIZE = 1000;
    const int HASH_CACHE_SIZE = 500; // separate cache for hash computations
}

#endif
