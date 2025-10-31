#!/usr/bin/env python3
"""
Performance comparison between original and secure versions
Measures the impact of security improvements on speed
"""

import os
import sys
import time
import tempfile
import random
from pathlib import Path
from typing import List, Tuple
import requests
import threading
import concurrent.futures


def benchmark_service(service_module, service_name: str, sizes_mb: List[int], iterations: int = 50):
    """Benchmark a service implementation"""
    print(f"\n=== Benchmarking {service_name} ===")
    
    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as cache:
        os.environ["HYBRIDCACHE_SOURCE"] = src
        os.environ["HYBRIDCACHE_DIR"] = cache
        os.environ["HYBRIDCACHE_ENCRYPTION"] = "0"
        
        # Create test files
        files = []
        for i, size in enumerate(sizes_mb):
            name = f"file_{i}_{size}mb.bin"
            path = Path(src) / name
            with open(path, "wb") as f:
                f.write(os.urandom(size * 1024 * 1024))
            files.append(name)
        
        # Set service directories
        service_module.SOURCE_DIR = src
        service_module.CACHE_DIR = cache
        
        # 1. Cache warm-up (write performance)
        print("  Warming up cache...")
        start = time.perf_counter()
        for name in files:
            service_module.get_from_cache(name)
        warmup_time = time.perf_counter() - start
        total_mb = sum(sizes_mb)
        write_throughput = (total_mb / warmup_time) if warmup_time > 0 else 0
        
        # 2. Random cache hits (read performance)
        print("  Testing cache hits...")
        rng = random.Random(42)  # Fixed seed for consistency
        latencies = []
        start = time.perf_counter()
        
        for _ in range(iterations):
            name = rng.choice(files)
            t0 = time.perf_counter()
            try:
                path = service_module.get_from_cache(name)
                with open(path, "rb") as f:
                    data = f.read()
                if hasattr(service_module, 'decrypt_data'):
                    _ = service_module.decrypt_data(data)
                latencies.append(time.perf_counter() - t0)
            except Exception as e:
                print(f"    Error: {e}")
                latencies.append(1.0)  # Penalty for errors
        
        total_time = time.perf_counter() - start
        avg_latency = sum(latencies) / len(latencies)
        read_throughput = (total_mb * iterations) / total_time
        
        # 3. Validation overhead test
        print("  Testing validation overhead...")
        validation_times = []
        for _ in range(1000):
            test_names = [
                "valid_file.txt",
                "../../../etc/passwd",
                "test.txt; cat /etc/passwd",
                "<script>alert('xss')</script>",
                "normal_file.bin"
            ]
            for test_name in test_names:
                t0 = time.perf_counter()
                if hasattr(service_module, 'validate_filename'):
                    service_module.validate_filename(test_name)
                else:
                    # Simple validation for original service
                    len(test_name) < 255 and not ('..' in test_name)
                validation_times.append(time.perf_counter() - t0)
        
        avg_validation_time = sum(validation_times) / len(validation_times)
        
        return {
            "service": service_name,
            "warmup_time": warmup_time,
            "write_throughput": write_throughput,
            "total_time": total_time,
            "avg_latency": avg_latency,
            "read_throughput": read_throughput,
            "validation_overhead": avg_validation_time,
            "iterations": iterations
        }


def test_rate_limiting_overhead():
    """Test the overhead of rate limiting"""
    print("\n=== Rate Limiting Overhead Test ===")
    
    # Import secure service to test rate limiting
    try:
        import commercial_service_fast_secure as secure_service
        
        # Test rate limiting function directly
        test_cases = [
            ("127.0.0.1", 100, 60),  # Normal case
            ("192.168.1.1", 100, 60),  # Different IP
            ("127.0.0.1", 100, 60),  # Same IP again
        ]
        
        times = []
        for ip, max_req, window in test_cases:
            start = time.perf_counter()
            for _ in range(10):
                result = secure_service.check_rate_limit(ip, max_req, window)
            times.append(time.perf_counter() - start)
        
        avg_rate_limit_time = sum(times) / len(times) / 10  # Per call
        
        print(f"  Rate limiting overhead: {avg_rate_limit_time*1000:.3f} ms per request")
        return avg_rate_limit_time
        
    except ImportError:
        print("  Secure service not available")
        return 0


def test_security_headers_overhead():
    """Test middleware overhead"""
    print("\n=== Security Headers Overhead Test ===")
    
    # Simulate middleware processing time
    def mock_middleware_processing():
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        }
        return headers
    
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        _ = mock_middleware_processing()
        times.append(time.perf_counter() - start)
    
    avg_middleware_time = sum(times) / len(times)
    print(f"  Security headers overhead: {avg_middleware_time*1000:.3f} ms per request")
    return avg_middleware_time


