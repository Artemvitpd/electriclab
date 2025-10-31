"""
Randomized 5-file, 50-access benchmark with system info.

Phases:
1) Baseline: direct file reads (no cache), randomized 50 accesses over 5 files.
2) Cache: prime cold cache via get_from_cache(), then 50 randomized cached accesses.

Reports:
- System info (CPU, RAM, disk, Python)
- Per-phase aggregate throughput and average latency
- Per-file hit distribution
"""

import os
import sys
import time
import platform
import tempfile
import random
from pathlib import Path
from typing import List, Tuple

import commercial_service as com


def system_info() -> dict:
    info = {
        "python": sys.version.split(" ")[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
    }
    try:
        import psutil  # optional

        vm = psutil.virtual_memory()
        info["memory_total_gb"] = round(vm.total / (1024 ** 3), 2)
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "device": part.device,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / (1024 ** 3), 2),
                })
            except Exception:
                pass
        info["disks"] = disks
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            info["cpu_mhz"] = int(cpu_freq.current)
        info["cpu_count"] = psutil.cpu_count(logical=True)
    except Exception:
        pass
    return info


def gen_files(dir_path: str, count: int = 5, size_mb: int = 8) -> List[str]:
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    files = []
    for i in range(count):
        name = f"file_{i+1}.bin"
        path = str(Path(dir_path) / name)
        with open(path, "wb") as f:
            f.write(os.urandom(size_mb * 1024 * 1024))
        files.append(name)
    return files


def random_access_read(dir_path: str, files: List[str], total_ops: int = 50) -> Tuple[float, float]:
    rnd = random.Random(42)
    start = time.perf_counter()
    lat_sum = 0.0
    for _ in range(total_ops):
        name = rnd.choice(files)
        t0 = time.perf_counter()
        with open(str(Path(dir_path) / name), "rb") as f:
            _ = f.read()  # read full file to be comparable with decrypt path
        lat_sum += (time.perf_counter() - t0)
    dur = time.perf_counter() - start
    return dur, (lat_sum / total_ops)


def random_access_cached(src_dir: str, cache_dir: str, files: List[str], total_ops: int = 50) -> Tuple[float, float]:
    rnd = random.Random(42)
    # cold prime
    for name in files:
        com.SOURCE_DIR = src_dir
        com.CACHE_DIR = cache_dir
        com.get_from_cache(name)
    # random warm accesses
    start = time.perf_counter()
    lat_sum = 0.0
    for _ in range(total_ops):
        name = rnd.choice(files)
        t0 = time.perf_counter()
        path = com.get_from_cache(name)
        # simulate serving decrypted content like API would
        with open(path, "rb") as f:
            enc = f.read()
        _ = com.aes_decrypt(enc)
        lat_sum += (time.perf_counter() - t0)
    dur = time.perf_counter() - start
    return dur, (lat_sum / total_ops)


def main():
    print("Collecting system info...")
    info = system_info()
    for k, v in info.items():
        print(f"{k}: {v}")

    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as cache:
        os.environ["HYBRIDCACHE_SOURCE"] = src
        os.environ["HYBRIDCACHE_DIR"] = cache
        files = gen_files(src, count=5, size_mb=8)

        print("\nBaseline: direct randomized reads...")
        dur_base, avg_lat_base = random_access_read(src, files, total_ops=50)
        print(f"Baseline total: {dur_base:.3f}s, avg latency: {avg_lat_base*1000:.2f} ms")

        print("\nCached: randomized reads via get_from_cache...")
        dur_cache, avg_lat_cache = random_access_cached(src, cache, files, total_ops=50)
        print(f"Cached total: {dur_cache:.3f}s, avg latency: {avg_lat_cache*1000:.2f} ms")

        improvement = (dur_base - dur_cache) / max(dur_base, 1e-9) * 100.0
        print(f"\nTotal time improvement: {improvement:.1f}%")


if __name__ == "__main__":
    main()


