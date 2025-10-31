#!/usr/bin/env python3
"""
Security fixes for HybridCache Services
Addresses vulnerabilities found in security testing
"""

import os
import re
import time
import secrets
from pathlib import Path


def fix_commercial_service_fast():
    """Apply security fixes to commercial_service_fast.py"""
    print("Applying security fixes to commercial_service_fast.py...")
    
    # Read current file
    with open("commercial_service_fast.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Fix 1: Enhanced filename validation
    old_validation = '''def validate_filename(name: str) -> bool:
    import re
    return re.fullmatch(r"[A-Za-z0-9._-]+", name) is not None'''
    
    new_validation = '''def validate_filename(name: str) -> bool:
    import re
    # Enhanced validation: only alphanumeric, dots, dashes, underscores
    # No path separators, no special chars, max 255 chars
    if not name or len(name) > 255:
        return False
    # Block path traversal patterns
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
    return re.fullmatch(r"[A-Za-z0-9._-]+", name) is not None'''
    
    content = content.replace(old_validation, new_validation)
    
    # Fix 2: Add rate limiting
    rate_limiting_code = '''
# Rate limiting
from collections import defaultdict, deque
import time

_rate_limits = defaultdict(lambda: deque())

def check_rate_limit(client_ip: str, max_requests: int = 100, window: int = 60) -> bool:
    """Check if client exceeded rate limit"""
    now = time.time()
    client_requests = _rate_limits[client_ip]
    
    # Remove old requests outside window
    while client_requests and client_requests[0] < now - window:
        client_requests.popleft()
    
    # Check if limit exceeded
    if len(client_requests) >= max_requests:
        return False
    
    # Add current request
    client_requests.append(now)
    return True
'''
    
    # Insert rate limiting after imports
    content = content.replace(
        "from fastapi import FastAPI, HTTPException",
        "from fastapi import FastAPI, HTTPException, Request" + rate_limiting_code
    )
    
    # Fix 3: Add request size limits and timeout handling
    old_get_file = '''@app.get("/api/cache/{filename}")
def api_get_file(filename: str):
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    try:
        path = get_from_cache(filename)
        # Serve decrypted content
        with open(path, "rb") as f:
            data = f.read()
        raw = decrypt_data(data)
        
        # Create temp file for response
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(raw)
        tmp.close()
        
        return FileResponse(tmp.name, media_type="application/octet-stream", filename=filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error")'''
    
    new_get_file = '''@app.get("/api/cache/{filename}")
def api_get_file(filename: str, request: Request):
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Enhanced filename validation
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # File size limit (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    try:
        path = get_from_cache(filename)
        
        # Check file size before reading
        file_size = os.path.getsize(path)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Serve decrypted content
        with open(path, "rb") as f:
            data = f.read()
        raw = decrypt_data(data)
        
        # Create temp file for response
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(raw)
        tmp.close()
        
        return FileResponse(tmp.name, media_type="application/octet-stream", filename=filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error")'''
    
    content = content.replace(old_get_file, new_get_file)
    
    # Fix 4: Add security headers middleware
    security_middleware = '''
# Security middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
'''
    
    # Insert after app creation
    content = content.replace(
        "app = FastAPI(title=\"Fast Commercial HybridCache\", version=\"2.1-fast\")",
        "app = FastAPI(title=\"Fast Commercial HybridCache\", version=\"2.1-fast\")" + security_middleware
    )
    
    # Write fixed file
    with open("commercial_service_fast_secure.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✓ Created commercial_service_fast_secure.py with security fixes")


def create_secure_benchmark():
    """Create secure version of benchmark"""
    print("Creating secure benchmark...")
    
    secure_benchmark = '''#!/usr/bin/env python3
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
    print("\\n🔒 Running Security Tests...")
    
    # Test 1: Path traversal
    test_cases = [
        "../../../etc/passwd",
        "..\\\\..\\\\..\\\\windows\\\\system32\\\\drivers\\\\etc\\\\hosts",
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
    print("\\n⚡ Running Performance Tests...")
    
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
    
    print("\\n" + "=" * 40)
    if security_ok and performance_ok:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 40)


if __name__ == "__main__":
    main()
'''
    
    with open("secure_benchmark.py", "w", encoding="utf-8") as f:
        f.write(secure_benchmark)
    
    print("✓ Created secure_benchmark.py")


def main():
    """Apply all security fixes"""
    print("🔒 Applying Security Fixes to HybridCache")
    print("=" * 50)
    
    fix_commercial_service_fast()
    create_secure_benchmark()
    
    print("\\n" + "=" * 50)
    print("✅ SECURITY FIXES APPLIED")
    print("=" * 50)
    print("\\nNew files created:")
    print("  - commercial_service_fast_secure.py")
    print("  - secure_benchmark.py")
    print("\\nSecurity improvements:")
    print("  ✓ Enhanced path traversal protection")
    print("  ✓ Rate limiting (100 req/min per IP)")
    print("  ✓ File size limits (10MB max)")
    print("  ✓ Security headers")
    print("  ✓ Input validation")
    print("  ✓ CORS configuration")
    print("=" * 50)


if __name__ == "__main__":
    main()



