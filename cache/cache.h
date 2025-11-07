#ifndef CACHE_H
#define CACHE_H

#include <string>
#include <unordered_map>
#include <list>
#include <mutex>

using namespace std;

// simple LRU cache
class Cache
{
private:
    struct Node
    {
        string k;
        string v;
    };

    int max_size;
    list<Node> items;
    unordered_map<string, list<Node>::iterator> map;
    mutex mtx;

    int hits = 0;
    int misses = 0;
    int evicts = 0;

public:
    Cache(int size) : max_size(size) {}

    // get value from cache
    bool get(const string &key, string &val)
    {
        lock_guard<mutex> lock(mtx);

        auto it = map.find(key);
        if (it == map.end())
        {
            misses++;
            return false;
        }

        // move to front
        items.splice(items.begin(), items, it->second);
        val = it->second->v;
        hits++;
        return true;
    }

    // add to cache
    void put(const string &key, const string &val)
    {
        lock_guard<mutex> lock(mtx);

        auto it = map.find(key);
        if (it != map.end())
        {
            // update existing
            items.splice(items.begin(), items, it->second);
            it->second->v = val;
            return;
        }

        // check if full
        if (items.size() >= (size_t)max_size)
        {
            // remove last item
            auto last = items.back();
            map.erase(last.k);
            items.pop_back();
            evicts++;
        }

        // add new item
        items.push_front({key, val});
        map[key] = items.begin();
    }

    // remove from cache
    void remove(const string &key)
    {
        lock_guard<mutex> lock(mtx);

        auto it = map.find(key);
        if (it != map.end())
        {
            items.erase(it->second);
            map.erase(it);
        }
    }

    // get stats
    int size() { return items.size(); }
    int get_hits() { return hits; }
    int get_misses() { return misses; }
    int get_evictions() { return evicts; }
    double hit_rate()
    {
        int total = hits + misses;
        return total > 0 ? (double)hits / total * 100.0 : 0.0;
    }
};

#endif
