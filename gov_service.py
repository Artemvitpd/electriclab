"""
Gov-oriented HybridCache service (FSTEC-style):
- GOST 34.12-2015 CTR encryption via pygost
- Integrity hashes (.sha256) per cached file
- Access counts and cache eviction by score (mtime + access weight)
- Simple HTTP API using FastAPI

Environment variables:
  HYBRIDCACHE_DIR          Cache directory (default: /cache)
  HYBRIDCACHE_SOURCE       Source directory for original files (default: /source)
  HYBRIDCACHE_MAXSIZE      Max cache size in bytes (default: 107374182400, 100 GiB)
  HYBRIDCACHE_TTL          TTL seconds (default: 604800)
  HYBRIDCACHE_ENCRYPTION   Enable encryption ("1"|"0", default: "1")
  HYBRIDCACHE_SECURITY_LOG Security log path (default: security.log)

Run:
  python gov_service.py --host 0.0.0.0 --port 8080
"""

import os
import time
import json
import hashlib
import logging
import secrets
from typing import List, Optional
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

# Preferred: GOST via pygost; fallback: AES-256 CTR via cryptography when pygost unavailable
HAS_PYGOST = True
try:
    from pygost.gost3412 import GOST34122015  # type: ignore
    from pygost.gost3413 import ctr  # type: ignore
except Exception:
    HAS_PYGOST = False
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # type: ignore
    from cryptography.hazmat.backends import default_backend  # type: ignore


# ===================== Configuration =====================

CACHE_DIR = os.getenv("HYBRIDCACHE_DIR", "/cache")
SOURCE_DIR = os.getenv("HYBRIDCACHE_SOURCE", "/source")
MAX_CACHE_SIZE = int(os.getenv("HYBRIDCACHE_MAXSIZE", str(100 * 1024 ** 3)))
CACHE_TTL = int(os.getenv("HYBRIDCACHE_TTL", str(60 * 60 * 24 * 7)))
ENABLE_ENCRYPTION = os.getenv("HYBRIDCACHE_ENCRYPTION", "1") == "1"
# Fallback AES key (Base64 32 bytes) if pygost is not available
GOV_AES_KEY_ENV = os.getenv("GOV_AES_KEY")
SECURITY_LOG = os.getenv("HYBRIDCACHE_SECURITY_LOG", "security.log")

ACCESS_COUNT_FILE = str(Path(CACHE_DIR) / ".access_count.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SECURITY] %(message)s",
    handlers=[logging.FileHandler(SECURITY_LOG, encoding="utf-8"), logging.StreamHandler()],
)

access_counts = defaultdict(int)


# ===================== Utilities =====================

def ensure_dirs() -> None:
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)


def load_access_counts() -> None:
    if Path(ACCESS_COUNT_FILE).exists():
        try:
            with open(ACCESS_COUNT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                access_counts.update({str(k): int(v) for k, v in data.items()})
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


# ===================== Encryption (GOST CTR) =====================

def gost_encrypt(data: bytes) -> bytes:
    if not HAS_PYGOST:
        # AES fallback
        key = None
        if GOV_AES_KEY_ENV:
            try:
                import base64

                key = base64.b64decode(GOV_AES_KEY_ENV)
            except Exception:
                key = None
        if not key or len(key) != 32:
            key = hashlib.sha256(b"gov_fallback_demo_key").digest()[:32]
        iv = secrets.token_bytes(16)
        cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
        enc = cipher.encryptor()
        return iv + enc.update(data) + enc.finalize()
    # GOST path
    key = hashlib.sha256(b"gov_default_key_for_demo").digest()[:32]
    cipher = GOST34122015(key)
    iv = secrets.token_bytes(16)
    enc = ctr(cipher.encrypt, data, iv)
    return iv + enc


def gost_decrypt(data: bytes) -> bytes:
    if not HAS_PYGOST:
        # AES fallback
        key = None
        if GOV_AES_KEY_ENV:
            try:
                import base64

                key = base64.b64decode(GOV_AES_KEY_ENV)
            except Exception:
                key = None
        if not key or len(key) != 32:
            key = hashlib.sha256(b"gov_fallback_demo_key").digest()[:32]
        iv = data[:16]
        ct = data[16:]
        cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
        dec = cipher.decryptor()
        return dec.update(ct) + dec.finalize()
    # GOST path
    key = hashlib.sha256(b"gov_default_key_for_demo").digest()[:32]
    cipher = GOST34122015(key)
    iv = data[:16]
    ct = data[16:]
    return ctr(cipher.encrypt, ct, iv)


def encrypt_data(data: bytes) -> bytes:
    if not ENABLE_ENCRYPTION:
        return data
    return gost_encrypt(data)


def decrypt_data(data: bytes) -> bytes:
    if not ENABLE_ENCRYPTION:
        return data
    return gost_decrypt(data)


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
            raw = decrypt_data(content)
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

    data = encrypt_data(raw)
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

app = FastAPI(title="Gov HybridCache", version="2.3-gov")


def validate_filename(name: str) -> bool:
    # allow letters, digits, dots, dashes, underscores
    import re

    return re.fullmatch(r"[A-Za-z0-9._-]+", name) is not None


@app.get("/api/cache/{filename}")
def api_get_file(filename: str):
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    try:
        path = get_from_cache(filename)
        # serve decrypted content via temp file
        tmp = Path(cache_path(f"tmp_{hashlib.sha256(filename.encode()).hexdigest()}"))
        with open(path, "rb") as f:
            data = f.read()
        raw = decrypt_data(data)
        with open(tmp, "wb") as f:
            f.write(raw)
        resp = FileResponse(str(tmp), media_type="application/octet-stream", filename=filename)
        # best-effort cleanup
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
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    ensure_dirs()
    load_access_counts()
    uvicorn.run("gov_service:app", host=args.host, port=args.port, reload=False)


