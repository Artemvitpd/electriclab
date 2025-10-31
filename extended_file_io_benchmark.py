#!/usr/bin/env python3
"""
Extended file I/O benchmark for large files (100-500 MB)
Tests read/write performance with very large files
"""

import os
import sys
import time
import tempfile
import shutil
import json
from pathlib import Path
import statistics
import threading
import concurrent.futures


class ExtendedFileIOBenchmark:
    def __init__(self):
        self.results = {
            "direct_io": {"reads": [], "writes": []},
            "fast_service": {"reads": [], "writes": []},
            "secure_service": {"reads": [], "writes": []},
            "gov_service": {"reads": [], "writes": []}
        }
        self.temp_dir = None
        
    def create_large_test_files(self, sizes_mb):
        """Create large test files of different sizes"""
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
        
        # Create large test files
        test_files = {}
        chunk_size = 1024 * 1024  # 1MB chunks
        
        for size_mb in sizes_mb:
            filename = f"test_{size_mb}mb.dat"
            filepath = os.path.join(source_dir, filename)
            
            print(f"📁 Creating {filename} ({size_mb} MB)...")
            start_time = time.perf_counter()
            
            # Create file with random-like data in chunks
            with open(filepath, "wb") as f:
                for chunk in range(size_mb):
                    # Generate 1MB of data
                    data = os.urandom(chunk_size)
                    f.write(data)
                    
                    # Progress indicator for very large files
                    if size_mb >= 100 and chunk % 50 == 0:
                        progress = (chunk / size_mb) * 100
                        print(f"    Progress: {progress:.1f}%")
            
            creation_time = time.perf_counter() - start_time
            actual_size = os.path.getsize(filepath) / (1024 * 1024)
            
            test_files[filename] = {
                "path": filepath,
                "size": size_mb * 1024 * 1024,
                "size_mb": size_mb,
                "actual_size_mb": actual_size,
                "creation_time": creation_time
            }
            
            print(f"    ✅ Created in {creation_time:.2f}s ({actual_size:.1f} MB)")
        
        return test_files, cache_dirs
    
    def benchmark_direct_io(self, test_files, iterations=3):
        """Benchmark direct file I/O without cache"""
        print("\n📁 Benchmarking Direct I/O for Large Files...")
        
        for filename, file_info in test_files.items():
            filepath = file_info["path"]
            size_bytes = file_info["size"]
            size_mb = file_info["size_mb"]
            
            print(f"  🔍 Testing {filename} ({size_mb} MB)...")
            
            # Read benchmark
            read_times = []
            for i in range(iterations):
                print(f"    📖 Read iteration {i+1}/{iterations}...")
                start = time.perf_counter()
                
                # Read in chunks to avoid memory issues
                chunk_size = 64 * 1024 * 1024  # 64MB chunks
                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                
                read_time = time.perf_counter() - start
                read_times.append(read_time)
                print(f"      Read time: {read_time:.2f}s")
            
            # Write benchmark
            write_times = []
            temp_file = os.path.join(self.temp_dir, f"temp_{filename}")
            for i in range(iterations):
                print(f"    📝 Write iteration {i+1}/{iterations}...")
                start = time.perf_counter()
                
                # Write in chunks
                chunk_size = 64 * 1024 * 1024  # 64MB chunks
                with open(temp_file, "wb") as f:
                    with open(filepath, "rb") as source:
                        while True:
                            chunk = source.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                
                write_time = time.perf_counter() - start
                write_times.append(write_time)
                print(f"      Write time: {write_time:.2f}s")
            
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            avg_read_time = statistics.mean(read_times)
            avg_write_time = statistics.mean(write_times)
            read_throughput = (size_bytes / avg_read_time) / (1024 * 1024)  # MB/s
            write_throughput = (size_bytes / avg_write_time) / (1024 * 1024)  # MB/s
            
            self.results["direct_io"]["reads"].append({
                "filename": filename,
                "size_mb": file_info["size_mb"],
                "time_s": avg_read_time,
                "throughput_mbps": read_throughput
            })
            
            self.results["direct_io"]["writes"].append({
                "filename": filename,
                "size_mb": file_info["size_mb"],
                "time_s": avg_write_time,
                "throughput_mbps": write_throughput
            })
            
            print(f"    📊 Results: Read {read_throughput:.1f} MB/s, Write {write_throughput:.1f} MB/s")
    
    def benchmark_fast_service(self, test_files, cache_dir, iterations=3):
        """Benchmark fast service cache operations"""
        print("\n⚡ Benchmarking Fast Service for Large Files...")
        
        def cache_path(filename):
            return os.path.join(cache_dir, filename)
        
        def get_from_cache(filename):
            cpath = cache_path(filename)
            spath = test_files[filename]["path"]
            
            if os.path.exists(cpath):
                return cpath
            
            # Copy to cache in chunks
            chunk_size = 64 * 1024 * 1024  # 64MB chunks
            with open(spath, "rb") as src, open(cpath, "wb") as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
            
            return cpath
        
        for filename, file_info in test_files.items():
            size_bytes = file_info["size"]
            size_mb = file_info["size_mb"]
            
            print(f"  🔍 Testing {filename} ({size_mb} MB)...")
            
            # Warm up cache
            print("    🔥 Warming up cache...")
            cache_file = get_from_cache(filename)
            
            # Read benchmark (cache hits)
            read_times = []
            for i in range(iterations):
                print(f"    📖 Cache read iteration {i+1}/{iterations}...")
                start = time.perf_counter()
                
                # Read from cache in chunks
                chunk_size = 64 * 1024 * 1024  # 64MB chunks
                with open(cache_file, "rb") as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                
                read_time = time.perf_counter() - start
                read_times.append(read_time)
                print(f"      Cache read time: {read_time:.2f}s")
            
            # Write benchmark (cache updates)
            write_times = []
            for i in range(iterations):
                print(f"    📝 Cache write iteration {i+1}/{iterations}...")
                start = time.perf_counter()
                
                # Write to cache in chunks
                chunk_size = 64 * 1024 * 1024  # 64MB chunks
                with open(cache_file, "wb") as f:
                    with open(file_info["path"], "rb") as source:
                        while True:
                            chunk = source.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                
                write_time = time.perf_counter() - start
                write_times.append(write_time)
                print(f"      Cache write time: {write_time:.2f}s")
            
            avg_read_time = statistics.mean(read_times)
            avg_write_time = statistics.mean(write_times)
            read_throughput = (size_bytes / avg_read_time) / (1024 * 1024)
            write_throughput = (size_bytes / avg_write_time) / (1024 * 1024)
            
            self.results["fast_service"]["reads"].append({
                "filename": filename,
                "size_mb": file_info["size_mb"],
                "time_s": avg_read_time,
                "throughput_mbps": read_throughput
            })
            
            self.results["fast_service"]["writes"].append({
                "filename": filename,
                "size_mb": file_info["size_mb"],
                "time_s": avg_write_time,
                "throughput_mbps": write_throughput
            })
            
            print(f"    📊 Results: Read {read_throughput:.1f} MB/s, Write {write_throughput:.1f} MB/s")
    
    def benchmark_secure_service(self, test_files, cache_dir, iterations=3):
        """Benchmark secure service with validation"""
        print("\n🔒 Benchmarking Secure Service for Large Files...")
        
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
            
            # Copy to cache in chunks with validation
            chunk_size = 64 * 1024 * 1024  # 64MB chunks
            with open(spath, "rb") as src, open(cpath, "wb") as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
            
            return cpath
        
        for filename, file_info in test_files.items():
            size_bytes = file_info["size"]
            size_mb = file_info["size_mb"]
            
            print(f"  🔍 Testing {filename} ({size_mb} MB)...")
            
            # Warm up cache
            print("    🔥 Warming up cache with validation...")
            cache_file = get_from_cache(filename)
            
            # Read benchmark (cache hits with validation)
            read_times = []
            for i in range(iterations):
                print(f"    📖 Secure read iteration {i+1}/{iterations}...")
                start = time.perf_counter()
                
                # Validate filename on each access
                if not validate_filename(filename):
                    raise ValueError(f"Invalid filename: {filename}")
                
                # Read from cache in chunks
                chunk_size = 64 * 1024 * 1024  # 64MB chunks
                with open(cache_file, "rb") as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                
                read_time = time.perf_counter() - start
                read_times.append(read_time)
                print(f"      Secure read time: {read_time:.2f}s")
            
            # Write benchmark (cache updates with validation)
            write_times = []
            for i in range(iterations):
                print(f"    📝 Secure write iteration {i+1}/{iterations}...")
                start = time.perf_counter()
                
                # Validate filename
                if not validate_filename(filename):
                    raise ValueError(f"Invalid filename: {filename}")
                
                # Write to cache in chunks
                chunk_size = 64 * 1024 * 1024  # 64MB chunks
                with open(cache_file, "wb") as f:
                    with open(file_info["path"], "rb") as source:
                        while True:
                            chunk = source.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                
                write_time = time.perf_counter() - start
                write_times.append(write_time)
                print(f"      Secure write time: {write_time:.2f}s")
            
            avg_read_time = statistics.mean(read_times)
            avg_write_time = statistics.mean(write_times)
            read_throughput = (size_bytes / avg_read_time) / (1024 * 1024)
            write_throughput = (size_bytes / avg_write_time) / (1024 * 1024)
            
            self.results["secure_service"]["reads"].append({
                "filename": filename,
                "size_mb": file_info["size_mb"],
                "time_s": avg_read_time,
                "throughput_mbps": read_throughput
            })
            
            self.results["secure_service"]["writes"].append({
                "filename": filename,
                "size_mb": file_info["size_mb"],
                "time_s": avg_write_time,
                "throughput_mbps": write_throughput
            })
            
            print(f"    📊 Results: Read {read_throughput:.1f} MB/s, Write {write_throughput:.1f} MB/s")
    
    def benchmark_gov_service(self, test_files, cache_dir, iterations=3):
        """Benchmark government service with encryption simulation"""
        print("\n🏛️ Benchmarking Government Service for Large Files...")
        
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
            
            # Encrypt and store in chunks
            chunk_size = 64 * 1024 * 1024  # 64MB chunks
            with open(spath, "rb") as src, open(cpath, "wb") as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    encrypted_chunk = simple_encrypt(chunk)
                    dst.write(encrypted_chunk)
            
            return cpath
        
        for filename, file_info in test_files.items():
            size_bytes = file_info["size"]
            size_mb = file_info["size_mb"]
            
            print(f"  🔍 Testing {filename} ({size_mb} MB)...")
            
            # Warm up cache
            print("    🔥 Warming up cache with encryption...")
            cache_file = get_from_cache(filename)
            
            # Read benchmark (cache hits with decryption)
            read_times = []
            for i in range(iterations):
                print(f"    📖 Encrypted read iteration {i+1}/{iterations}...")
                start = time.perf_counter()
                
                # Read from cache and decrypt in chunks
                chunk_size = 64 * 1024 * 1024  # 64MB chunks
                with open(cache_file, "rb") as f:
                    while True:
                        encrypted_chunk = f.read(chunk_size + 10)  # +10 for encryption overhead
                        if not encrypted_chunk:
                            break
                        decrypted_chunk = simple_decrypt(encrypted_chunk)
                
                read_time = time.perf_counter() - start
                read_times.append(read_time)
                print(f"      Encrypted read time: {read_time:.2f}s")
            
            # Write benchmark (cache updates with encryption)
            write_times = []
            for i in range(iterations):
                print(f"    📝 Encrypted write iteration {i+1}/{iterations}...")
                start = time.perf_counter()
                
                # Write to cache with encryption in chunks
                chunk_size = 64 * 1024 * 1024  # 64MB chunks
                with open(cache_file, "wb") as f:
                    with open(file_info["path"], "rb") as source:
                        while True:
                            chunk = source.read(chunk_size)
                            if not chunk:
                                break
                            encrypted_chunk = simple_encrypt(chunk)
                            f.write(encrypted_chunk)
                
                write_time = time.perf_counter() - start
                write_times.append(write_time)
                print(f"      Encrypted write time: {write_time:.2f}s")
            
            avg_read_time = statistics.mean(read_times)
            avg_write_time = statistics.mean(write_times)
            read_throughput = (size_bytes / avg_read_time) / (1024 * 1024)
            write_throughput = (size_bytes / avg_write_time) / (1024 * 1024)
            
            self.results["gov_service"]["reads"].append({
                "filename": filename,
                "size_mb": file_info["size_mb"],
                "time_s": avg_read_time,
                "throughput_mbps": read_throughput
            })
            
            self.results["gov_service"]["writes"].append({
                "filename": filename,
                "size_mb": file_info["size_mb"],
                "time_s": avg_write_time,
                "throughput_mbps": write_throughput
            })
            
            print(f"    📊 Results: Read {read_throughput:.1f} MB/s, Write {write_throughput:.1f} MB/s")
    
    def run_extended_benchmark(self):
        """Run extended benchmark with large files"""
        print("🏁 Extended File I/O Benchmark Suite (100-500 MB)")
        print("=" * 70)
        
        # Test very large file sizes
        sizes_mb = [100, 200, 300, 400, 500]  # 100MB, 200MB, 300MB, 400MB, 500MB
        
        try:
            test_files, cache_dirs = self.create_large_test_files(sizes_mb)
            print(f"\n📁 Created {len(test_files)} large test files")
            
            # Run benchmarks with reduced iterations for large files
            self.benchmark_direct_io(test_files, iterations=3)
            self.benchmark_fast_service(test_files, cache_dirs["fast"], iterations=3)
            self.benchmark_secure_service(test_files, cache_dirs["secure"], iterations=3)
            self.benchmark_gov_service(test_files, cache_dirs["gov"], iterations=3)
            
        finally:
            if self.temp_dir and os.path.exists(self.temp_dir):
                print(f"\n🧹 Cleaning up temporary files...")
                shutil.rmtree(self.temp_dir)
        
        self.print_extended_summary_table()
    
    def print_extended_summary_table(self):
        """Print comprehensive summary table for large files"""
        print("\n" + "=" * 90)
        print("📊 СВОДНАЯ ТАБЛИЦА ПРОИЗВОДИТЕЛЬНОСТИ ДЛЯ БОЛЬШИХ ФАЙЛОВ (100-500 MB)")
        print("=" * 90)
        
        # Header
        print(f"{'Размер файла':<12} {'Метод':<15} {'Чтение (MB/s)':<15} {'Запись (MB/s)':<15} {'Чтение (с)':<12} {'Запись (с)':<12}")
        print("-" * 90)
        
        # Get unique file sizes
        sizes = sorted(set([result["size_mb"] for result in self.results["direct_io"]["reads"]]))
        
        for size_mb in sizes:
            print(f"\n📁 {size_mb} MB файлы:")
            
            # Direct I/O
            direct_read = next((r for r in self.results["direct_io"]["reads"] if r["size_mb"] == size_mb), None)
            direct_write = next((w for w in self.results["direct_io"]["writes"] if w["size_mb"] == size_mb), None)
            if direct_read and direct_write:
                print(f"{'':12} {'Прямое I/O':<15} {direct_read['throughput_mbps']:<15.1f} {direct_write['throughput_mbps']:<15.1f} {direct_read['time_s']:<12.2f} {direct_write['time_s']:<12.2f}")
            
            # Fast Service
            fast_read = next((r for r in self.results["fast_service"]["reads"] if r["size_mb"] == size_mb), None)
            fast_write = next((w for w in self.results["fast_service"]["writes"] if w["size_mb"] == size_mb), None)
            if fast_read and fast_write:
                print(f"{'':12} {'Быстрый кэш':<15} {fast_read['throughput_mbps']:<15.1f} {fast_write['throughput_mbps']:<15.1f} {fast_read['time_s']:<12.2f} {fast_write['time_s']:<12.2f}")
            
            # Secure Service
            secure_read = next((r for r in self.results["secure_service"]["reads"] if r["size_mb"] == size_mb), None)
            secure_write = next((w for w in self.results["secure_service"]["writes"] if w["size_mb"] == size_mb), None)
            if secure_read and secure_write:
                print(f"{'':12} {'Безопасный кэш':<15} {secure_read['throughput_mbps']:<15.1f} {secure_write['throughput_mbps']:<15.1f} {secure_read['time_s']:<12.2f} {secure_write['time_s']:<12.2f}")
            
            # Government Service
            gov_read = next((r for r in self.results["gov_service"]["reads"] if r["size_mb"] == size_mb), None)
            gov_write = next((w for w in self.results["gov_service"]["writes"] if w["size_mb"] == size_mb), None)
            if gov_read and gov_write:
                print(f"{'':12} {'Гос. кэш':<15} {gov_read['throughput_mbps']:<15.1f} {gov_write['throughput_mbps']:<15.1f} {gov_read['time_s']:<12.2f} {gov_write['time_s']:<12.2f}")
        
        # Performance comparison table
        print(f"\n" + "=" * 90)
        print("📈 СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ ОТНОСИТЕЛЬНО ПРЯМОГО I/O")
        print("=" * 90)
        
        print(f"{'Размер':<8} {'Быстрый кэш':<15} {'Безопасный кэш':<15} {'Гос. кэш':<15}")
        print(f"{'файла':<8} {'Чт/Зп':<7} {'Чт/Зп':<7} {'Чт/Зп':<7}")
        print("-" * 90)
        
        for size_mb in sizes:
            direct_read = next((r for r in self.results["direct_io"]["reads"] if r["size_mb"] == size_mb), None)
            direct_write = next((w for w in self.results["direct_io"]["writes"] if w["size_mb"] == size_mb), None)
            
            if direct_read and direct_write:
                # Fast service comparison
                fast_read = next((r for r in self.results["fast_service"]["reads"] if r["size_mb"] == size_mb), None)
                fast_write = next((w for w in self.results["fast_service"]["writes"] if w["size_mb"] == size_mb), None)
                fast_read_pct = ((fast_read['throughput_mbps'] / direct_read['throughput_mbps']) - 1) * 100 if fast_read else 0
                fast_write_pct = ((fast_write['throughput_mbps'] / direct_write['throughput_mbps']) - 1) * 100 if fast_write else 0
                
                # Secure service comparison
                secure_read = next((r for r in self.results["secure_service"]["reads"] if r["size_mb"] == size_mb), None)
                secure_write = next((w for w in self.results["secure_service"]["writes"] if w["size_mb"] == size_mb), None)
                secure_read_pct = ((secure_read['throughput_mbps'] / direct_read['throughput_mbps']) - 1) * 100 if secure_read else 0
                secure_write_pct = ((secure_write['throughput_mbps'] / direct_write['throughput_mbps']) - 1) * 100 if secure_write else 0
                
                # Government service comparison
                gov_read = next((r for r in self.results["gov_service"]["reads"] if r["size_mb"] == size_mb), None)
                gov_write = next((w for w in self.results["gov_service"]["writes"] if w["size_mb"] == size_mb), None)
                gov_read_pct = ((gov_read['throughput_mbps'] / direct_read['throughput_mbps']) - 1) * 100 if gov_read else 0
                gov_write_pct = ((gov_write['throughput_mbps'] / direct_write['throughput_mbps']) - 1) * 100 if gov_write else 0
                
                print(f"{size_mb:<8} {fast_read_pct:+6.1f}%/{fast_write_pct:+6.1f}% {secure_read_pct:+6.1f}%/{secure_write_pct:+6.1f}% {gov_read_pct:+6.1f}%/{gov_write_pct:+6.1f}%")
        
        # Summary statistics
        print(f"\n" + "=" * 90)
        print("📋 СВОДНАЯ СТАТИСТИКА ДЛЯ БОЛЬШИХ ФАЙЛОВ")
        print("=" * 90)
        
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
        
        print("=" * 90)


def main():
    benchmark = ExtendedFileIOBenchmark()
    benchmark.run_extended_benchmark()


if __name__ == "__main__":
    main()



