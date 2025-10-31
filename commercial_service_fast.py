"""
Optimized commercial service for maximum speed:
- No integrity checks (.sha256 files)
- No access counting overhead
- Minimal file operations
- Direct cache hit/miss logic
"""

import os
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse


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


# ===================== Utilities =====================

def ensure_dirs() -> None:
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)


def cache_path(filename: str) -> str:
    safe = filename.replace("/", "_").replace("\\", "_").replace("..", "")
    return str(Path(CACHE_DIR) / safe)


def is_expired(filepath: str) -> bool:
    try:
        return (time.time() - os.path.getmtime(filepath)) > CACHE_TTL
    except Exception:
        return True


def enforce_cache_limit() -> None:
    # Simple LRU: remove oldest files
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

app = FastAPI(title="Fast Commercial HybridCache", version="2.1-fast")


def validate_filename(name: str) -> bool:
    import re
    return re.fullmatch(r"[A-Za-z0-9._-]+", name) is not None


@app.get("/api/cache/{filename}")
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
        raise HTTPException(status_code=500, detail="Internal error")


@app.post("/api/preload")
def api_preload(payload: dict):
    try:
        files = [f for f in payload.get("files", []) if isinstance(f, str) and validate_filename(f)]
        if not files:
            return JSONResponse({"error": "No valid files"}, status_code=400)
        preload_files(files)
        return {"status": "preloading", "files": files}
    except Exception as e:
        return JSONResponse({"error": "Internal error"}, status_code=500)


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()

    ensure_dirs()
    uvicorn.run("commercial_service_fast:app", host=args.host, port=args.port, reload=False)
