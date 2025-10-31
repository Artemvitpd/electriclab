#!/usr/bin/env python3
"""
Speed comparison test between original fast service and secure service
"""

import os
import sys
import time
import requests
import subprocess
import tempfile
import threading
from pathlib import Path


class SpeedComparisonTester:
    def __init__(self):
        self.temp_dir = None
        self.process_fast = None
        self.process_secure = None
        self.results = {
            "fast_service": {
                "startup": 0,
                "warmup": 0,
                "cache_hits": [],
                "throughput": 0
            },
            "secure_service": {
                "startup": 0,
                "warmup": 0,
                "cache_hits": [],
                "throughput": 0
            }
        }

    def create_test_files(self, base_dir: str):
        """Create test files of different sizes"""
        files = [
            ("tiny.txt", 100),       # 100 bytes
            ("small.txt", 1024),     # 1KB
            ("medium.txt", 1024*10), # 10KB
            ("large.txt", 1024*100)  # 100KB
        ]
        
        source_dir = os.path.join(base_dir, "source")
        os.makedirs(source_dir, exist_ok=True)
        
        for name, size in files:
            test_file = os.path.join(source_dir, name)
            with open(test_file, "w") as f:
                f.write("x" * size)
        
        return [name for name, _ in files]

    def start_service(self, service_file: str, port: int, base_dir: str):
        """Start a service and return the process"""
        env = os.environ.copy()
        env["HYBRIDCACHE_DIR"] = os.path.join(base_dir, "cache")
        env["HYBRIDCACHE_SOURCE"] = os.path.join(base_dir, "source")
        env["HYBRIDCACHE_ENCRYPTION"] = "0"
        
        process = subprocess.Popen([
            sys.executable, service_file, 
            "--host", "127.0.0.1", "--port", str(port)
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for service to start
        time.sleep(3)
        return process

    def test_service_performance(self, port: int, service_name: str):
        """Test performance of a specific service"""
        base_url = f"http://127.0.0.1:{port}"
        results = self.results[service_name]
        
        print(f"\n🧪 Testing {service_name} on port {port}")
        
        # Test 1: Startup time (already measured)
        print(f"  ⏱️  Startup: {results['startup']:.3f}s")
        
        # Test 2: Cache warm-up
        start = time.perf_counter()
        try:
            response = requests.get(f"{base_url}/api/cache/large.txt", timeout=10)
            warmup_time = time.perf_counter() - start
            results["warmup"] = warmup_time
            print(f"  🔥 Warm-up: {warmup_time:.3f}s")
        except Exception as e:
            print(f"  ❌ Warm-up failed: {str(e)[:50]}")
            results["warmup"] = 10.0  # Penalty
        
        # Test 3: Cache hits performance
        print("  🎯 Testing cache hits...")
        latencies = []
        total_data = 0
        
        for i in range(50):  # 50 cache hits
            try:
                t0 = time.perf_counter()
                response = requests.get(f"{base_url}/api/cache/small.txt", timeout=3)
                latency = time.perf_counter() - t0
                latencies.append(latency)
                total_data += len(response.content) if response.status_code == 200 else 0
            except Exception as e:
                latencies.append(1.0)  # Penalty for errors
                print(f"    ❌ Error {i}: {str(e)[:30]}")
        
        results["cache_hits"] = latencies
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            total_time = sum(latencies)
            throughput = (total_data / total_time) / 1024 / 1024 if total_time > 0 else 0
            results["throughput"] = throughput
            print(f"  ⚡ Cache hits: {avg_latency*1000:.2f}ms avg, {throughput:.2f} MB/s")

    def run_comparison(self):
        """Run speed comparison between services"""
        print("🏁 Starting Speed Comparison Test")
        print("=" * 50)
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        test_files = self.create_test_files(self.temp_dir)
        print(f"📁 Created test files in: {self.temp_dir}")
        
        try:
            # Test Fast Service
            print(f"\n🚀 Starting Fast Service...")
            start = time.perf_counter()
            self.process_fast = self.start_service("commercial_service_fast.py", 8080, self.temp_dir)
            self.results["fast_service"]["startup"] = time.perf_counter() - start
            
            # Test Secure Service  
            print(f"\n🔒 Starting Secure Service...")
            start = time.perf_counter()
            self.process_secure = self.start_service("commercial_service_fixed.py", 8081, self.temp_dir)
            self.results["secure_service"]["startup"] = time.perf_counter() - start
            
            # Test both services
            self.test_service_performance(8080, "fast_service")
            self.test_service_performance(8081, "secure_service")
            
        finally:
            # Cleanup
            if self.process_fast:
                self.process_fast.terminate()
                self.process_fast.wait()
            if self.process_secure:
                self.process_secure.terminate()
                self.process_secure.wait()
            
            import shutil
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        
        self.print_comparison_results()

    def print_comparison_results(self):
        """Print detailed comparison results"""
        print("\n" + "=" * 60)
        print("📊 SPEED COMPARISON RESULTS")
        print("=" * 60)
        
        fast = self.results["fast_service"]
        secure = self.results["secure_service"]
        
        # Startup comparison
        print(f"\n🚀 STARTUP TIME:")
        print(f"  Fast Service:    {fast['startup']:.3f}s")
        print(f"  Secure Service:  {secure['startup']:.3f}s")
        
        startup_diff = secure['startup'] - fast['startup']
        startup_overhead = (startup_diff / fast['startup']) * 100 if fast['startup'] > 0 else 0
        print(f"  Overhead:        {startup_diff:+.3f}s ({startup_overhead:+.1f}%)")
        
        # Warm-up comparison
        print(f"\n🔥 CACHE WARM-UP:")
        print(f"  Fast Service:    {fast['warmup']:.3f}s")
        print(f"  Secure Service:  {secure['warmup']:.3f}s")
        
        warmup_diff = secure['warmup'] - fast['warmup']
        warmup_overhead = (warmup_diff / fast['warmup']) * 100 if fast['warmup'] > 0 else 0
        print(f"  Overhead:        {warmup_diff:+.3f}s ({warmup_overhead:+.1f}%)")
        
        # Cache hits comparison
        if fast['cache_hits'] and secure['cache_hits']:
            fast_avg = sum(fast['cache_hits']) / len(fast['cache_hits'])
            secure_avg = sum(secure['cache_hits']) / len(secure['cache_hits'])
            
            print(f"\n⚡ CACHE HIT LATENCY:")
            print(f"  Fast Service:    {fast_avg*1000:.2f}ms avg")
            print(f"  Secure Service:  {secure_avg*1000:.2f}ms avg")
            
            latency_diff = secure_avg - fast_avg
            latency_overhead = (latency_diff / fast_avg) * 100 if fast_avg > 0 else 0
            print(f"  Overhead:        {latency_diff*1000:+.2f}ms ({latency_overhead:+.1f}%)")
        
        # Throughput comparison
        print(f"\n📈 THROUGHPUT:")
        print(f"  Fast Service:    {fast['throughput']:.2f} MB/s")
        print(f"  Secure Service:  {secure['throughput']:.2f} MB/s")
        
        if fast['throughput'] > 0 and secure['throughput'] > 0:
            throughput_diff = secure['throughput'] - fast['throughput']
            throughput_overhead = (throughput_diff / fast['throughput']) * 100
            print(f"  Difference:      {throughput_diff:+.2f} MB/s ({throughput_overhead:+.1f}%)")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print("-" * 30)
        
        total_overhead = (startup_overhead + warmup_overhead + latency_overhead) / 3
        print(f"Average overhead: {total_overhead:+.1f}%")
        
        if total_overhead < 5:
            print("✅ EXCELLENT: Security features have minimal performance impact")
        elif total_overhead < 15:
            print("✅ GOOD: Security features have acceptable performance impact")
        elif total_overhead < 30:
            print("⚠️  FAIR: Security features have noticeable performance impact")
        else:
            print("❌ POOR: Security features significantly impact performance")
        
        print("=" * 60)


def main():
    tester = SpeedComparisonTester()
    tester.run_comparison()


if __name__ == "__main__":
    main()



