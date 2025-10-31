#!/usr/bin/env python3
"""
Simple performance test comparing security overhead
"""

import os
import time
import tempfile
import random
from pathlib import Path


def test_validation_overhead():
    """Test filename validation overhead"""
    print("=== Validation Overhead Test ===")
    
    # Original simple validation
    def original_validation(name: str) -> bool:
        import re
        return re.fullmatch(r"[A-Za-z0-9._-]+", name) is not None
    
    # Enhanced secure validation
    def secure_validation(name: str) -> bool:
        import re
        if not name or len(name) > 255:
            return False
        dangerous_patterns = [
            r'\.\.',  # Parent directory
            r'/',     # Forward slash
            r'\\\\',  # Backslash
            r'%2e%2e',  # URL encoded ..
            r'%2f',     # URL encoded /
            r'%5c',     # URL encoded \\
            r'\x00',    # Null byte
            r'[<>:"|?*]'  # Windows forbidden chars
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False
        return re.fullmatch(r"[A-Za-z0-9._-]+", name) is not None
    
    test_names = [
        "valid_file.txt",
        "../../../etc/passwd",
        "test.txt; cat /etc/passwd",
        "<script>alert('xss')</script>",
        "normal_file.bin",
        "file_with_.._traversal.txt",
        "file%2fwith%2fencoded.txt",
        "file\x00null.txt",
        "file<forbidden>chars.txt"
    ]
    
    # Test original validation
    start = time.perf_counter()
    for _ in range(10000):
        for name in test_names:
            original_validation(name)
    original_time = time.perf_counter() - start
    
    # Test secure validation
    start = time.perf_counter()
    for _ in range(10000):
        for name in test_names:
            secure_validation(name)
    secure_time = time.perf_counter() - start
    
    overhead = (secure_time - original_time) / original_time * 100
    per_call_overhead = (secure_time - original_time) / (10000 * len(test_names))
    
    print(f"Original validation: {original_time*1000:.2f} ms")
    print(f"Secure validation: {secure_time*1000:.2f} ms")
    print(f"Overhead: {overhead:.2f}%")
    print(f"Per call overhead: {per_call_overhead*1000000:.2f} μs")
    
    return per_call_overhead


def test_rate_limiting_overhead():
    """Test rate limiting overhead"""
    print("\n=== Rate Limiting Overhead Test ===")
    
    from collections import defaultdict, deque
    
    def simple_rate_limit(client_ip: str, max_requests: int = 100, window: int = 60):
        """Simple rate limiting implementation"""
        now = time.time()
        if not hasattr(simple_rate_limit, '_requests'):
            simple_rate_limit._requests = defaultdict(lambda: deque())
        
        client_requests = simple_rate_limit._requests[client_ip]
        
        # Remove old requests
        while client_requests and client_requests[0] < now - window:
            client_requests.popleft()
        
        if len(client_requests) >= max_requests:
            return False
        
        client_requests.append(now)
        return True
    
    # Test rate limiting overhead
    start = time.perf_counter()
    for _ in range(1000):
        simple_rate_limit("127.0.0.1")
    rate_limit_time = time.perf_counter() - start
    
    per_call_overhead = rate_limit_time / 1000
    
    print(f"Rate limiting: {rate_limit_time*1000:.2f} ms for 1000 calls")
    print(f"Per call overhead: {per_call_overhead*1000000:.2f} μs")
    
    return per_call_overhead


def test_file_size_check_overhead():
    """Test file size checking overhead"""
    print("\n=== File Size Check Overhead Test ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files of different sizes
        test_files = []
        sizes = [1024, 1024*1024, 10*1024*1024]  # 1KB, 1MB, 10MB
        
        for i, size in enumerate(sizes):
            test_file = Path(temp_dir) / f"test_{i}.bin"
            with open(test_file, "wb") as f:
                f.write(b"x" * size)
            test_files.append(test_file)
        
        # Test file size checking
        start = time.perf_counter()
        for _ in range(1000):
            for file_path in test_files:
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:  # 10MB limit
                    pass  # Reject
        size_check_time = time.perf_counter() - start
        
        per_call_overhead = size_check_time / (1000 * len(test_files))
        
        print(f"File size checks: {size_check_time*1000:.2f} ms for 1000*{len(test_files)} checks")
        print(f"Per call overhead: {per_call_overhead*1000000:.2f} μs")
        
        return per_call_overhead


def test_security_headers_overhead():
    """Test security headers overhead"""
    print("\n=== Security Headers Overhead Test ===")
    
    def add_security_headers():
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        }
        return headers
    
    start = time.perf_counter()
    for _ in range(10000):
        add_security_headers()
    headers_time = time.perf_counter() - start
    
    per_call_overhead = headers_time / 10000
    
    print(f"Security headers: {headers_time*1000:.2f} ms for 10000 calls")
    print(f"Per call overhead: {per_call_overhead*1000000:.2f} μs")
    
    return per_call_overhead


def main():
    print("🔒 Security Performance Impact Analysis")
    print("=" * 50)
    
    # Run all overhead tests
    validation_overhead = test_validation_overhead()
    rate_limit_overhead = test_rate_limiting_overhead()
    size_check_overhead = test_file_size_check_overhead()
    headers_overhead = test_security_headers_overhead()
    
    # Calculate total overhead
    total_overhead = (validation_overhead + rate_limit_overhead + 
                     size_check_overhead + headers_overhead)
    
    print("\n" + "=" * 50)
    print("📊 SECURITY OVERHEAD SUMMARY")
    print("=" * 50)
    print(f"{'Component':<25} {'Overhead (μs)':<15}")
    print("-" * 40)
    print(f"{'Enhanced Validation':<25} {validation_overhead*1000000:<15.2f}")
    print(f"{'Rate Limiting':<25} {rate_limit_overhead*1000000:<15.2f}")
    print(f"{'File Size Checks':<25} {size_check_overhead*1000000:<15.2f}")
    print(f"{'Security Headers':<25} {headers_overhead*1000000:<15.2f}")
    print("-" * 40)
    print(f"{'TOTAL OVERHEAD':<25} {total_overhead*1000000:<15.2f}")
    
    print("\n" + "=" * 50)
    print("🎯 PERFORMANCE IMPACT ANALYSIS")
    print("=" * 50)
    
    # Typical request processing time (estimated)
    typical_request_time = 10 * 1000  # 10ms in microseconds
    
    impact_percentage = (total_overhead / (typical_request_time / 1000000)) * 100
    
    print(f"Typical request time: {typical_request_time:.0f} μs")
    print(f"Security overhead: {total_overhead*1000000:.2f} μs")
    print(f"Performance impact: {impact_percentage:.3f}%")
    
    if impact_percentage < 1:
        print("\n✅ IMPACT: NEGLIGIBLE (< 1%)")
        print("Security improvements have minimal performance cost")
    elif impact_percentage < 5:
        print("\n✅ IMPACT: MINIMAL (1-5%)")
        print("Security improvements have acceptable performance cost")
    elif impact_percentage < 15:
        print("\n⚠️  IMPACT: MODERATE (5-15%)")
        print("Security improvements have noticeable but acceptable cost")
    else:
        print("\n🚨 IMPACT: SIGNIFICANT (> 15%)")
        print("Security improvements have high performance cost")
    
    print("\nSecurity Benefits:")
    print("  ✓ Path traversal protection")
    print("  ✓ Rate limiting (DoS protection)")
    print("  ✓ File size limits")
    print("  ✓ Security headers")
    print("  ✓ Enhanced input validation")
    
    print(f"\nRecommendation: {'Accept' if impact_percentage < 10 else 'Consider optimizing'} the {impact_percentage:.2f}% performance cost for comprehensive security")
    
    print("=" * 50)


if __name__ == "__main__":
    main()