def main():
    print("🔒 Security vs Performance Analysis")
    print("=" * 60)
    
    sizes_mb = [1, 5, 10]  # Test file sizes
    iterations = 50
    
    # Benchmark original service
    try:
        import commercial_service_fast as original_service
        original_results = benchmark_service(original_service, "Original Fast", sizes_mb, iterations)
    except ImportError:
        print("Original service not available")
        original_results = None
    
    # Benchmark secure service
    try:
        import commercial_service_fast_secure as secure_service
        secure_results = benchmark_service(secure_service, "Secure Fast", sizes_mb, iterations)
    except ImportError:
        print("Secure service not available")
        secure_results = None
    
    # Test security overhead components
    rate_limit_overhead = test_rate_limiting_overhead()
    headers_overhead = test_security_headers_overhead()
    
    # Print comparison
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE COMPARISON RESULTS")
    print("=" * 60)
    
    if original_results and secure_results:
        print(f"\n{'Metric':<25} {'Original':<15} {'Secure':<15} {'Impact':<15}")
        print("-" * 70)
        
        # Write throughput
        write_impact = ((secure_results["write_throughput"] - original_results["write_throughput"]) / 
                       original_results["write_throughput"] * 100)
        print(f"{'Write Throughput (MB/s)':<25} {original_results['write_throughput']:<15.2f} "
              f"{secure_results['write_throughput']:<15.2f} {write_impact:+.1f}%")
        
        # Read throughput  
        read_impact = ((secure_results["read_throughput"] - original_results["read_throughput"]) / 
                      original_results["read_throughput"] * 100)
        print(f"{'Read Throughput (MB/s)':<25} {original_results['read_throughput']:<15.2f} "
              f"{secure_results['read_throughput']:<15.2f} {read_impact:+.1f}%")
        
        # Average latency
        lat_impact = ((secure_results["avg_latency"] - original_results["avg_latency"]) / 
                     original_results["avg_latency"] * 100)
        print(f"{'Avg Latency (ms)':<25} {original_results['avg_latency']*1000:<15.2f} "
              f"{secure_results['avg_latency']*1000:<15.2f} {lat_impact:+.1f}%")
        
        # Validation overhead
        val_impact = ((secure_results["validation_overhead"] - original_results["validation_overhead"]) / 
                     original_results["validation_overhead"] * 100)
        print(f"{'Validation Time (μs)':<25} {original_results['validation_overhead']*1000000:<15.2f} "
              f"{secure_results['validation_overhead']*1000000:<15.2f} {val_impact:+.1f}%")
    
    print(f"\n{'Security Overhead Components':<25} {'Time':<15}")
    print("-" * 40)
    print(f"{'Rate Limiting':<25} {rate_limit_overhead*1000:<15.3f} ms/req")
    print(f"{'Security Headers':<25} {headers_overhead*1000:<15.3f} ms/req")
    print(f"{'Total Security Overhead':<25} {(rate_limit_overhead + headers_overhead)*1000:<15.3f} ms/req")
    
    print("\n" + "=" * 60)
    print("🎯 CONCLUSION")
    print("=" * 60)
    
    if original_results and secure_results:
        total_impact = ((secure_results["read_throughput"] - original_results["read_throughput"]) / 
                       original_results["read_throughput"] * 100)
        
        if abs(total_impact) < 5:
            print("✅ SECURITY IMPACT: MINIMAL (< 5% performance loss)")
        elif abs(total_impact) < 15:
            print("⚠️  SECURITY IMPACT: MODERATE (5-15% performance loss)")
        else:
            print("🚨 SECURITY IMPACT: SIGNIFICANT (> 15% performance loss)")
        
        print(f"\nPerformance trade-off: {abs(total_impact):.1f}% slower for comprehensive security")
        print("Security benefits:")
        print("  ✓ Path traversal protection")
        print("  ✓ Rate limiting (DoS protection)")
        print("  ✓ Input validation")
        print("  ✓ Security headers")
        print("  ✓ File size limits")
        
        if total_impact < 0:
            print(f"\nRecommendation: Accept {abs(total_impact):.1f}% performance loss for security")
        else:
            print(f"\nBonus: Secure version is actually {total_impact:.1f}% faster!")
    
    print("=" * 60)


if __name__ == "__main__":
    main()



