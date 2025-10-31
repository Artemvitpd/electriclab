#!/usr/bin/env python3
"""
Коммерческий сервис HybridCache с системой лицензирования
Поддерживает демо-режим и полные лицензии
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

# Импортируем систему лицензий
from demo_license_system import get_license_system


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


# ===================== License Integration =====================

def check_license_limits(request_type: str = "file_access") -> tuple[bool, str]:
    """Проверяем лицензионные ограничения"""
    license_system = get_license_system()
    
    # Проверяем статус лицензии
    is_valid, status_msg = license_system.check_license_status()
    if not is_valid:
        return False, f"License issue: {status_msg}"
    
    # Проверяем лимит запросов
    req_ok, req_msg = license_system.check_request_limit()
    if not req_ok:
        return False, f"Request limit: {req_msg}"
    
    # Увеличиваем счетчик запросов
    license_system.increment_request_count()
    
    return True, "License check passed"


def check_cache_limits(current_size_bytes: int, file_count: int) -> tuple[bool, str]:
    """Проверяем ограничения кэша"""
    license_system = get_license_system()
    
    # Проверяем размер кэша
    cache_ok, cache_msg = license_system.check_cache_size_limit(current_size_bytes)
    if not cache_ok:
        return False, cache_msg
    
    # Проверяем количество файлов
    file_ok, file_msg = license_system.check_file_limit(file_count)
    if not file_ok:
        return False, file_msg
    
    # Обновляем статистику
    license_system.update_cache_size(current_size_bytes)
    
    return True, "Cache limits OK"


def has_feature_access(feature: str) -> bool:
    """Проверяем доступ к функции"""
    license_system = get_license_system()
    return license_system.has_feature(feature)


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


def get_cache_stats() -> dict:
    """Получаем статистику кэша"""
    try:
        files = []
        total_size = 0
        file_count = 0
        
        for name in os.listdir(CACHE_DIR):
            if name.endswith('.sha256'):
                continue
            cp = cache_path(name)
            try:
                size = os.path.getsize(cp)
                files.append((name, size))
                total_size += size
                file_count += 1
            except Exception:
                continue
        
        return {
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": total_size // (1024 * 1024),
            "files": files[:10]  # Первые 10 файлов для примера
        }
    except Exception:
        return {"file_count": 0, "total_size_bytes": 0, "total_size_mb": 0}


def enforce_cache_limit() -> None:
    """Simple LRU cache eviction with license limits"""
    license_system = get_license_system()
    cache_stats = get_cache_stats()
    
    # Проверяем лицензионные ограничения
    cache_ok, cache_msg = license_system.check_cache_size_limit(cache_stats["total_size_bytes"])
    file_ok, file_msg = license_system.check_file_limit(cache_stats["file_count"])
    
    if cache_ok and file_ok:
        return  # Все в пределах лимитов
    
    # Если превышены лимиты, удаляем старые файлы
    try:
        files = []
        for name in os.listdir(CACHE_DIR):
            if name.endswith('.sha256'):
                continue
            cp = cache_path(name)
            try:
                mtime = os.path.getmtime(cp)
                size = os.path.getsize(cp)
                files.append((name, mtime, size))
            except Exception:
                continue
        
        files.sort(key=lambda x: x[1])  # sort by mtime
        
        # Удаляем файлы пока не уложимся в лимиты
        for name, _, size in files:
            cache_stats = get_cache_stats()
            
            cache_ok, _ = license_system.check_cache_size_limit(cache_stats["total_size_bytes"])
            file_ok, _ = license_system.check_file_limit(cache_stats["file_count"])
            
            if cache_ok and file_ok:
                break
            
            try:
                os.remove(cache_path(name))
                # Удаляем соответствующий .sha256 файл если есть
                sha256_path = cache_path(name) + ".sha256"
                if os.path.exists(sha256_path):
                    os.remove(sha256_path)
            except Exception:
                continue
                
    except Exception:
        pass


# ===================== Encryption =====================

def encrypt_data(data: bytes) -> bytes:
    """Шифрование данных с проверкой лицензии"""
    if not has_feature_access("aes_encryption"):
        raise HTTPException(status_code=402, detail="AES encryption requires full license")
    
    if not ENABLE_ENCRYPTION:
        return data
    
    import secrets
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CTR(iv), backend=default_backend())
    enc = cipher.encryptor()
    return iv + enc.update(data) + enc.finalize()


def decrypt_data(data: bytes) -> bytes:
    """Расшифровка данных с проверкой лицензии"""
    if not has_feature_access("aes_encryption"):
        raise HTTPException(status_code=402, detail="AES decryption requires full license")
    
    if not ENABLE_ENCRYPTION:
        return data
    
    iv = data[:16]
    ct = data[16:]
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CTR(iv), backend=default_backend())
    dec = cipher.decryptor()
    return dec.update(ct) + dec.finalize()


# ===================== Core cache operations =====================

def get_from_cache(filename: str, src_dir: Optional[str] = None) -> str:
    """Получение файла из кэша с проверкой лицензии"""
    # Проверяем лицензионные ограничения
    license_ok, license_msg = check_license_limits("file_access")
    if not license_ok:
        raise HTTPException(status_code=402, detail=f"License limit: {license_msg}")
    
    # Validate filename first
    if not validate_filename(filename):
        raise ValueError(f"Invalid filename: {filename}")
    
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

    # Write to cache with encryption
    data = encrypt_data(raw_data)
    with open(cpath, "wb") as f:
        f.write(data)

    # Проверяем ограничения после добавления файла
    cache_stats = get_cache_stats()
    limits_ok, limits_msg = check_cache_limits(cache_stats["total_size_bytes"], cache_stats["file_count"])
    if not limits_ok:
        # Удаляем только что добавленный файл
        try:
            os.remove(cpath)
        except Exception:
            pass
        raise HTTPException(status_code=402, detail=f"Cache limit: {limits_msg}")
    
    # Увеличиваем счетчик файлов
    license_system = get_license_system()
    license_system.increment_file_count()
    
    enforce_cache_limit()
    return cpath


def preload_files(filelist: list, src_dir: Optional[str] = None) -> None:
    """Предварительная загрузка файлов с проверкой лицензии"""
    license_system = get_license_system()
    
    for name in filelist:
        try:
            if validate_filename(name):
                # Проверяем лимит файлов перед загрузкой
                cache_stats = get_cache_stats()
                file_ok, file_msg = license_system.check_file_limit(cache_stats["file_count"])
                
                if not file_ok:
                    print(f"File limit reached: {file_msg}")
                    break
                
                get_from_cache(name, src_dir)
        except Exception as e:
            print(f"Preload failed for {name}: {e}")


# ===================== HTTP API =====================

app = FastAPI(title="Licensed Commercial HybridCache", version="2.2-licensed")

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/api/license")
def get_license_info():
    """Получаем информацию о лицензии"""
    license_system = get_license_system()
    return license_system.get_license_info()


@app.post("/api/license/activate")
def activate_license(payload: dict):
    """Активация полной лицензии"""
    license_key = payload.get("license_key")
    if not license_key:
        return JSONResponse({"error": "License key required"}, status_code=400)
    
    license_system = get_license_system()
    success, message = license_system.activate_full_license(license_key)
    
    if success:
        return {"status": "success", "message": message}
    else:
        return JSONResponse({"error": message}, status_code=400)


@app.get("/api/cache/{filename}")
def api_get_file(filename: str, request: Request):
    """Получение файла с проверкой лицензии"""
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Enhanced filename validation
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
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error")


@app.post("/api/preload")
def api_preload(payload: dict, request: Request):
    """Предварительная загрузка с проверкой лицензии"""
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


@app.get("/api/stats")
def get_stats():
    """Получаем статистику использования"""
    license_system = get_license_system()
    cache_stats = get_cache_stats()
    
    return {
        "cache_stats": cache_stats,
        "license_info": license_system.get_license_info(),
        "timestamp": time.time()
    }


@app.get("/health")
def health_check():
    """Проверка здоровья сервиса"""
    license_system = get_license_system()
    is_valid, status_msg = license_system.check_license_status()
    
    return {
        "status": "healthy" if is_valid else "license_issue",
        "service": "HybridCache Licensed",
        "license_status": status_msg
    }


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()

    ensure_dirs()
    
    # Показываем информацию о лицензии при запуске
    license_system = get_license_system()
    is_valid, status_msg = license_system.check_license_status()
    print(f"License Status: {status_msg}")
    
    if not is_valid:
        print("WARNING: License issues detected. Service may have limited functionality.")
    
    uvicorn.run("commercial_service_licensed:app", host=args.host, port=args.port, reload=False)

