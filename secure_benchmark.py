#!/usr/bin/env python3
"""
Secure benchmark for HybridCache Services
Includes security testing alongside performance testing
"""

import os
import sys
import time
import requests
import threading
from pathlib import Path
import tempfile
import random
from typing import List, Tuple, Dict

import commercial_service_fast_secure as com


def security_test():
    """Run basic security tests"""
    print("\n🔒 Running Security Tests...")
    
    # Test 1: Path traversal
    test_cases = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
        "test.txt%00.jpg",
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --"
    ]
    
    blocked = 0
    for case in test_cases:
        try:
            response = requests.get(f"http://127.0.0.1:8081/api/cache/{case}", timeout=2)
            if response.status_code == 400:
                blocked += 1
                print(f"  ✓ Blocked: {case[:30]}...")
            else:
                print(f"  ✗ Allowed: {case[:30]}... -> {response.status_code}")
        except:
            print(f"  ✗ Error: {case[:30]}...")
    
    print(f"  Security: {blocked}/{len(test_cases)} attacks blocked")
    return blocked == len(test_cases)


def performance_test():
    """Run performance tests"""
    print("\n⚡ Running Performance Tests...")
    
    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as cache:
        os.environ["HYBRIDCACHE_SOURCE"] = src
        os.environ["HYBRIDCACHE_DIR"] = cache
        
        # Create test files
        sizes = [1, 5, 10]  # MB
        files = []
        for i, size in enumerate(sizes):
            name = f"test_{i}_{size}mb.bin"
            path = Path(src) / name
            with open(path, "wb") as f:
                f.write(os.urandom(size * 1024 * 1024))
            files.append(name)
        
        # Test direct reads
        start = time.perf_counter()
        for _ in range(10):
            for name in files:
                with open(Path(src) / name, "rb") as f:
                    _ = f.read()
        direct_time = time.perf_counter() - start
        
        # Test cached reads
        com.SOURCE_DIR = src
        com.CACHE_DIR = cache
        
        # Warm up cache
        for name in files:
            com.get_from_cache(name)
        
        start = time.perf_counter()
        for _ in range(10):
            for name in files:
                com.get_from_cache(name)
        cached_time = time.perf_counter() - start
        
        improvement = (direct_time - cached_time) / direct_time * 100
        print(f"  Direct reads: {direct_time:.3f}s")
        print(f"  Cached reads: {cached_time:.3f}s")
        print(f"  Improvement: {improvement:.1f}%")
        
        return improvement > 0


def main():
    print("🚀 HybridCache Secure Benchmark")
    print("=" * 40)
    
    # Start service
    print("Starting service...")
    # Note: In real usage, start service separately
    
    # Run tests
    security_ok = security_test()
    performance_ok = performance_test()
    
    print("\n" + "=" * 40)
    if security_ok and performance_ok:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 40)


if __name__ == "__main__":
    main()
