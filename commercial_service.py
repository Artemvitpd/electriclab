"""
Commercial HybridCache service:
- AES-256 CTR encryption via cryptography
- Optional encryption toggled by HYBRIDCACHE_ENCRYPTION
- Basic logging and integrity hashes for safety
- Simple HTTP API using FastAPI

Environment:
  HYBRIDCACHE_DIR        Cache directory (default: /cache)
  HYBRIDCACHE_SOURCE     Source directory for original files (default: /source)
  HYBRIDCACHE_MAXSIZE    Max cache size in bytes (default: 107374182400)
  HYBRIDCACHE_TTL        TTL seconds (default: 604800)
  HYBRIDCACHE_ENCRYPTION Enable encryption ("1"|"0", default: "1")
  HYBRIDCACHE_AES_KEY    Base64 32-byte key when encryption enabled

Run:
  python commercial_service.py --host 0.0.0.0 --port 8081
"""

import os
import time
import json
import base64
import hashlib
import logging
import secrets
from typing import List, Optional
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


# ===================== Configuration =====================

CACHE_DIR = os.getenv("HYBRIDCACHE_DIR", "/cache")
SOURCE_DIR = os.getenv("HYBRIDCACHE_SOURCE", "/source")
MAX_CACHE_SIZE = int(os.getenv("HYBRIDCACHE_MAXSIZE", str(100 * 1024 ** 3)))
CACHE_TTL = int(os.getenv("HYBRIDCACHE_TTL", str(60 * 60 * 24 * 7)))
ENABLE_ENCRYPTION = os.getenv("HYBRIDCACHE_ENCRYPTION", "1") == "1"

AES_KEY_ENV = os.getenv("HYBRIDCACHE_AES_KEY")
AES_KEY: Optional[bytes] = None
if ENABLE_ENCRYPTION:
    if not AES_KEY_ENV:
        raise RuntimeError("HYBRIDCACHE_AES_KEY is required when encryption is enabled")
    try:
        AES_KEY = base64.b64decode(AES_KEY_ENV)
        if len(AES_KEY) != 32:
            raise ValueError("AES key must be 32 bytes")
    except Exception as e:
        raise RuntimeError(f"Failed to load AES key: {e}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [APP] %(message)s")

ACCESS_COUNT_FILE = str(Path(CACHE_DIR) / ".access_count.json")
access_counts = defaultdict(int)


# ===================== Utilities =====================

def ensure_dirs() -> None:
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)


def load_access_counts() -> None:
    if Path(ACCESS_COUNT_FILE).exists():
        try:
            with open(ACCESS_COUNT_FILE, "r", encoding="utf-8") as f:
                access_counts.update(json.load(f))
        except Exception:
            pass


def save_access_counts() -> None:
    try:
        with open(ACCESS_COUNT_FILE, "w", encoding="utf-8") as f:
            json.dump(dict(access_counts), f)
    except Exception:
        pass


def cache_path(filename: str) -> str:
    safe = filename.replace("/", "_").replace("\\", "_").replace("..", "")
    return str(Path(CACHE_DIR) / safe)


def integrity_path(cpath: str) -> str:
    return f"{cpath}.sha256"


def is_expired(filepath: str) -> bool:
    try:
        return (time.time() - os.path.getmtime(filepath)) > CACHE_TTL
    except Exception:
        return True


def enforce_cache_limit() -> None:
    load_access_counts()
    entries = []
    try:
        for name in os.listdir(CACHE_DIR):
            if name.endswith(".sha256") or name == ".access_count.json":
                continue
            cp = cache_path(name)
            try:
                mtime = os.path.getmtime(cp)
                size = os.path.getsize(cp)
                score = mtime + access_counts.get(name, 0) * 86400
                entries.append((name, score, size))
            except Exception:
                continue
        total = sum(s for _, _, s in entries)
        if total <= MAX_CACHE_SIZE:
            return
        entries.sort(key=lambda x: x[1])
        for name, _, size in entries:
            if total <= MAX_CACHE_SIZE:
                break
            try:
                cp = cache_path(name)
                os.remove(cp)
                ip = integrity_path(cp)
                if os.path.exists(ip):
                    os.remove(ip)
                access_counts.pop(name, None)
                total -= size
                logging.warning(f"Evicted from cache: {name}")
            except Exception:
                continue
    finally:
        save_access_counts()


