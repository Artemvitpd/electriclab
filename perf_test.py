"""
Performance test for gov_service and commercial_service.

Measures:
- Encryption throughput (MB/s)
- Cache get_from_cache latency on warm and cold cache

Usage:
  python perf_test.py --service gov --iterations 50 --size_mb 10
  python perf_test.py --service commercial --iterations 50 --size_mb 10
"""

import os
import time
import tempfile
import random
import string
from pathlib import Path
import argparse

# Local imports without servers: import and call functions directly
import gov_service as gov
import commercial_service as com


def random_bytes(megabytes: int) -> bytes:
    return os.urandom(megabytes * 1024 * 1024)


def write_source_file(source_dir: str, name: str, data: bytes) -> str:
    Path(source_dir).mkdir(parents=True, exist_ok=True)
    path = str(Path(source_dir) / name)
    with open(path, "wb") as f:
        f.write(data)
    return path


def bench_encryption(service: str, size_mb: int, iterations: int) -> float:
    payload = random_bytes(size_mb)
    start = time.perf_counter()
    if service == "gov":
        for _ in range(iterations):
            e = gov.encrypt_data(payload)
            d = gov.decrypt_data(e)
            assert d == payload
    else:
        for _ in range(iterations):
            e = com.aes_encrypt(payload)
            d = com.aes_decrypt(e)
            assert d == payload
    dur = time.perf_counter() - start
    total_mb = size_mb * iterations
    return total_mb / dur


def bench_cache_latency(service: str, size_mb: int, iterations: int) -> tuple:
    with tempfile.TemporaryDirectory() as tmp_source, tempfile.TemporaryDirectory() as tmp_cache:
        os.environ["HYBRIDCACHE_SOURCE"] = tmp_source
        os.environ["HYBRIDCACHE_DIR"] = tmp_cache
        name = "bigfile.bin"
        write_source_file(tmp_source, name, random_bytes(size_mb))

        # First call: cold cache
        t0 = time.perf_counter()
        if service == "gov":
            gov.SOURCE_DIR = tmp_source
            gov.CACHE_DIR = tmp_cache
            path = gov.get_from_cache(name)
        else:
            com.SOURCE_DIR = tmp_source
            com.CACHE_DIR = tmp_cache
            path = com.get_from_cache(name)
        cold = time.perf_counter() - t0

        # Warm cache repeated
        t1 = time.perf_counter()
        for _ in range(iterations):
            if service == "gov":
                path = gov.get_from_cache(name)
            else:
                path = com.get_from_cache(name)
        warm = (time.perf_counter() - t1) / max(iterations, 1)

        return cold, warm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--service", choices=["gov", "commercial"], required=True)
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--size_mb", type=int, default=10)
    args = parser.parse_args()

    thr = bench_encryption(args.service, args.size_mb, args.iterations)
    cold, warm = bench_cache_latency(args.service, args.size_mb, max(args.iterations // 5, 1))

    print(f"Service: {args.service}")
    print(f"Encryption throughput: {thr:.2f} MB/s")
    print(f"Cold cache latency: {cold*1000:.1f} ms")
    print(f"Warm cache avg latency: {warm*1000:.1f} ms")


if __name__ == "__main__":
    main()



