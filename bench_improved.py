"""
Improved benchmark per recommendations:
- 5 files with mixed sizes: 8, 16, 32, 64, 128 MB
- 100 randomized accesses (baseline vs warm cache)
- Baseline: direct full-file reads
- Cache: warm-up (measures cache write throughput), then warm randomized reads
- Reports throughput (MB/s) and average latency (ms) for both phases
"""

import os
import sys
import time
import platform
import tempfile
import random
from pathlib import Path
from typing import List, Tuple, Dict

import commercial_service as com


def system_info() -> Dict[str, str]:
    info = {
        "python": sys.version.split(" ")[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
    }
    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        info["memory_total_gb"] = f"{vm.total / (1024 ** 3):.2f}"
        cpu = psutil.cpu_freq()
        if cpu:
            info["cpu_mhz"] = f"{cpu.current:.0f}"
        info["cpu_count"] = str(psutil.cpu_count(logical=True))
    except Exception:
        pass
    return info


def gen_files(dir_path: str, sizes_mb: List[int]) -> List[str]:
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    files = []
    for idx, size in enumerate(sizes_mb, start=1):
        name = f"file_{idx}_{size}mb.bin"
        path = Path(dir_path) / name
        with open(path, "wb") as f:
            f.write(os.urandom(size * 1024 * 1024))
        files.append(name)
    return files


def baseline_reads(src_dir: str, files: List[str], ops: int, rng: random.Random) -> Tuple[float, float, int]:
    total_bytes = 0
    lat_sum = 0.0
    t0 = time.perf_counter()
    for _ in range(ops):
        name = rng.choice(files)
        p = Path(src_dir) / name
        s = os.path.getsize(p)
        with open(p, "rb") as f:
            _ = f.read()
        lat_sum += (time.perf_counter() - t0)  # not perfect per-op; adjust below
        total_bytes += s
        t0 = time.perf_counter()
    total_time = time.perf_counter() - (t0 - (lat_sum if ops > 0 else 0.0))
    avg_lat = (lat_sum / ops) if ops else 0.0
    return total_time, avg_lat, total_bytes


def cache_warmup(src_dir: str, cache_dir: str, files: List[str]) -> Tuple[float, int]:
    # Measure initial cache population time and bytes written
    com.SOURCE_DIR = src_dir
    com.CACHE_DIR = cache_dir
    total_bytes = 0
    t0 = time.perf_counter()
    for name in files:
        p = Path(src_dir) / name
        total_bytes += os.path.getsize(p)
        com.get_from_cache(name)
    warm_time = time.perf_counter() - t0
    return warm_time, total_bytes


def warm_cached_reads(src_dir: str, cache_dir: str, files: List[str], ops: int, rng: random.Random) -> Tuple[float, float, int]:
    com.SOURCE_DIR = src_dir
    com.CACHE_DIR = cache_dir
    total_bytes = 0
    lat_sum = 0.0
    t0 = time.perf_counter()
    for _ in range(ops):
        name = rng.choice(files)
        path = com.get_from_cache(name)
        with open(path, "rb") as f:
            enc = f.read()
        _ = com.aes_decrypt(enc)
        s = len(enc)
        total_bytes += s
        lat_sum += (time.perf_counter() - t0)
        t0 = time.perf_counter()
    total_time = time.perf_counter() - (t0 - (lat_sum if ops > 0 else 0.0))
    avg_lat = (lat_sum / ops) if ops else 0.0
    return total_time, avg_lat, total_bytes


def mb_per_s(bytes_count: int, seconds: float) -> float:
    return (bytes_count / (1024 * 1024)) / max(seconds, 1e-9)


def main():
    sizes = [8, 16, 32, 64, 128]
    ops = 100
    rng = random.Random(123)

    print("System info:")
    for k, v in system_info().items():
        print(f"  {k}: {v}")

    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as cache:
        os.environ["HYBRIDCACHE_SOURCE"] = src
        os.environ["HYBRIDCACHE_DIR"] = cache

        files = gen_files(src, sizes)

        print("\nBaseline (direct reads):")
        t_base, lat_base, bytes_base = baseline_reads(src, files, ops, rng)
        thr_base = mb_per_s(bytes_base, t_base)
        print(f"  total={t_base:.3f}s, avg_latency={lat_base*1000:.2f} ms, throughput={thr_base:.2f} MB/s")

        print("\nCache warm-up (write to cache):")
        t_warm, bytes_warm = cache_warmup(src, cache, files)
        thr_warm_write = mb_per_s(bytes_warm, t_warm)
        print(f"  total={t_warm:.3f}s, write_throughput={thr_warm_write:.2f} MB/s")

        print("\nWarm cache (cached reads):")
        t_cached, lat_cached, bytes_cached = warm_cached_reads(src, cache, files, ops, rng)
        thr_cached = mb_per_s(bytes_cached, t_cached)
        print(f"  total={t_cached:.3f}s, avg_latency={lat_cached*1000:.2f} ms, throughput={thr_cached:.2f} MB/s")

        improvement_time = (t_base - t_cached) / max(t_base, 1e-9) * 100.0
        print(f"\nTime improvement (baseline vs warm cached): {improvement_time:.1f}%")


if __name__ == "__main__":
    main()



