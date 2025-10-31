#!/usr/bin/env python3
"""
Создание исполняемых файлов HybridCache для всех ОС
"""

import os
import sys
import platform
import subprocess
import tempfile
import shutil
import zipfile
from pathlib import Path


def create_windows_exe():
    """Создание Windows .exe файла"""
    print("🪟 Creating Windows executable...")
    
    # Основной код установщика
    installer_code = '''#!/usr/bin/env python3
"""
HybridCache Windows Installer
"""

import os
import sys
import platform
import subprocess
import tempfile
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
    uvicorn.run(app, host="127.0.0.1", port=8081)
'''
    
    # Записываем сервисы
    with open(os.path.join(install_dir, "services", "fast_service.py"), "w") as f:
        f.write(fast_service)
    
    with open(os.path.join(install_dir, "services", "secure_service.py"), "w") as f:
        f.write(secure_service)
    
    # Создаем batch файлы
    start_fast = f'''@echo off
echo Starting HybridCache Fast Service...
set HYBRIDCACHE_DIR=%~dp0data\\cache
set HYBRIDCACHE_SOURCE=%~dp0data\\source
"{python_exe}" "%~dp0services\\fast_service.py"
pause
'''
    
    start_secure = f'''@echo off
echo Starting HybridCache Secure Service...
set HYBRIDCACHE_DIR=%~dp0data\\cache
set HYBRIDCACHE_SOURCE=%~dp0data\\source
"{python_exe}" "%~dp0services\\secure_service.py"
pause
'''
    
    with open(os.path.join(install_dir, "start_fast.bat"), "w") as f:
        f.write(start_fast)
    
    with open(os.path.join(install_dir, "start_secure.bat"), "w") as f:
        f.write(start_secure)
    
    # Создаем README
    readme = '''# HybridCache v3.0

## Описание
HybridCache - высокопроизводительная система кэширования файлов.

## Запуск
- start_fast.bat - Быстрый сервис (порт 8080)
- start_secure.bat - Безопасный сервис (порт 8081)

## API
- GET /api/cache/{filename} - Получить файл
- GET /health - Проверка здоровья

## Установка завершена!
'''
    
    with open(os.path.join(install_dir, "README.md"), "w") as f:
        f.write(readme)
    
    print("Installation completed successfully!")
    print(f"Installed to: {install_dir}")
    print("Run start_fast.bat or start_secure.bat to start services")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
'''
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(installer_code)
        temp_file = f.name
    
    try:
        # Создаем exe с PyInstaller
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pyinstaller"
        ], check=True)
        
        subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "--onefile", 
            "--name=HybridCache_Installer_Windows", 
            "--add-data=README.md;.",
            temp_file
        ], check=True)
        
        # Перемещаем exe в текущую директорию
        exe_path = "dist/HybridCache_Installer_Windows.exe"
        if os.path.exists(exe_path):
            shutil.move(exe_path, "HybridCache_Windows.exe")
            print("✅ Created: HybridCache_Windows.exe")
        
    finally:
        os.unlink(temp_file)
        # Очищаем временные файлы PyInstaller
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        if os.path.exists("HybridCache_Installer_Windows.spec"):
            os.unlink("HybridCache_Installer_Windows.spec")


def create_linux_executable():
    """Создание Linux исполняемого файла"""
    print("🐧 Creating Linux executable...")
    
    # Основной код установщика для Linux
    installer_code = '''#!/usr/bin/env python3
"""
HybridCache Linux Installer
"""

import os
import sys
import platform
import subprocess
import tempfile
import shutil
import time
from pathlib import Path


