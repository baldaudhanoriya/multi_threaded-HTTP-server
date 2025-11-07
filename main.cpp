// Simple KV Store Server
// Multi-tier HTTP server with cache and database

#include <iostream>
#include <csignal>
#include "include/config.h"
#include "cache/cache.h"
#include "db/db.h"
#include "server/server.h"

using namespace std;

Server *global_srv = nullptr;

void handle_signal(int sig)
{
    cout << "\nShutting down...\n";
    if (global_srv)
    {
        global_srv->stop();
    }
    exit(0);
}

int main()
{
    cout << "=================================\n";
    cout << "  KV Store Server\n";
    cout << "=================================\n\n";

    // setup signal handler
    signal(SIGINT, handle_signal);

    // create KV cache
    Cache cache(Config::CACHE_SIZE);
    cout << "KV Cache created (size=" << Config::CACHE_SIZE << ")\n";

    // create Hash cache
    Cache hash_cache(Config::HASH_CACHE_SIZE);
    cout << "Hash Cache created (size=" << Config::HASH_CACHE_SIZE << ")\n";

    // create db pool
    DB db;

    // create server
    Server srv(&cache, &hash_cache, &db);
    global_srv = &srv;

    cout << "Ready to start on http://" << Config::HOST << ":" << Config::PORT << "\n";
    cout << "Press Ctrl+C to stop\n";

    // start server (blocking - will show logs when requests come in)
    srv.run();

    return 0;
}
