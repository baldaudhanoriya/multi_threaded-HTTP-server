#ifndef DB_H
#define DB_H

#include <mysql/mysql.h>
#include <string>
#include <vector>
#include <mutex>
#include <iostream>
#include <sstream>
#include <iomanip>
#include "../include/config.h"

using namespace std;

// helper function to compute SHA256-like hash for text (simple version)
inline string compute_text_hash(const string &text)
{
    // Simple hash function (not cryptographic, but sufficient for DB key)
    uint64_t h1 = 0, h2 = 0;
    for (size_t i = 0; i < text.length(); i++)
    {
        h1 = h1 * 31 + text[i];
        h2 = h2 * 37 + text[i];
    }
    stringstream ss;
    ss << hex << setfill('0') << setw(16) << h1 << setw(16) << h2;
    return ss.str();
}

// database connection pool
class DB
{
private:
    vector<MYSQL *> pool;
    mutex mtx;

public:
    DB()
    {
        // create connections
        for (int i = 0; i < Config::DB_POOL; i++)
        {
            MYSQL *conn = mysql_init(nullptr);
            if (!conn)
            {
                cerr << "mysql_init failed\n";
                continue;
            }

            if (!mysql_real_connect(conn, Config::DB_HOST.c_str(),
                                    Config::DB_USER.c_str(),
                                    Config::DB_PASS.c_str(),
                                    Config::DB_NAME.c_str(),
                                    Config::DB_PORT, nullptr, 0))
            {
                cerr << "DB connect failed: " << mysql_error(conn) << "\n";
                mysql_close(conn);
                continue;
            }

            pool.push_back(conn);
        }

        cout << "DB pool created: " << pool.size() << " connections\n";
    }

    ~DB()
    {
        for (auto conn : pool)
        {
            mysql_close(conn);
        }
    }

    // get connection from pool
    MYSQL *get_conn()
    {
        lock_guard<mutex> lock(mtx);
        if (pool.empty())
            return nullptr;
        MYSQL *conn = pool.back();
        pool.pop_back();
        return conn;
    }

    // return connection to pool
    void return_conn(MYSQL *conn)
    {
        if (!conn)
            return;
        lock_guard<mutex> lock(mtx);
        pool.push_back(conn);
    }

    // insert or update
    bool put(const string &key, const string &val)
    {
        MYSQL *conn = get_conn();
        if (!conn)
            return false;

        char esc_key[512], esc_val[1024];
        mysql_real_escape_string(conn, esc_key, key.c_str(), key.length());
        mysql_real_escape_string(conn, esc_val, val.c_str(), val.length());

        string query = "INSERT INTO kv_pairs (kv_key, kv_value) VALUES ('" +
                       string(esc_key) + "', '" + string(esc_val) +
                       "') ON DUPLICATE KEY UPDATE kv_value='" + string(esc_val) + "'";

        bool ok = mysql_query(conn, query.c_str()) == 0;
        return_conn(conn);
        return ok;
    }

    // get value by key
    bool get(const string &key, string &val)
    {
        MYSQL *conn = get_conn();
        if (!conn)
            return false;

        char esc_key[512];
        mysql_real_escape_string(conn, esc_key, key.c_str(), key.length());

        string query = "SELECT kv_value FROM kv_pairs WHERE kv_key='" +
                       string(esc_key) + "'";

        bool found = false;
        if (mysql_query(conn, query.c_str()) == 0)
        {
            MYSQL_RES *res = mysql_store_result(conn);
            if (res)
            {
                MYSQL_ROW row = mysql_fetch_row(res);
                if (row && row[0])
                {
                    val = row[0];
                    found = true;
                }
                mysql_free_result(res);
            }
        }

        return_conn(conn);
        return found;
    }

    // delete by key
    bool del(const string &key)
    {
        MYSQL *conn = get_conn();
        if (!conn)
            return false;

        char esc_key[512];
        mysql_real_escape_string(conn, esc_key, key.c_str(), key.length());

        string query = "DELETE FROM kv_pairs WHERE kv_key='" + string(esc_key) + "'";

        bool ok = mysql_query(conn, query.c_str()) == 0;
        return_conn(conn);
        return ok;
    }

    // insert or update hash (text -> hash value)
    bool put_hash(const string &text, uint32_t hash)
    {
        MYSQL *conn = get_conn();
        if (!conn)
            return false;

        // Compute text_hash for indexing
        string text_hash = compute_text_hash(text);

        // Get text prefix (first 255 chars)
        string text_prefix = text.substr(0, 255);

        char esc_text[4096];
        char esc_prefix[512];
        mysql_real_escape_string(conn, esc_text, text.c_str(), text.length());
        mysql_real_escape_string(conn, esc_prefix, text_prefix.c_str(), text_prefix.length());

        string query = "INSERT INTO hash_store (text_prefix, text_hash, text, hash_value) VALUES ('" +
                       string(esc_prefix) + "', '" + text_hash + "', '" + string(esc_text) + "', " + to_string(hash) +
                       ") ON DUPLICATE KEY UPDATE hash_value=" + to_string(hash);

        bool ok = mysql_query(conn, query.c_str()) == 0;
        return_conn(conn);
        return ok;
    }

    // get hash by text
    bool get_hash(const string &text, uint32_t &hash)
    {
        MYSQL *conn = get_conn();
        if (!conn)
            return false;

        // Compute text_hash for quick filtering
        string text_hash = compute_text_hash(text);
        string text_prefix = text.substr(0, 255);

        char esc_text[4096];
        char esc_prefix[512];
        mysql_real_escape_string(conn, esc_text, text.c_str(), text.length());
        mysql_real_escape_string(conn, esc_prefix, text_prefix.c_str(), text_prefix.length());

        // Query uses hash for fast filtering, then exact text match to handle collisions
        string query = "SELECT hash_value FROM hash_store WHERE text_prefix='" +
                       string(esc_prefix) + "' AND text_hash='" + text_hash +
                       "' AND text='" + string(esc_text) + "'";

        bool found = false;
        if (mysql_query(conn, query.c_str()) == 0)
        {
            MYSQL_RES *res = mysql_store_result(conn);
            if (res)
            {
                MYSQL_ROW row = mysql_fetch_row(res);
                if (row && row[0])
                {
                    hash = stoul(row[0]);
                    found = true;
                }
                mysql_free_result(res);
            }
        }

        return_conn(conn);
        return found;
    }
};

#endif