# ===================== Encryption (AES CTR) =====================

def aes_encrypt(data: bytes) -> bytes:
    if not ENABLE_ENCRYPTION:
        return data
    assert AES_KEY is not None
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CTR(iv), backend=default_backend())
    enc = cipher.encryptor()
    return iv + enc.update(data) + enc.finalize()


def aes_decrypt(data: bytes) -> bytes:
    if not ENABLE_ENCRYPTION:
        return data
    assert AES_KEY is not None
    iv = data[:16]
    ct = data[16:]
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CTR(iv), backend=default_backend())
    dec = cipher.decryptor()
    return dec.update(ct) + dec.finalize()


# ===================== Core cache operations =====================

def get_from_cache(filename: str, src_dir: Optional[str] = None) -> str:
    ensure_dirs()
    load_access_counts()
    cpath = cache_path(filename)
    ipath = integrity_path(cpath)
    spath = str(Path(src_dir or SOURCE_DIR) / filename)

    access_counts[filename] += 1
    save_access_counts()

    if os.path.exists(cpath) and not is_expired(cpath):
        try:
            with open(cpath, "rb") as f:
                content = f.read()
            raw = aes_decrypt(content)
            if os.path.exists(ipath):
                with open(ipath, "r", encoding="utf-8") as f:
                    stored = f.read().strip()
                if hashlib.sha256(raw).hexdigest() == stored:
                    os.utime(cpath, None)
                    logging.info(f"Cache hit (integrity OK): {filename}")
                    return cpath
        except Exception as e:
            logging.warning(f"Cache validation failed for {filename}: {e}")
            for p in [cpath, ipath]:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

    if not os.path.exists(spath):
        raise FileNotFoundError(f"Source not found: {spath}")

    with open(spath, "rb") as f:
        raw = f.read()

    with open(ipath, "w", encoding="utf-8") as f:
        f.write(hashlib.sha256(raw).hexdigest())

    data = aes_encrypt(raw)
    with open(cpath, "wb") as f:
        f.write(data)

    enforce_cache_limit()
    logging.info(f"Cached: {filename}")
    return cpath


def preload_files(filelist: List[str], src_dir: Optional[str] = None) -> None:
    for name in filelist:
        try:
            get_from_cache(name, src_dir)
            logging.info(f"Preloaded: {name}")
        except Exception as e:
            logging.error(f"Preload failed for {name}: {e}")


# ===================== HTTP API =====================

app = FastAPI(title="Commercial HybridCache", version="2.1-aes")


def validate_filename(name: str) -> bool:
    import re

    return re.fullmatch(r"[A-Za-z0-9._-]+", name) is not None


@app.get("/api/cache/{filename}")
def api_get_file(filename: str):
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    try:
        path = get_from_cache(filename)
        tmp = Path(cache_path(f"tmp_{hashlib.sha256(filename.encode()).hexdigest()}"))
        with open(path, "rb") as f:
            data = f.read()
        raw = aes_decrypt(data)
        with open(tmp, "wb") as f:
            f.write(raw)
        resp = FileResponse(str(tmp), media_type="application/octet-stream", filename=filename)
        try:
            os.remove(tmp)
        except Exception:
            pass
        return resp
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logging.error(f"API get_file error: {e}")
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
        logging.error(f"API preload error: {e}")
        return JSONResponse({"error": "Internal error"}, status_code=500)


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()

    ensure_dirs()
    load_access_counts()
    uvicorn.run("commercial_service:app", host=args.host, port=args.port, reload=False)



