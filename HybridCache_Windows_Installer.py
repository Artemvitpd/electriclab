#!/usr/bin/env python3
"""
HybridCache Windows Installer
Автоматическая установка для Windows
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path


def main():
    print("HybridCache Windows Installer v3.0")
    print("=" * 50)
    
    # Проверка Python
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ required")
        input("Press Enter to exit...")
        return
    
    install_dir = os.path.join(os.environ.get('APPDATA', ''), 'HybridCache')
    
    print(f"Installing to: {install_dir}")
    
    # Удаляем старую установку
    if os.path.exists(install_dir):
        print("Removing old installation...")
        shutil.rmtree(install_dir)
    
    # Создаем директории
    os.makedirs(install_dir, exist_ok=True)
    os.makedirs(os.path.join(install_dir, "services"), exist_ok=True)
    os.makedirs(os.path.join(install_dir, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(install_dir, "data", "cache"), exist_ok=True)
    os.makedirs(os.path.join(install_dir, "data", "source"), exist_ok=True)
    
    # Создаем виртуальное окружение
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", install_dir], check=True)
    
    # Устанавливаем зависимости
    pip_exe = os.path.join(install_dir, "Scripts", "pip.exe")
    python_exe = os.path.join(install_dir, "Scripts", "python.exe")
    
    dependencies = [
        "fastapi>=0.68.0",
        "uvicorn[standard]>=0.15.0", 
        "cryptography>=3.4.8",
        "requests>=2.25.1",
        "psutil>=5.8.0"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        subprocess.run([pip_exe, "install", dep], check=True)
    
    # Создаем быстрый сервис
    fast_service = """import os
import time
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

CACHE_DIR = os.getenv("HYBRIDCACHE_DIR", "/cache")
SOURCE_DIR = os.getenv("HYBRIDCACHE_SOURCE", "/source")

def ensure_dirs():
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)

def cache_path(filename: str) -> str:
    safe = filename.replace("/", "_").replace("\\\\", "_").replace("..", "")
    return str(Path(CACHE_DIR) / safe)

def get_from_cache(filename: str, src_dir: Optional[str] = None) -> str:
    ensure_dirs()
    cpath = cache_path(filename)
    spath = str(Path(src_dir or SOURCE_DIR) / filename)
    
    if os.path.exists(cpath):
        return cpath
    
    if not os.path.exists(spath):
        raise FileNotFoundError(f"Source not found: {spath}")
    
    with open(spath, "rb") as f:
        data = f.read()
    
    with open(cpath, "wb") as f:
        f.write(data)
    
    return cpath

app = FastAPI(title="HybridCache Fast Service", version="2.0")

@app.get("/api/cache/{filename}")
def api_get_file(filename: str):
    try:
        path = get_from_cache(filename)
        return FileResponse(path, media_type="application/octet-stream", filename=filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "HybridCache Fast"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)"""
    
    # Создаем безопасный сервис
    secure_service = """import os
import time
import re
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

CACHE_DIR = os.getenv("HYBRIDCACHE_DIR", "/cache")
SOURCE_DIR = os.getenv("HYBRIDCACHE_SOURCE", "/source")

def validate_filename(name: str) -> bool:
    if not name or len(name) > 255:
        return False
    dangerous_patterns = [r'\\.\\.', r'/', r'\\\\\\\\', r'%2e%2e', r'%2f', r'%5c', r'\\x00', r'[<>:"|?*]']
    for pattern in dangerous_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return False
    return re.fullmatch(r"[A-Za-z0-9._-]+", name) is not None

def ensure_dirs():
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)

def cache_path(filename: str) -> str:
    safe = filename.replace("/", "_").replace("\\\\", "_").replace("..", "")
    return str(Path(CACHE_DIR) / safe)

def get_from_cache(filename: str, src_dir: Optional[str] = None) -> str:
    if not validate_filename(filename):
        raise ValueError(f"Invalid filename: {filename}")
    
    ensure_dirs()
    cpath = cache_path(filename)
    spath = str(Path(src_dir or SOURCE_DIR) / filename)
    
    if os.path.exists(cpath):
        return cpath
    
    if not os.path.exists(spath):
        raise FileNotFoundError(f"Source not found: {spath}")
    
    with open(spath, "rb") as f:
        data = f.read()
    
    with open(cpath, "wb") as f:
        f.write(data)
    
    return cpath

app = FastAPI(title="HybridCache Secure Service", version="2.1")

@app.get("/api/cache/{filename}")
def api_get_file(filename: str, request: Request):
    if not validate_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    try:
        path = get_from_cache(filename)
        return FileResponse(path, media_type="application/octet-stream", filename=filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "HybridCache Secure"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8081)"""
    
    # Записываем сервисы
    with open(os.path.join(install_dir, "services", "fast_service.py"), "w") as f:
        f.write(fast_service)
    
    with open(os.path.join(install_dir, "services", "secure_service.py"), "w") as f:
        f.write(secure_service)
    
    # Создаем batch файлы
    start_fast = f"""@echo off
echo Starting HybridCache Fast Service...
set HYBRIDCACHE_DIR=%~dp0data\\cache
set HYBRIDCACHE_SOURCE=%~dp0data\\source
"{python_exe}" "%~dp0services\\fast_service.py"
pause
"""
    
    start_secure = f"""@echo off
echo Starting HybridCache Secure Service...
set HYBRIDCACHE_DIR=%~dp0data\\cache
set HYBRIDCACHE_SOURCE=%~dp0data\\source
"{python_exe}" "%~dp0services\\secure_service.py"
pause
"""
    
    with open(os.path.join(install_dir, "start_fast.bat"), "w") as f:
        f.write(start_fast)
    
    with open(os.path.join(install_dir, "start_secure.bat"), "w") as f:
        f.write(start_secure)
    
    # Создаем README
    readme = """# HybridCache v3.0

## Описание
HybridCache - высокопроизводительная система кэширования файлов.

## Запуск
- start_fast.bat - Быстрый сервис (порт 8080)
- start_secure.bat - Безопасный сервис (порт 8081)

## API
- GET /api/cache/{filename} - Получить файл
- GET /health - Проверка здоровья

## Установка завершена!
"""
    
    with open(os.path.join(install_dir, "README.md"), "w") as f:
        f.write(readme)
    
    # Создаем пример файла
    with open(os.path.join(install_dir, "data", "source", "sample.txt"), "w") as f:
        f.write("HybridCache Sample File\\nThis is a test file for cache demonstration.\\n")
    
    print("Installation completed successfully!")
    print(f"Installed to: {install_dir}")
    print("Run start_fast.bat or start_secure.bat to start services")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()



