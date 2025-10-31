## HybridCache Services (Gov and Commercial)

Two ready-to-run services and a performance test:
- Gov (`gov_service.py`): GOST CTR via `pygost`, integrity checks, access counts, FastAPI.
- Commercial (`commercial_service.py`): AES-256 CTR via `cryptography`, integrity checks, FastAPI.
- Perf test (`perf_test.py`): throughput and cache latency benchmarks without running servers.

### Quick start (local)
1) Python 3.11 and pip install:
```
pip install -r requirements.txt
```
2) Run services:
```
python gov_service.py --host 0.0.0.0 --port 8080
python commercial_service.py --host 0.0.0.0 --port 8081
```
3) API endpoints:
- GET /api/cache/{filename}
- POST /api/preload { "files": ["file1.bin", "file2.bin"] }

Env vars:
- HYBRIDCACHE_DIR (default /cache)
- HYBRIDCACHE_SOURCE (default /source)
- HYBRIDCACHE_MAXSIZE (default 100 GiB)
- HYBRIDCACHE_TTL (default 7d)
- HYBRIDCACHE_ENCRYPTION ("1"|"0")
- Commercial only: HYBRIDCACHE_AES_KEY (Base64 32 bytes)

### Docker
Build and run both services:
```
docker compose up --build
```

Bind mounts:
- data/gov/cache and data/gov/source
- data/commercial/cache and data/commercial/source

Switch image service target:
```
docker build . -t hybridcache:gov --build-arg SERVICE=gov
docker run -p 8080:8080 -e HYBRIDCACHE_DIR=/cache -e HYBRIDCACHE_SOURCE=/source -v $(pwd)/data/gov/cache:/cache -v $(pwd)/data/gov/source:/source hybridcache:gov
```

### Performance test
Run without servers:
```
python perf_test.py --service gov --iterations 50 --size_mb 10
python perf_test.py --service commercial --iterations 50 --size_mb 10
```

### Notes
- Filename validation allows [A-Za-z0-9._-] and blocks path traversal.
- Integrity: per-file .sha256 stored in cache dir.
- Eviction: score = mtime + access_count*86400.
- For production, set secure locations for logs and rotate them.