def main():
    print("HybridCache Linux Installer v3.0")
    print("=" * 50)
    
    # Проверка Python
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ required")
        return
    
    install_dir = os.path.expanduser("~/HybridCache")
    
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
    pip_exe = os.path.join(install_dir, "bin", "pip")
    python_exe = os.path.join(install_dir, "bin", "python")
    
    dependencies = [
        "fastapi>=0.68.0",
        "uvicorn[standard]>=0.15.0", 
        "cryptography>=3.4.8",
        "requests>=2.25.1",
        "psutil>=5.8.0",
        "pygost>=5.4,<6"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        subprocess.run([pip_exe, "install", dep], check=True)
    
    # Создаем быстрый сервис (тот же код что и для Windows)
    fast_service = '''import os
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
    uvicorn.run(app, host="127.0.0.1", port=8080)
'''
    
    # Создаем безопасный сервис (тот же код что и для Windows)
    secure_service = '''import os
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
    uvicorn.run(app, host="127.0.0.1", port=8081)
'''
    
    # Записываем сервисы
    with open(os.path.join(install_dir, "services", "fast_service.py"), "w") as f:
        f.write(fast_service)
    
    with open(os.path.join(install_dir, "services", "secure_service.py"), "w") as f:
        f.write(secure_service)
    
    # Создаем shell скрипты
    start_fast = f'''#!/bin/bash
echo "Starting HybridCache Fast Service..."
export HYBRIDCACHE_DIR="$(dirname "$0")/data/cache"
export HYBRIDCACHE_SOURCE="$(dirname "$0")/data/source"
"{python_exe}" "$(dirname "$0")/services/fast_service.py"
'''
    
    start_secure = f'''#!/bin/bash
echo "Starting HybridCache Secure Service..."
export HYBRIDCACHE_DIR="$(dirname "$0")/data/cache"
export HYBRIDCACHE_SOURCE="$(dirname "$0")/data/source"
"{python_exe}" "$(dirname "$0")/services/secure_service.py"
'''
    
    with open(os.path.join(install_dir, "start_fast.sh"), "w") as f:
        f.write(start_fast)
    
    with open(os.path.join(install_dir, "start_secure.sh"), "w") as f:
        f.write(start_secure)
    
    # Делаем скрипты исполняемыми
    os.chmod(os.path.join(install_dir, "start_fast.sh"), 0o755)
    os.chmod(os.path.join(install_dir, "start_secure.sh"), 0o755)
    
    # Создаем README
    readme = '''# HybridCache v3.0

## Описание
HybridCache - высокопроизводительная система кэширования файлов.

## Запуск
- ./start_fast.sh - Быстрый сервис (порт 8080)
- ./start_secure.sh - Безопасный сервис (порт 8081)

## API
- GET /api/cache/{filename} - Получить файл
- GET /health - Проверка здоровья

## Установка завершена!
'''
    
    with open(os.path.join(install_dir, "README.md"), "w") as f:
        f.write(readme)
    
    print("Installation completed successfully!")
    print(f"Installed to: {install_dir}")
    print("Run ./start_fast.sh or ./start_secure.sh to start services")


if __name__ == "__main__":
    main()
'''
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(installer_code)
        temp_file = f.name
    
    try:
        # Создаем исполняемый файл с PyInstaller
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pyinstaller"
        ], check=True)
        
        subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "--onefile", 
            "--name=HybridCache_Installer_Linux", 
            temp_file
        ], check=True)
        
        # Перемещаем исполняемый файл
        bin_path = "dist/HybridCache_Installer_Linux"
        if os.path.exists(bin_path):
            shutil.move(bin_path, "HybridCache_Linux.bin")
            os.chmod("HybridCache_Linux.bin", 0o755)
            print("✅ Created: HybridCache_Linux.bin")
        
    finally:
        os.unlink(temp_file)
        # Очищаем временные файлы PyInstaller
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        if os.path.exists("HybridCache_Installer_Linux.spec"):
            os.unlink("HybridCache_Installer_Linux.spec")


def create_macos_executable():
    """Создание macOS исполняемого файла"""
    print("🍎 Creating macOS executable...")
    
    # Код установщика для macOS (аналогичен Linux)
    installer_code = '''#!/usr/bin/env python3
"""
HybridCache macOS Installer
"""

import os
import sys
import platform
import subprocess
import tempfile
import shutil
import time
from pathlib import Path


def main():
    print("HybridCache macOS Installer v3.0")
    print("=" * 50)
    
    # Проверка Python
    if sys.version_info < (3, 8):
        print("Error: Python 3.8+ required")
        return
    
    install_dir = os.path.expanduser("~/HybridCache")
    
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
    pip_exe = os.path.join(install_dir, "bin", "pip")
    python_exe = os.path.join(install_dir, "bin", "python")
    
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
    
    # Создаем сервисы (тот же код что и для Linux)
    fast_service = '''import os
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
    uvicorn.run(app, host="127.0.0.1", port=8080)
'''
    
    secure_service = '''import os
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
    uvicorn.run(app, host="127.0.0.1", port=8081)
'''
    
    # Записываем сервисы
    with open(os.path.join(install_dir, "services", "fast_service.py"), "w") as f:
        f.write(fast_service)
    
    with open(os.path.join(install_dir, "services", "secure_service.py"), "w") as f:
        f.write(secure_service)
    
    # Создаем shell скрипты
    start_fast = f'''#!/bin/bash
echo "Starting HybridCache Fast Service..."
export HYBRIDCACHE_DIR="$(dirname "$0")/data/cache"
export HYBRIDCACHE_SOURCE="$(dirname "$0")/data/source"
"{python_exe}" "$(dirname "$0")/services/fast_service.py"
'''
    
    start_secure = f'''#!/bin/bash
echo "Starting HybridCache Secure Service..."
export HYBRIDCACHE_DIR="$(dirname "$0")/data/cache"
export HYBRIDCACHE_SOURCE="$(dirname "$0")/data/source"
"{python_exe}" "$(dirname "$0")/services/secure_service.py"
'''
    
    with open(os.path.join(install_dir, "start_fast.sh"), "w") as f:
        f.write(start_fast)
    
    with open(os.path.join(install_dir, "start_secure.sh"), "w") as f:
        f.write(start_secure)
    
    # Делаем скрипты исполняемыми
    os.chmod(os.path.join(install_dir, "start_fast.sh"), 0o755)
    os.chmod(os.path.join(install_dir, "start_secure.sh"), 0o755)
    
    # Создаем README
    readme = '''# HybridCache v3.0

## Описание
HybridCache - высокопроизводительная система кэширования файлов.

## Запуск
- ./start_fast.sh - Быстрый сервис (порт 8080)
- ./start_secure.sh - Безопасный сервис (порт 8081)

## API
- GET /api/cache/{filename} - Получить файл
- GET /health - Проверка здоровья

## Установка завершена!
'''
    
    with open(os.path.join(install_dir, "README.md"), "w") as f:
        f.write(readme)
    
    print("Installation completed successfully!")
    print(f"Installed to: {install_dir}")
    print("Run ./start_fast.sh or ./start_secure.sh to start services")


if __name__ == "__main__":
    main()
'''
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(installer_code)
        temp_file = f.name
    
    try:
        # Создаем исполняемый файл с PyInstaller
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pyinstaller"
        ], check=True)
        
        subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "--onefile", 
            "--name=HybridCache_Installer_macOS", 
            temp_file
        ], check=True)
        
        # Перемещаем исполняемый файл
        bin_path = "dist/HybridCache_Installer_macOS"
        if os.path.exists(bin_path):
            shutil.move(bin_path, "HybridCache_macOS.bin")
            os.chmod("HybridCache_macOS.bin", 0o755)
            print("✅ Created: HybridCache_macOS.bin")
        
    finally:
        os.unlink(temp_file)
        # Очищаем временные файлы PyInstaller
        if os.path.exists("build"):
            shutil.rmtree("build")
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        if os.path.exists("HybridCache_Installer_macOS.spec"):
            os.unlink("HybridCache_Installer_macOS.spec")


def main():
    """Создание исполняемых файлов для всех ОС"""
    print("🚀 Creating HybridCache Executables for All Platforms")
    print("=" * 60)
    
    current_os = platform.system().lower()
    
    try:
        if current_os == "windows":
            create_windows_exe()
        elif current_os == "linux":
            create_linux_executable()
        elif current_os == "darwin":  # macOS
            create_macos_executable()
        else:
            print(f"❌ Unsupported OS: {current_os}")
            return
        
        print("\n🎉 Executable creation completed!")
        print("=" * 60)
        
        if current_os == "windows":
            print("✅ Created: HybridCache_Windows.exe")
            print("💡 Run HybridCache_Windows.exe to install and start HybridCache")
        elif current_os == "linux":
            print("✅ Created: HybridCache_Linux.bin")
            print("💡 Run ./HybridCache_Linux.bin to install and start HybridCache")
        elif current_os == "darwin":
            print("✅ Created: HybridCache_macOS.bin")
            print("💡 Run ./HybridCache_macOS.bin to install and start HybridCache")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error creating executables: {e}")


if __name__ == "__main__":
    main()
