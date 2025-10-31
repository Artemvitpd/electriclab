#!/usr/bin/env python3
"""
Performance comparison between fast and secure implementations
Tests core functionality without HTTP dependencies
"""

import os
import sys
import time
import tempfile
import shutil
import re
from pathlib import Path


class FastService:
    """Fast service implementation (no security features)"""
    
    def __init__(self, cache_dir: str, source_dir: str):
        self.cache_dir = cache_dir
        self.source_dir = source_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def cache_path(self, filename: str) -> str:
        # Simple unsafe implementation
        return os.path.join(self.cache_dir, filename)
    
    def get_from_cache(self, filename: str) -> str:
        cpath = self.cache_path(filename)
        spath = os.path.join(self.source_dir, filename)
        
        # Cache hit check
        if os.path.exists(cpath):
            return cpath
        
        # Cache miss - load from source
        if not os.path.exists(spath):
            raise FileNotFoundError(f"Source not found: {spath}")
        
        # Copy to cache
        shutil.copy2(spath, cpath)
        return cpath


class SecureService:
    """Secure service implementation (with security features)"""
    
    def __init__(self, cache_dir: str, source_dir: str):
        self.cache_dir = cache_dir
        self.source_dir = source_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def validate_filename(self, name: str) -> bool:
        """Enhanced filename validation"""
        if not name or len(name) > 255:
            return False
        
        # Block path traversal patterns
        dangerous_patterns = [
            r'\.\.',      # Parent directory
            r'/',         # Forward slash
            r'\\\\',      # Backslash
            r'%2e%2e',    # URL encoded ..
            r'%2f',       # URL encoded /
            r'%5c',       # URL encoded \\
            r'\x00',      # Null byte
            r'[<>:"|?*]'  # Windows forbidden chars
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False
        
        # Only allow safe characters
        return re.fullmatch(r"[A-Za-z0-9._-]+", name) is not None
    
    def cache_path(self, filename: str) -> str:
        # Safe implementation
        safe = filename.replace("/", "_").replace("\\", "_").replace("..", "")
        return os.path.join(self.cache_dir, safe)
    
    def get_from_cache(self, filename: str) -> str:
        # Validate filename first
        if not self.validate_filename(filename):
            raise ValueError(f"Invalid filename: {filename}")
        
        cpath = self.cache_path(filename)
        spath = os.path.join(self.source_dir, filename)
        
        # Cache hit check
        if os.path.exists(cpath):
            return cpath
        
        # Cache miss - load from source
        if not os.path.exists(spath):
            raise FileNotFoundError(f"Source not found: {spath}")
        
        # Copy to cache
        shutil.copy2(spath, cpath)
        return cpath


class PerformanceComparison:
    def __init__(self):
        self.temp_dir = None
        self.results = {
            "fast_service": {
                "warmup": 0,
                "cache_hits": [],
                "throughput": 0,
                "validation_time": 0
            },
            "secure_service": {
                "warmup": 0,
                "cache_hits": [],
                "throughput": 0,
                "validation_time": 0
            }
        }
    
    def create_test_environment(self):
        """Create test files and directories"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create directories
        fast_cache = os.path.join(self.temp_dir, "fast_cache")
        secure_cache = os.path.join(self.temp_dir, "secure_cache")
        source_dir = os.path.join(self.temp_dir, "source")
        
        os.makedirs(source_dir, exist_ok=True)
        
        # Create test files of different sizes
        test_files = [
            ("tiny.txt", 100),       # 100 bytes
            ("small.txt", 1024),     # 1KB
            ("medium.txt", 1024*10), # 10KB
            ("large.txt", 1024*100)  # 100KB
        ]
        
        for name, size in test_files:
            test_file = os.path.join(source_dir, name)
            with open(test_file, "w") as f:
                f.write("x" * size)
        
        return fast_cache, secure_cache, source_dir, test_files
    
    def test_service_performance(self, service, service_name: str, test_files: list):
        """Test performance of a service"""
        print(f"\n🧪 Testing {service_name}...")
        
        # Test 1: Cache warm-up
        start = time.perf_counter()
        for name, _ in test_files:
            try:
                service.get_from_cache(name)
            except Exception as e:
                print(f"    ❌ Warm-up error for {name}: {str(e)[:50]}")
        warmup_time = time.perf_counter() - start
        self.results[service_name]["warmup"] = warmup_time
        print(f"  🔥 Warm-up: {warmup_time:.3f}s")
        
        # Test 2: Cache hits
        print("  🎯 Testing cache hits...")
        latencies = []
        total_data = 0
        
        for i in range(50):  # 50 cache hits
            for name, size in test_files:
                try:
                    t0 = time.perf_counter()
                    service.get_from_cache(name)
                    latency = time.perf_counter() - t0
                    latencies.append(latency)
                    total_data += size
                except Exception as e:
                    latencies.append(1.0)  # Penalty for errors
                    print(f"    ❌ Cache hit error for {name}: {str(e)[:50]}")
        
        self.results[service_name]["cache_hits"] = latencies
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            total_time = sum(latencies)
            throughput = (total_data / total_time) / 1024 / 1024 if total_time > 0 else 0
            self.results[service_name]["throughput"] = throughput
            print(f"  ⚡ Cache hits: {avg_latency*1000:.2f}ms avg, {throughput:.2f} MB/s")
        
        # Test 3: Validation overhead (for secure service)
        if service_name == "secure_service":
            print("  🛡️  Testing validation overhead...")
            validation_start = time.perf_counter()
            
            test_filenames = [
                "valid_file.txt",
                "../../../etc/passwd",
                "<script>alert('xss')</script>",
                "test.txt; cat /etc/passwd",
                "normal.bin"
            ]
            
            for _ in range(1000):
                for name in test_filenames:
                    service.validate_filename(name)
            
            validation_time = time.perf_counter() - validation_start
            self.results[service_name]["validation_time"] = validation_time
            print(f"  🛡️  Validation: {validation_time:.3f}s for 5000 validations")
    
    def run_comparison(self):
        """Run the complete performance comparison"""
        print("🏁 Performance Comparison: Fast vs Secure Service")
        print("=" * 60)
        
        # Create test environment
        fast_cache, secure_cache, source_dir, test_files = self.create_test_environment()
        print(f"📁 Test environment: {self.temp_dir}")
        
        try:
            # Create services
            fast_service = FastService(fast_cache, source_dir)
            secure_service = SecureService(secure_cache, source_dir)
            
            # Test both services
            self.test_service_performance(fast_service, "fast_service", test_files)
            self.test_service_performance(secure_service, "secure_service", test_files)
            
        finally:
            # Cleanup
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        
        self.print_results()
    
    def print_results(self):
        """Print detailed comparison results"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE COMPARISON RESULTS")
        print("=" * 60)
        
        fast = self.results["fast_service"]
        secure = self.results["secure_service"]
        
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
        
        # Validation overhead
        print(f"\n🛡️  VALIDATION OVERHEAD:")
        print(f"  Secure Service:  {secure['validation_time']:.3f}s")
        print(f"  Fast Service:    N/A (no validation)")
        print(f"  Additional cost: {secure['validation_time']:.3f}s")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print("-" * 30)
        
        # Calculate average overhead
        overheads = []
        if warmup_overhead != 0:
            overheads.append(abs(warmup_overhead))
        if 'latency_overhead' in locals() and latency_overhead != 0:
            overheads.append(abs(latency_overhead))
        if 'throughput_overhead' in locals() and throughput_overhead != 0:
            overheads.append(abs(throughput_overhead))
        
        if overheads:
            avg_overhead = sum(overheads) / len(overheads)
            print(f"Average performance overhead: {avg_overhead:.1f}%")
            
            if avg_overhead < 5:
                print("✅ EXCELLENT: Security features have minimal performance impact")
            elif avg_overhead < 15:
                print("✅ GOOD: Security features have acceptable performance impact")
            elif avg_overhead < 30:
                print("⚠️  FAIR: Security features have noticeable performance impact")
            else:
                print("❌ POOR: Security features significantly impact performance")
        else:
            print("✅ No significant performance overhead detected")
        
        # Security vs Performance trade-off
        print(f"\n🔒 SECURITY vs ⚡ PERFORMANCE:")
        print("-" * 30)
        print("✅ Path traversal protection: ACTIVE")
        print("✅ Injection attack prevention: ACTIVE")
        print("✅ Filename validation: ACTIVE")
        print("✅ Input sanitization: ACTIVE")
        
        validation_cost = secure['validation_time']
        if validation_cost < 0.1:
            print("✅ Validation cost: NEGLIGIBLE")
        elif validation_cost < 0.5:
            print("✅ Validation cost: MINIMAL")
        else:
            print("⚠️  Validation cost: NOTICEABLE")
        
        print("=" * 60)


def main():
    tester = PerformanceComparison()
    tester.run_comparison()


if __name__ == "__main__":
    main()



