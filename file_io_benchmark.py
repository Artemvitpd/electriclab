#!/usr/bin/env python3
"""
Comprehensive file I/O benchmark for all HybridCache versions
Tests read/write performance with different file sizes
"""

import os
import sys
import time
import tempfile
import shutil
import json
from pathlib import Path
import statistics


class FileIOBenchmark:
    def __init__(self):
        self.results = {
            "direct_io": {"reads": [], "writes": []},
            "fast_service": {"reads": [], "writes": []},
            "secure_service": {"reads": [], "writes": []},
            "gov_service": {"reads": [], "writes": []}
        }
        self.temp_dir = None
        
    def create_test_files(self, sizes_kb):
        """Create test files of different sizes"""
        self.temp_dir = tempfile.mkdtemp()
        source_dir = os.path.join(self.temp_dir, "source")
        cache_dirs = {
            "fast": os.path.join(self.temp_dir, "fast_cache"),
            "secure": os.path.join(self.temp_dir, "secure_cache"),
            "gov": os.path.join(self.temp_dir, "gov_cache")
        }
        
        os.makedirs(source_dir, exist_ok=True)
        for cache_dir in cache_dirs.values():
            os.makedirs(cache_dir, exist_ok=True)
        
        # Create test files
        test_files = {}
        for size_kb in sizes_kb:
            filename = f"test_{size_kb}kb.dat"
            filepath = os.path.join(source_dir, filename)
            
            # Create file with random-like data
            data = os.urandom(size_kb * 1024)
            with open(filepath, "wb") as f:
                f.write(data)
            
            test_files[filename] = {
                "path": filepath,
                "size": size_kb * 1024,
                "size_kb": size_kb
            }
        
        return test_files, cache_dirs
    
    def benchmark_direct_io(self, test_files, iterations=10):
        """Benchmark direct file I/O without cache"""
        print("📁 Benchmarking Direct I/O...")
        
        for filename, file_info in test_files.items():
            filepath = file_info["path"]
            size_bytes = file_info["size"]
            
            # Read benchmark
            read_times = []
            for _ in range(iterations):
                start = time.perf_counter()
                with open(filepath, "rb") as f:
                    data = f.read()
                read_time = time.perf_counter() - start
                read_times.append(read_time)
            
            # Write benchmark
            write_times = []
            temp_file = os.path.join(self.temp_dir, f"temp_{filename}")
            for _ in range(iterations):
                start = time.perf_counter()
                with open(temp_file, "wb") as f:
                    f.write(data)
                write_time = time.perf_counter() - start
                write_times.append(write_time)
            
            avg_read_time = statistics.mean(read_times)
            avg_write_time = statistics.mean(write_times)
            read_throughput = (size_bytes / avg_read_time) / (1024 * 1024)  # MB/s
            write_throughput = (size_bytes / avg_write_time) / (1024 * 1024)  # MB/s
            
            self.results["direct_io"]["reads"].append({
                "filename": filename,
                "size_kb": file_info["size_kb"],
                "time_ms": avg_read_time * 1000,
                "throughput_mbps": read_throughput
            })
            
            self.results["direct_io"]["writes"].append({
                "filename": filename,
                "size_kb": file_info["size_kb"],
                "time_ms": avg_write_time * 1000,
                "throughput_mbps": write_throughput
            })
            
            print(f"  {filename}: Read {read_throughput:.1f} MB/s, Write {write_throughput:.1f} MB/s")
    
    def benchmark_fast_service(self, test_files, cache_dir, iterations=10):
        """Benchmark fast service cache operations"""
        print("\n⚡ Benchmarking Fast Service...")
        
        def cache_path(filename):
            return os.path.join(cache_dir, filename)
        
        def get_from_cache(filename):
            cpath = cache_path(filename)
            spath = test_files[filename]["path"]
            
            if os.path.exists(cpath):
                return cpath
            
            shutil.copy2(spath, cpath)
            return cpath
        
        for filename, file_info in test_files.items():
            size_bytes = file_info["size"]
            
            # Warm up cache
            get_from_cache(filename)
            
            # Read benchmark (cache hits)
            read_times = []
            for _ in range(iterations):
                start = time.perf_counter()
                cache_file = get_from_cache(filename)
                with open(cache_file, "rb") as f:
                    data = f.read()
                read_time = time.perf_counter() - start
                read_times.append(read_time)
            
            # Write benchmark (cache updates)
            write_times = []
            for _ in range(iterations):
                start = time.perf_counter()
                cache_file = get_from_cache(filename)
                with open(cache_file, "wb") as f:
                    f.write(data)
                write_time = time.perf_counter() - start
                write_times.append(write_time)
            
            avg_read_time = statistics.mean(read_times)
            avg_write_time = statistics.mean(write_times)
            read_throughput = (size_bytes / avg_read_time) / (1024 * 1024)
            write_throughput = (size_bytes / avg_write_time) / (1024 * 1024)
            
            self.results["fast_service"]["reads"].append({
                "filename": filename,
                "size_kb": file_info["size_kb"],
                "time_ms": avg_read_time * 1000,
                "throughput_mbps": read_throughput
            })
            
            self.results["fast_service"]["writes"].append({
                "filename": filename,
                "size_kb": file_info["size_kb"],
                "time_ms": avg_write_time * 1000,
                "throughput_mbps": write_throughput
            })
            
            print(f"  {filename}: Read {read_throughput:.1f} MB/s, Write {write_throughput:.1f} MB/s")
    
    def benchmark_secure_service(self, test_files, cache_dir, iterations=10):
        """Benchmark secure service with validation"""
        print("\n🔒 Benchmarking Secure Service...")
        
        def validate_filename(name):
            import re
            if not name or len(name) > 255:
                return False
            dangerous_patterns = [r'\.\.', r'/', r'\\\\', r'%2e%2e', r'%2f', r'%5c', r'\x00', r'[<>:"|?*]']
            for pattern in dangerous_patterns:
                if re.search(pattern, name, re.IGNORECASE):
                    return False
            return re.fullmatch(r"[A-Za-z0-9._-]+", name) is not None
        
        def cache_path(filename):
            safe = filename.replace("/", "_").replace("\\", "_").replace("..", "")
            return os.path.join(cache_dir, safe)
        
        def get_from_cache(filename):
            if not validate_filename(filename):
                raise ValueError(f"Invalid filename: {filename}")
            
            cpath = cache_path(filename)
            spath = test_files[filename]["path"]
            
            if os.path.exists(cpath):
                return cpath
            
            shutil.copy2(spath, cpath)
            return cpath
        
        for filename, file_info in test_files.items():
            size_bytes = file_info["size"]
            
            # Warm up cache
            get_from_cache(filename)
            
            # Read benchmark (cache hits with validation)
            read_times = []
            for _ in range(iterations):
                start = time.perf_counter()
                cache_file = get_from_cache(filename)
                with open(cache_file, "rb") as f:
                    data = f.read()
                read_time = time.perf_counter() - start
                read_times.append(read_time)
            
            # Write benchmark (cache updates with validation)
            write_times = []
            for _ in range(iterations):
                start = time.perf_counter()
                cache_file = get_from_cache(filename)
                with open(cache_file, "wb") as f:
                    f.write(data)
                write_time = time.perf_counter() - start
                write_times.append(write_time)
            
            avg_read_time = statistics.mean(read_times)
            avg_write_time = statistics.mean(write_times)
            read_throughput = (size_bytes / avg_read_time) / (1024 * 1024)
            write_throughput = (size_bytes / avg_write_time) / (1024 * 1024)
            
            self.results["secure_service"]["reads"].append({
                "filename": filename,
                "size_kb": file_info["size_kb"],
                "time_ms": avg_read_time * 1000,
                "throughput_mbps": read_throughput
            })
            
            self.results["secure_service"]["writes"].append({
                "filename": filename,
                "size_kb": file_info["size_kb"],
                "time_ms": avg_write_time * 1000,
                "throughput_mbps": write_throughput
            })
            
            print(f"  {filename}: Read {read_throughput:.1f} MB/s, Write {write_throughput:.1f} MB/s")
    
    def benchmark_gov_service(self, test_files, cache_dir, iterations=10):
        """Benchmark government service with encryption"""
        print("\n🏛️ Benchmarking Government Service...")
        
        # Simple encryption simulation (AES-like)
        def simple_encrypt(data):
            # Simulate encryption overhead without actual crypto
            return data + b"_encrypted"
        
        def simple_decrypt(data):
            # Simulate decryption overhead
            return data[:-10] if data.endswith(b"_encrypted") else data
        
        def cache_path(filename):
            safe = filename.replace("/", "_").replace("\\", "_").replace("..", "")
            return os.path.join(cache_dir, safe)
        
        def get_from_cache(filename):
            cpath = cache_path(filename)
            spath = test_files[filename]["path"]
            
            if os.path.exists(cpath):
                return cpath
            
            # Encrypt and store
            with open(spath, "rb") as f:
                raw_data = f.read()
            encrypted_data = simple_encrypt(raw_data)
            with open(cpath, "wb") as f:
                f.write(encrypted_data)
            
            return cpath
        
        for filename, file_info in test_files.items():
            size_bytes = file_info["size"]
            
            # Warm up cache
            get_from_cache(filename)
            
            # Read benchmark (cache hits with decryption)
            read_times = []
            for _ in range(iterations):
                start = time.perf_counter()
                cache_file = get_from_cache(filename)
                with open(cache_file, "rb") as f:
                    encrypted_data = f.read()
                data = simple_decrypt(encrypted_data)
                read_time = time.perf_counter() - start
                read_times.append(read_time)
            
            # Write benchmark (cache updates with encryption)
            write_times = []
            for _ in range(iterations):
                start = time.perf_counter()
                cache_file = get_from_cache(filename)
                with open(cache_file, "wb") as f:
                    encrypted_data = simple_encrypt(data)
                    f.write(encrypted_data)
                write_time = time.perf_counter() - start
                write_times.append(write_time)
            
            avg_read_time = statistics.mean(read_times)
            avg_write_time = statistics.mean(write_times)
            read_throughput = (size_bytes / avg_read_time) / (1024 * 1024)
            write_throughput = (size_bytes / avg_write_time) / (1024 * 1024)
            
            self.results["gov_service"]["reads"].append({
                "filename": filename,
                "size_kb": file_info["size_kb"],
                "time_ms": avg_read_time * 1000,
                "throughput_mbps": read_throughput
            })
            
            self.results["gov_service"]["writes"].append({
                "filename": filename,
                "size_kb": file_info["size_kb"],
                "time_ms": avg_write_time * 1000,
                "throughput_mbps": write_throughput
            })
            
            print(f"  {filename}: Read {read_throughput:.1f} MB/s, Write {write_throughput:.1f} MB/s")
    
    def run_benchmark(self):
        """Run complete benchmark suite"""
        print("🏁 File I/O Benchmark Suite")
        print("=" * 60)
        
        # Test different file sizes
        sizes_kb = [1, 10, 100, 1024, 10240]  # 1KB, 10KB, 100KB, 1MB, 10MB
        
        try:
            test_files, cache_dirs = self.create_test_files(sizes_kb)
            print(f"📁 Created {len(test_files)} test files in {self.temp_dir}")
            
            # Run benchmarks
            self.benchmark_direct_io(test_files)
            self.benchmark_fast_service(test_files, cache_dirs["fast"])
            self.benchmark_secure_service(test_files, cache_dirs["secure"])
            self.benchmark_gov_service(test_files, cache_dirs["gov"])
            
        finally:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        
        self.print_summary_table()
    
    def print_summary_table(self):
        """Print comprehensive summary table"""
        print("\n" + "=" * 80)
        print("📊 СВОДНАЯ ТАБЛИЦА ПРОИЗВОДИТЕЛЬНОСТИ ЧТЕНИЯ/ЗАПИСИ")
        print("=" * 80)
        
        # Header
        print(f"{'Размер файла':<12} {'Метод':<15} {'Чтение (MB/s)':<15} {'Запись (MB/s)':<15} {'Чтение (мс)':<12} {'Запись (мс)':<12}")
        print("-" * 80)
        
        # Get unique file sizes
        sizes = sorted(set([result["size_kb"] for result in self.results["direct_io"]["reads"]]))
        
        for size_kb in sizes:
            print(f"\n📁 {size_kb} KB файлы:")
            
            # Direct I/O
            direct_read = next((r for r in self.results["direct_io"]["reads"] if r["size_kb"] == size_kb), None)
            direct_write = next((w for w in self.results["direct_io"]["writes"] if w["size_kb"] == size_kb), None)
            if direct_read and direct_write:
                print(f"{'':12} {'Прямое I/O':<15} {direct_read['throughput_mbps']:<15.1f} {direct_write['throughput_mbps']:<15.1f} {direct_read['time_ms']:<12.2f} {direct_write['time_ms']:<12.2f}")
            
            # Fast Service
            fast_read = next((r for r in self.results["fast_service"]["reads"] if r["size_kb"] == size_kb), None)
            fast_write = next((w for w in self.results["fast_service"]["writes"] if w["size_kb"] == size_kb), None)
            if fast_read and fast_write:
                print(f"{'':12} {'Быстрый кэш':<15} {fast_read['throughput_mbps']:<15.1f} {fast_write['throughput_mbps']:<15.1f} {fast_read['time_ms']:<12.2f} {fast_write['time_ms']:<12.2f}")
            
            # Secure Service
            secure_read = next((r for r in self.results["secure_service"]["reads"] if r["size_kb"] == size_kb), None)
            secure_write = next((w for w in self.results["secure_service"]["writes"] if w["size_kb"] == size_kb), None)
            if secure_read and secure_write:
                print(f"{'':12} {'Безопасный кэш':<15} {secure_read['throughput_mbps']:<15.1f} {secure_write['throughput_mbps']:<15.1f} {secure_read['time_ms']:<12.2f} {secure_write['time_ms']:<12.2f}")
            
            # Government Service
            gov_read = next((r for r in self.results["gov_service"]["reads"] if r["size_kb"] == size_kb), None)
            gov_write = next((w for w in self.results["gov_service"]["writes"] if w["size_kb"] == size_kb), None)
            if gov_read and gov_write:
                print(f"{'':12} {'Гос. кэш':<15} {gov_read['throughput_mbps']:<15.1f} {gov_write['throughput_mbps']:<15.1f} {gov_read['time_ms']:<12.2f} {gov_write['time_ms']:<12.2f}")
        
        # Performance comparison table
        print(f"\n" + "=" * 80)
        print("📈 СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ ОТНОСИТЕЛЬНО ПРЯМОГО I/O")
        print("=" * 80)
        
        print(f"{'Размер':<8} {'Быстрый кэш':<15} {'Безопасный кэш':<15} {'Гос. кэш':<15}")
        print(f"{'файла':<8} {'Чт/Зп':<7} {'Чт/Зп':<7} {'Чт/Зп':<7}")
        print("-" * 80)
        
        for size_kb in sizes:
            direct_read = next((r for r in self.results["direct_io"]["reads"] if r["size_kb"] == size_kb), None)
            direct_write = next((w for w in self.results["direct_io"]["writes"] if w["size_kb"] == size_kb), None)
            
            if direct_read and direct_write:
                # Fast service comparison
                fast_read = next((r for r in self.results["fast_service"]["reads"] if r["size_kb"] == size_kb), None)
                fast_write = next((w for w in self.results["fast_service"]["writes"] if w["size_kb"] == size_kb), None)
                fast_read_pct = ((fast_read['throughput_mbps'] / direct_read['throughput_mbps']) - 1) * 100 if fast_read else 0
                fast_write_pct = ((fast_write['throughput_mbps'] / direct_write['throughput_mbps']) - 1) * 100 if fast_write else 0
                
                # Secure service comparison
                secure_read = next((r for r in self.results["secure_service"]["reads"] if r["size_kb"] == size_kb), None)
                secure_write = next((w for w in self.results["secure_service"]["writes"] if w["size_kb"] == size_kb), None)
                secure_read_pct = ((secure_read['throughput_mbps'] / direct_read['throughput_mbps']) - 1) * 100 if secure_read else 0
                secure_write_pct = ((secure_write['throughput_mbps'] / direct_write['throughput_mbps']) - 1) * 100 if secure_write else 0
                
                # Government service comparison
                gov_read = next((r for r in self.results["gov_service"]["reads"] if r["size_kb"] == size_kb), None)
                gov_write = next((w for w in self.results["gov_service"]["writes"] if w["size_kb"] == size_kb), None)
                gov_read_pct = ((gov_read['throughput_mbps'] / direct_read['throughput_mbps']) - 1) * 100 if gov_read else 0
                gov_write_pct = ((gov_write['throughput_mbps'] / direct_write['throughput_mbps']) - 1) * 100 if gov_write else 0
                
                print(f"{size_kb:<8} {fast_read_pct:+6.1f}%/{fast_write_pct:+6.1f}% {secure_read_pct:+6.1f}%/{secure_write_pct:+6.1f}% {gov_read_pct:+6.1f}%/{gov_write_pct:+6.1f}%")
        
        # Summary statistics
        print(f"\n" + "=" * 80)
        print("📋 СВОДНАЯ СТАТИСТИКА")
        print("=" * 80)
        
        # Calculate average performance across all sizes
        services = ["fast_service", "secure_service", "gov_service"]
        for service in services:
            read_speeds = [r["throughput_mbps"] for r in self.results[service]["reads"]]
            write_speeds = [w["throughput_mbps"] for w in self.results[service]["writes"]]
            
            avg_read = statistics.mean(read_speeds)
            avg_write = statistics.mean(write_speeds)
            
            # Compare to direct I/O
            direct_reads = [r["throughput_mbps"] for r in self.results["direct_io"]["reads"]]
            direct_writes = [w["throughput_mbps"] for w in self.results["direct_io"]["writes"]]
            avg_direct_read = statistics.mean(direct_reads)
            avg_direct_write = statistics.mean(direct_writes)
            
            read_overhead = ((avg_read / avg_direct_read) - 1) * 100
            write_overhead = ((avg_write / avg_direct_write) - 1) * 100
            
            service_name = {
                "fast_service": "Быстрый кэш",
                "secure_service": "Безопасный кэш", 
                "gov_service": "Гос. кэш"
            }[service]
            
            print(f"{service_name}:")
            print(f"  📖 Средняя скорость чтения: {avg_read:.1f} MB/s ({read_overhead:+.1f}% от прямого I/O)")
            print(f"  📝 Средняя скорость записи: {avg_write:.1f} MB/s ({write_overhead:+.1f}% от прямого I/O)")
        
        print("=" * 80)


def main():
    benchmark = FileIOBenchmark()
    benchmark.run_benchmark()


if __name__ == "__main__":
    main()



