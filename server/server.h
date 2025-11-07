#ifndef SERVER_H
#define SERVER_H

#include <string>
#include "../include/httplib.h"
#include "../cache/cache.h"
#include "../db/db.h"

using namespace std;

// simple http server
class Server
{
private:
    httplib::Server srv;
    Cache *cache;
    Cache *hash_cache; // separate cache for hash computations
    DB *db;

public:
    Server(Cache *c, Cache *hc, DB *d) : cache(c), hash_cache(hc), db(d)
    {
        setup();
    }

    void setup()
    {
        // create key-value
        srv.Post("/kv/create", [this](const httplib::Request &req, httplib::Response &res)
                 {
            cout << "\n[REQUEST] POST /kv/create from " << req.remote_addr << endl;
            
            string key, val;
            
            // try query params first
            if (req.has_param("key") && req.has_param("value")) {
                key = req.get_param_value("key");
                val = req.get_param_value("value");
            }
            
            cout << "  Key: '" << key << "', Value: '" << val << "'" << endl;
            
            if (key.empty()) {
                cout << "  [ERROR] Missing key" << endl;
                res.status = 400;
                res.set_content("{\"error\": \"missing key\"}", "application/json");
                cout << "  [RESPONSE] 400 Bad Request" << endl;
                return;
            }
            
            // check if key already exists
            string old_val;
            bool key_exists = db->get(key, old_val);
            
            // write to db first
            cout << "  Writing to database..." << endl;
            if (!db->put(key, val)) {
                cout << "  [ERROR] Database write failed" << endl;
                res.status = 500;
                res.set_content("{\"error\": \"db error\"}", "application/json");
                cout << "  [RESPONSE] 500 Internal Error" << endl;
                return;
            }
            
            if (key_exists) {
                cout << "  ✓ Key OVERWRITTEN in database (old: '" << old_val << "' -> new: '" << val << "')" << endl;
            } else {
                cout << "  ✓ New key written to database" << endl;
            }
            
            // then cache
            cache->put(key, val);
            cout << "  ✓ Written to cache" << endl;
            
            string response_msg = key_exists ? "Key overwritten" : "Key created";
            // build JSON response with overwritten flag and old_value when applicable
            string json = "{\"success\": true, \"message\": \"" + response_msg + "\", \"key\": \"" + key + "\", \"value\": \"" + val + "\", \"overwritten\": ";
            json += (key_exists ? "true" : "false");
            if (key_exists) {
                json += ", \"old_value\": \"" + old_val + "\"";
            }
            json += "}";

            res.status = 201;
            res.set_content(json, "application/json");
            cout << "  [RESPONSE] 201 Created - " << response_msg << endl; });

        // read key-value
        srv.Get("/kv/read", [this](const httplib::Request &req, httplib::Response &res)
                {
            cout << "\n[REQUEST] GET /kv/read from " << req.remote_addr << endl;
            
            if (!req.has_param("key")) {
                cout << "  [ERROR] Missing key parameter" << endl;
                res.status = 400;
                res.set_content("{\"error\": \"missing key\"}", "application/json");
                cout << "  [RESPONSE] 400 Bad Request" << endl;
                return;
            }
            
            string key = req.get_param_value("key");
            string val;
            
            cout << "  Key: '" << key << "'" << endl;
            
            // check cache first
            cout << "  Checking cache..." << endl;
            if (cache->get(key, val)) {
                cout << "  ✓ CACHE HIT - Value: '" << val << "'" << endl;
                res.status = 200;
                res.set_content("{\"success\": true, \"key\": \"" + key + "\", \"value\": \"" + val + "\", \"source\": \"cache\"}", "application/json");
                cout << "  [RESPONSE] 200 OK (from cache)" << endl;
                return;
            }
            
            cout << "  ✗ Cache miss, checking database..." << endl;
            
            // check db
            if (db->get(key, val)) {
                cout << "  ✓ Found in database - Value: '" << val << "'" << endl;
                cache->put(key, val);  // fill cache
                cout << "  ✓ Cached for future requests" << endl;
                res.status = 200;
                res.set_content("{\"success\": true, \"key\": \"" + key + "\", \"value\": \"" + val + "\", \"source\": \"database\"}", "application/json");
                cout << "  [RESPONSE] 200 OK (from database)" << endl;
                return;
            }
            
            cout << "  ✗ Key not found in database" << endl;
            
            res.status = 404;
            res.set_content("{\"error\": \"Key not found\", \"key\": \"" + key + "\"}", "application/json");
            cout << "  [RESPONSE] 404 Not Found" << endl; });

        // delete key-value
        srv.Delete("/kv/delete", [this](const httplib::Request &req, httplib::Response &res)
                   {
            cout << "\n[REQUEST] DELETE /kv/delete from " << req.remote_addr << endl;
            
            if (!req.has_param("key")) {
                cout << "  [ERROR] Missing key parameter" << endl;
                res.status = 400;
                res.set_content("{\"error\": \"missing key\"}", "application/json");
                cout << "  [RESPONSE] 400 Bad Request" << endl;
                return;
            }
            
            string key = req.get_param_value("key");
            cout << "  Key: '" << key << "'" << endl;
            
            cout << "  Deleting from database..." << endl;
            db->del(key);
            cout << "  Deleting from cache..." << endl;
            cache->remove(key);
            
            cout << "  ✓ Deleted from both database and cache" << endl;
            res.status = 200;
            res.set_content("{\"success\": true, \"message\": \"Deleted\", \"key\": \"" + key + "\"}", "application/json");
            cout << "  [RESPONSE] 200 OK" << endl; });

        // get primes
        srv.Get("/compute/prime", [](const httplib::Request &req, httplib::Response &res)
                {
            cout << "\n[REQUEST] GET /compute/prime from " << req.remote_addr << endl;
            
            int n = 10;
            if (req.has_param("count")) {
                n = stoi(req.get_param_value("count"));
            }
            if (n > 10000) n = 10000;
            
            cout << "  Computing first " << n << " prime numbers..." << endl;
            
            string result;
            int count = 0, num = 2;
            while (count < n) {
                bool is_prime = true;
                for (int i = 2; i * i <= num; i++) {
                    if (num % i == 0) {
                        is_prime = false;
                        break;
                    }
                }
                if (is_prime) {
                    if (count > 0) result += ",";
                    result += to_string(num);
                    count++;
                }
                num++;
            }
            
            cout << "  ✓ Computed " << n << " primes" << endl;
            res.status = 200;
            res.set_content("{\"success\": true, \"count\": " + to_string(n) + ", \"primes\": \"" + result + "\"}", "application/json");
            cout << "  [RESPONSE] 200 OK" << endl; });

        // compute hash
        srv.Get("/compute/hash", [this](const httplib::Request &req, httplib::Response &res)
                {
            cout << "\n[REQUEST] GET /compute/hash from " << req.remote_addr << endl;
            
            if (!req.has_param("text")) {
                cout << "  [ERROR] Missing text parameter" << endl;
                res.status = 400;
                res.set_content("{\"error\": \"missing text\"}", "application/json");
                cout << "  [RESPONSE] 400 Bad Request" << endl;
                return;
            }
            
            string text = req.get_param_value("text");
            cout << "  Text: '" << text << "'" << endl;
            
            // check hash cache first
            string cached_hash_str;
            cout << "  Checking hash cache..." << endl;
            if (hash_cache->get(text, cached_hash_str)) {
                cout << "  ✓ HASH CACHE HIT - Hash: " << cached_hash_str << endl;
                res.status = 200;
                res.set_content("{\"success\": true, \"text\": \"" + text + "\", \"hash\": " + cached_hash_str + ", \"source\": \"cache\"}", "application/json");
                cout << "  [RESPONSE] 200 OK (from hash cache)" << endl;
                return;
            }
            
            cout << "  ✗ Hash cache miss, checking database..." << endl;
            
            // check db for previously computed hash
            uint32_t db_hash;
            if (db->get_hash(text, db_hash)) {
                cout << "  ✓ Found in database - Hash: " << db_hash << endl;
                hash_cache->put(text, to_string(db_hash));  // cache for future
                cout << "  ✓ Cached for future requests" << endl;
                res.status = 200;
                res.set_content("{\"success\": true, \"text\": \"" + text + "\", \"hash\": " + to_string(db_hash) + ", \"source\": \"database\"}", "application/json");
                cout << "  [RESPONSE] 200 OK (from database)" << endl;
                return;
            }
            
            cout << "  ✗ Not found in database, computing hash..." << endl;
            
            // compute hash (not in cache or db)
            uint32_t h = 0;
            for (char c : text) {
                h = h * 31 + c;
            }
            
            cout << "  ✓ Hash computed: " << h << endl;
            
            // store in db and cache
            cout << "  Writing to database..." << endl;
            db->put_hash(text, h);
            cout << "  ✓ Written to database" << endl;
            
            hash_cache->put(text, to_string(h));
            cout << "  ✓ Written to hash cache" << endl;
            
            res.status = 200;
            res.set_content("{\"success\": true, \"text\": \"" + text + "\", \"hash\": " + to_string(h) + ", \"source\": \"computed\"}", "application/json");
            cout << "  [RESPONSE] 200 OK (newly computed)" << endl; });

        // status
        srv.Get("/status", [this](const httplib::Request &req, httplib::Response &res)
                {
            cout << "\n[REQUEST] GET /status from " << req.remote_addr << endl;
            
            string json = "{\"success\": true, \"data\": {";
            json += "\"server\": \"running\", ";
            json += "\"kv_cache_size\": " + to_string(cache->size()) + ", ";
            json += "\"kv_cache_hits\": " + to_string(cache->get_hits()) + ", ";
            json += "\"kv_cache_misses\": " + to_string(cache->get_misses()) + ", ";
            json += "\"kv_cache_hit_rate\": " + to_string(cache->hit_rate()) + ", ";
            json += "\"kv_cache_evictions\": " + to_string(cache->get_evictions()) + ", ";
            json += "\"hash_cache_size\": " + to_string(hash_cache->size()) + ", ";
            json += "\"hash_cache_hits\": " + to_string(hash_cache->get_hits()) + ", ";
            json += "\"hash_cache_misses\": " + to_string(hash_cache->get_misses()) + ", ";
            json += "\"hash_cache_hit_rate\": " + to_string(hash_cache->hit_rate()) + ", ";
            json += "\"hash_cache_evictions\": " + to_string(hash_cache->get_evictions());
            json += "}}";
            
            cout << "  KV Cache: " << cache->size() << " items, "
                      << cache->get_hits() << " hits, "
                      << cache->get_misses() << " misses ("
                      << cache->hit_rate() << "% hit rate)" << endl;
            cout << "  Hash Cache: " << hash_cache->size() << " items, "
                      << hash_cache->get_hits() << " hits, "
                      << hash_cache->get_misses() << " misses ("
                      << hash_cache->hit_rate() << "% hit rate)" << endl;
            
            res.status = 200;
            res.set_content(json, "application/json");
            cout << "  [RESPONSE] 200 OK" << endl; });

        // generic error / not-found handler - return helpful JSON for bad endpoints
        srv.set_error_handler([](const httplib::Request &req, httplib::Response &res)
                              {
            cout << "\n[REQUEST] " << req.method << " " << req.path << " from " << req.remote_addr << endl;
            int status = res.status ? res.status : 404;
            res.status = status;

            string hint = "Valid endpoints: /kv/create (POST), /kv/read (GET), /kv/delete (DELETE), /compute/prime (GET), /compute/hash (GET), /status (GET)";
            string json = "{\"error\": \"endpoint not found\", \"method\": \"" + req.method + "\", \"path\": \"" + req.path + "\", \"status\": " + to_string(status) + ", \"hint\": \"" + hint + "\"}";
            res.set_content(json, "application/json");
            cout << "  [RESPONSE] " << status << " Not Found (handled)" << endl; });

        // exception handler to return JSON 500 on unexpected exceptions
        srv.set_exception_handler([](const httplib::Request &req, httplib::Response &res, exception_ptr ep)
                                  {
            try {
                if (ep) rethrow_exception(ep);
            } catch (const exception &e) {
                cerr << "[EXCEPTION] " << e.what() << endl;
            } catch (...) {
                cerr << "[EXCEPTION] unknown" << endl;
            }
            res.status = 500;
            res.set_content("{\"error\": \"internal server error\"}", "application/json"); });
    }

    void run()
    {
        cout << "\n========================================" << endl;
        cout << "Starting server on port " << Config::PORT << "..." << endl;
        cout << "========================================" << endl;
        cout.flush();

        srv.new_task_queue = []
        { return new httplib::ThreadPool(Config::THREADS); };

        // This is a BLOCKING call - server runs here
        // When successful, it blocks forever until stopped
        if (!srv.listen(Config::HOST.c_str(), Config::PORT))
        {
            cerr << "\n[ERROR] Failed to start server!" << endl;
            cerr << "Possible reasons:" << endl;
            cerr << "  - Port " << Config::PORT << " is already in use" << endl;
            cerr << "  - No permission to bind to port" << endl;
            cerr << "\nCheck: sudo lsof -i :" << Config::PORT << endl;
            return;
        }

        cout << "\nServer stopped gracefully." << endl;
    }

    void stop()
    {
        srv.stop();
    }
};

#endif
