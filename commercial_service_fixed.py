"""
Fixed secure commercial service with all security improvements
"""

import os
import time
import re
from pathlib import Path
from typing import Optional
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware


# ===================== Configuration =====================

CACHE_DIR = os.getenv("HYBRIDCACHE_DIR", "/cache")
SOURCE_DIR = os.getenv("HYBRIDCACHE_SOURCE", "/source")
MAX_CACHE_SIZE = int(os.getenv("HYBRIDCACHE_MAXSIZE", str(100 * 1024 ** 3)))
CACHE_TTL = int(os.getenv("HYBRIDCACHE_TTL", str(60 * 60 * 24 * 7)))
ENABLE_ENCRYPTION = os.getenv("HYBRIDCACHE_ENCRYPTION", "0") == "1"

if ENABLE_ENCRYPTION:
    import base64
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    
    AES_KEY_ENV = os.getenv("HYBRIDCACHE_AES_KEY")
    if not AES_KEY_ENV:
        raise RuntimeError("HYBRIDCACHE_AES_KEY required when encryption enabled")
    AES_KEY = base64.b64decode(AES_KEY_ENV)
    if len(AES_KEY) != 32:
        raise ValueError("AES key must be 32 bytes")


# ===================== Rate Limiting =====================

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


# ===================== Utilities =====================

def ensure_dirs() -> None:
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)


def cache_path(filename: str) -> str:
    safe = filename.replace("/", "_").replace("\\", "_").replace("..", "")
    return str(Path(CACHE_DIR) / safe)


def validate_filename(name: str) -> bool:
    """Enhanced filename validation with security checks"""
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


def is_expired(filepath: str) -> bool:
    try:
        return (time.time() - os.path.getmtime(filepath)) > CACHE_TTL
    except Exception:
        return True


def enforce_cache_limit() -> None:
    """Simple LRU cache eviction"""
    try:
        files = []
        for name in os.listdir(CACHE_DIR):
            cp = cache_path(name)
            try:
                mtime = os.path.getmtime(cp)
                size = os.path.getsize(cp)
                files.append((name, mtime, size))
            except Exception:
                continue
        
        total = sum(size for _, _, size in files)
        if total <= MAX_CACHE_SIZE:
            return
            
        files.sort(key=lambda x: x[1])  # sort by mtime
        for name, _, size in files:
            if total <= MAX_CACHE_SIZE:
                break
            try:
                os.remove(cache_path(name))
                total -= size
            except Exception:
                continue
    except Exception:
        pass


# ===================== Encryption =====================

def encrypt_data(data: bytes) -> bytes:
    if not ENABLE_ENCRYPTION:
        return data
    import secrets
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CTR(iv), backend=default_backend())
    enc = cipher.encryptor()
    return iv + enc.update(data) + enc.finalize()


def decrypt_data(data: bytes) -> bytes:
    if not ENABLE_ENCRYPTION:
        return data
    iv = data[:16]
    ct = data[16:]
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CTR(iv), backend=default_backend())
    dec = cipher.decryptor()
    return dec.update(ct) + dec.finalize()


# ===================== Core cache operations =====================

def get_from_cache(filename: str, src_dir: Optional[str] = None) -> str:
    ensure_dirs()
    cpath = cache_path(filename)
    spath = str(Path(src_dir or SOURCE_DIR) / filename)

    # Fast cache hit check
    if os.path.exists(cpath) and not is_expired(cpath):
        return cpath

    # Cache miss - load from source
    if not os.path.exists(spath):
        raise FileNotFoundError(f"Source not found: {spath}")

    with open(spath, "rb") as f:
        raw_data = f.read()

    # Write to cache
    data = encrypt_data(raw_data)
    with open(cpath, "wb") as f:
        f.write(data)

    enforce_cache_limit()
    return cpath


def preload_files(filelist: list, src_dir: Optional[str] = None) -> None:
    for name in filelist:
        try:
            get_from_cache(name, src_dir)
        except Exception:
            pass


# ===================== HTTP API =====================

app = FastAPI(title="Secure Commercial HybridCache", version="2.1-secure")

# Security middleware
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

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/api/cache/{filename}")
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
        raise HTTPException(status_code=500, detail="Internal error")


@app.post("/api/preload")
def api_preload(payload: dict, request: Request):
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        files = [f for f in payload.get("files", []) if isinstance(f, str) and validate_filename(f)]
        if not files:
            return JSONResponse({"error": "No valid files"}, status_code=400)
        preload_files(files)
        return {"status": "preloading", "files": files}
    except Exception as e:
        return JSONResponse({"error": "Internal error"}, status_code=500)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "HybridCache Secure"}


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()

    ensure_dirs()
    uvicorn.run("commercial_service_fixed:app", host=args.host, port=args.port, reload=False)



