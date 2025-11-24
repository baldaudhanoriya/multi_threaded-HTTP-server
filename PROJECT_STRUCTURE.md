# Project Organization Summary

All load generator files have been moved to the `load_generator/` directory for better organization.

## New Structure

```
multi_threaded-HTTP-server/
├── server/                    # Server implementation
├── cache/                     # Cache implementation
├── db/                        # Database layer
├── include/                   # Headers and config
├── build/                     # Server build output
├── main.cpp                   # Server entry point
├── CMakeLists.txt            # Server build config
├── Makefile                  # Convenience build commands
├── setup_mysql.sh            # Database setup script
├── README.md                 # Main project README
│
└── load_generator/           # ALL LOAD TESTING FILES
    ├── load_generator.cpp           # Load generator source
    ├── CMakeLists.txt               # Load gen build config
    ├── build.sh                     # Build script
    ├── run_experiments.sh           # Automated experiments
    ├── monitor_resources.sh         # Resource monitoring
    ├── parse_results.py            # Results parser
    ├── plot_results.py             # Graph generator
    ├── README.md                    # Load gen README
    ├── QUICK_START.md              # Quick reference
    ├── README_LOAD_TESTING.md      # Complete guide
    ├── IMPLEMENTATION_SUMMARY.md   # Implementation details
    ├── REPORT_TEMPLATE.md          # Report template
    └── DEMO_CHECKLIST.md           # Demo preparation
```

## Key Changes

1. **All load testing files** moved to `load_generator/` directory
2. **Updated Makefile** to build in new structure
3. **Updated main README.md** to reference new structure
4. **Created load_generator/README.md** with local documentation

## How to Use

### Build Everything

```bash
# From project root
make all

# Or separately
make server    # Builds KV server
make loadgen   # Builds load generator
```

### Run Server

```bash
cd build
./kv-server
```

### Run Load Tests

```bash
cd load_generator

# Single test
./load-generator -h 127.0.0.1 -p 8080 -t 10 -d 60 -w get_all

# Full experiments
./run_experiments.sh get_all 127.0.0.1 8080

# Analyze
python3 parse_results.py results_get_all_*/
python3 plot_results.py results_get_all_*/summary.csv
```

## Documentation Locations

- **Server docs**: Main `README.md` in project root
- **Load testing docs**: All in `load_generator/` directory
  - Quick start: `load_generator/QUICK_START.md`
  - Full guide: `load_generator/README_LOAD_TESTING.md`
  - Demo prep: `load_generator/DEMO_CHECKLIST.md`

## Benefits

- ✅ Clear separation of server and testing components
- ✅ Easier to navigate project
- ✅ Load generator can be distributed separately if needed
- ✅ All testing documentation in one place
- ✅ Cleaner project root directory
