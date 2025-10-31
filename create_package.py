#!/usr/bin/env python3
"""
Create distributable package for HybridCache Services
"""

import os
import sys
import shutil
import zipfile
import tarfile
from pathlib import Path
import platform


def create_package():
    """Create distributable package"""
    print("Creating HybridCache package...")
    
    # Package name with version and platform
    version = "2.3"
    platform_name = platform.system().lower()
    package_name = f"HybridCache-v{version}-{platform_name}"
    
    # Create package directory
    package_dir = Path(package_name)
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy all necessary files
    files_to_copy = [
        "install.py",
        "gov_service.py",
        "commercial_service.py", 
        "commercial_service_fast.py",
        "perf_test.py",
        "bench_improved.py",
        "bench_fast.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "README.md"
    ]
    
    print("Copying files to package...")
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, package_dir / file)
            print(f"  Added {file}")
    
    # Create quick start script
    if platform.system() == "Windows":
        quick_start = """@echo off
echo HybridCache Services - Quick Start
echo ================================
echo.
echo Installing HybridCache...
python install.py --install-dir ./HybridCache
echo.
echo Installation complete! 
echo.
echo To start services:
echo   - Fast service: cd HybridCache && start_fast.bat
echo   - Gov service: cd HybridCache && start_gov.bat  
echo   - Benchmark: cd HybridCache && run_benchmark.bat
echo   - Docker: cd HybridCache && install_docker.bat
echo.
pause
"""
        with open(package_dir / "install.bat", "w") as f:
            f.write(quick_start)
    else:
        quick_start = """#!/bin/bash
echo "HybridCache Services - Quick Start"
echo "================================"
echo ""
echo "Installing HybridCache..."
python3 install.py --install-dir ./HybridCache
echo ""
echo "Installation complete!"
echo ""
echo "To start services:"
echo "  - Fast service: cd HybridCache && ./start_fast.sh"
echo "  - Gov service: cd HybridCache && ./start_gov.sh"
echo "  - Benchmark: cd HybridCache && ./run_benchmark.sh"
echo "  - Docker: cd HybridCache && ./install_docker.sh"
echo ""
"""
        with open(package_dir / "install.sh", "w") as f:
            f.write(quick_start)
        os.chmod(package_dir / "install.sh", 0o755)
    
    # Create README for package
    package_readme = f"""# HybridCache Services v{version}

Cross-platform caching services with encryption support.

## Quick Installation

### Windows
```cmd
install.bat
```

### Linux/macOS
```bash
chmod +x install.sh
./install.sh
```

## Manual Installation
```bash
python install.py --install-dir ./HybridCache
```

## Services Included

- **Gov Service**: GOST encryption, integrity checks, FSTEC compliance
- **Commercial Service**: AES-256 encryption, standard compliance  
- **Fast Service**: Optimized for maximum speed (recommended)

## Features

- Cross-platform (Windows, Linux, macOS)
- Multiple encryption modes (AES-256, GOST)
- HTTP API with FastAPI
- Performance benchmarking
- Docker support
- Configurable cache policies

## Usage

After installation, navigate to the HybridCache directory and run:

- `start_fast.bat` / `./start_fast.sh` - Start optimized service
- `start_gov.bat` / `./start_gov.sh` - Start government service
- `run_benchmark.bat` / `./run_benchmark.sh` - Run performance tests
- `install_docker.bat` / `./install_docker.sh` - Start with Docker

## Configuration

Edit `.env` file to configure:
- Cache directory
- Source directory  
- Encryption settings
- Cache size limits

## API Endpoints

- `GET /api/cache/{{filename}}` - Get cached file
- `POST /api/preload` - Preload files to cache

## Performance

Optimized fast service shows 4.3% improvement over direct file access
on local SSD storage.

## Requirements

- Python 3.8+
- 100MB free space
- Optional: Docker for containerized deployment

## Support

See README.md for detailed documentation.
"""
    
    with open(package_dir / "PACKAGE_README.md", "w") as f:
        f.write(package_readme)
    
    # Create archive
    print(f"\nCreating archive: {package_name}.zip")
    with zipfile.ZipFile(f"{package_name}.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(package_dir.parent)
                zipf.write(file_path, arc_path)
    
    # Also create tar.gz for Unix systems
    if platform.system() != "Windows":
        print(f"Creating archive: {package_name}.tar.gz")
        with tarfile.open(f"{package_name}.tar.gz", "w:gz") as tarf:
            tarf.add(package_dir, arcname=package_name)
    
    print(f"\nPackage created successfully!")
    print(f"Package directory: {package_dir}")
    print(f"Archive: {package_name}.zip")
    if platform.system() != "Windows":
        print(f"Archive: {package_name}.tar.gz")
    
    return package_name


if __name__ == "__main__":
    create_package()
