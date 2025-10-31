#!/usr/bin/env python3
"""
Cross-platform installer for HybridCache Services
Supports Windows, Linux, macOS
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import argparse


def get_platform():
    """Detect current platform"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    elif system == "darwin":
        return "macos"
    else:
        return "unknown"


def create_venv(install_dir: Path):
    """Create virtual environment"""
    print("Creating virtual environment...")
    venv_path = install_dir / "venv"
    
    if venv_path.exists():
        shutil.rmtree(venv_path)
    
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    
    # Get pip path
    if platform.system() == "Windows":
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    return venv_path, pip_path, python_path


def install_dependencies(pip_path: Path):
    """Install Python dependencies"""
    print("Installing dependencies...")
    requirements = [
        "fastapi==0.115.0",
        "uvicorn[standard]==0.30.6",
        "cryptography==43.0.1",
        "httpx==0.27.2",
        "psutil>=5.9.0"
    ]
    
    for req in requirements:
        subprocess.run([str(pip_path), "install", req], check=True)


def copy_files(install_dir: Path):
    """Copy all necessary files to installation directory"""
    print("Copying files...")
    
    files_to_copy = [
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
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, install_dir / file)
            print(f"  Copied {file}")


def create_scripts(install_dir: Path, python_path: Path):
    """Create platform-specific scripts"""
    print("Creating scripts...")
    
    # Common script content
    gov_service_script = f"""#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gov_service import main
if __name__ == "__main__":
    main()
"""
    
    commercial_script = f"""#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from commercial_service import main
if __name__ == "__main__":
    main()
"""
    
    fast_script = f"""#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from commercial_service_fast import main
if __name__ == "__main__":
    main()
"""
    
    benchmark_script = f"""#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench_fast import main
if __name__ == "__main__":
    main()
"""
    
    # Write scripts
    scripts = {
        "run_gov_service.py": gov_service_script,
        "run_commercial_service.py": commercial_script,
        "run_fast_service.py": fast_script,
        "run_benchmark.py": benchmark_script
    }
    
    for script_name, content in scripts.items():
        script_path = install_dir / script_name
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Make executable on Unix systems
        if platform.system() != "Windows":
            os.chmod(script_path, 0o755)
        
        print(f"  Created {script_name}")


def create_batch_files(install_dir: Path, python_path: Path):
    """Create Windows batch files"""
    if platform.system() != "Windows":
        return
    
    print("Creating Windows batch files...")
    
    batch_files = {
        "start_gov.bat": f"""@echo off
cd /d "%~dp0"
"{python_path}" run_gov_service.py --host 0.0.0.0 --port 8080
pause
""",
        "start_commercial.bat": f"""@echo off
cd /d "%~dp0"
"{python_path}" run_commercial_service.py --host 0.0.0.0 --port 8081
pause
""",
        "start_fast.bat": f"""@echo off
cd /d "%~dp0"
"{python_path}" run_fast_service.py --host 0.0.0.0 --port 8081
pause
""",
        "run_benchmark.bat": f"""@echo off
cd /d "%~dp0"
set HYBRIDCACHE_ENCRYPTION=0
"{python_path}" run_benchmark.py
pause
""",
        "install_docker.bat": f"""@echo off
echo Installing Docker services...
docker-compose up --build
pause
"""
    }
    
    for batch_name, content in batch_files.items():
        batch_path = install_dir / batch_name
        with open(batch_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Created {batch_name}")


def create_shell_scripts(install_dir: Path, python_path: Path):
    """Create Unix shell scripts"""
    if platform.system() == "Windows":
        return
    
    print("Creating shell scripts...")
    
    shell_files = {
        "start_gov.sh": f"""#!/bin/bash
cd "$(dirname "$0")"
{python_path} run_gov_service.py --host 0.0.0.0 --port 8080
""",
        "start_commercial.sh": f"""#!/bin/bash
cd "$(dirname "$0")"
{python_path} run_commercial_service.py --host 0.0.0.0 --port 8081
""",
        "start_fast.sh": f"""#!/bin/bash
cd "$(dirname "$0")"
{python_path} run_fast_service.py --host 0.0.0.0 --port 8081
""",
        "run_benchmark.sh": f"""#!/bin/bash
cd "$(dirname "$0")"
export HYBRIDCACHE_ENCRYPTION=0
{python_path} run_benchmark.py
""",
        "install_docker.sh": f"""#!/bin/bash
echo "Installing Docker services..."
docker-compose up --build
"""
    }
    
    for shell_name, content in shell_files.items():
        shell_path = install_dir / shell_name
        with open(shell_path, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(shell_path, 0o755)
        print(f"  Created {shell_name}")


def create_config_files(install_dir: Path):
    """Create configuration files"""
    print("Creating configuration files...")
    
    # Environment config
    env_config = """# HybridCache Configuration
HYBRIDCACHE_DIR=/cache
HYBRIDCACHE_SOURCE=/source
HYBRIDCACHE_MAXSIZE=107374182400
HYBRIDCACHE_TTL=604800
HYBRIDCACHE_ENCRYPTION=0
HYBRIDCACHE_AES_KEY=your_base64_32_byte_key_here
"""
    
    with open(install_dir / ".env.example", "w") as f:
        f.write(env_config)
    
    # Docker environment
    docker_env = """HYBRIDCACHE_DIR=/cache
HYBRIDCACHE_SOURCE=/source
HYBRIDCACHE_ENCRYPTION=0
HYBRIDCACHE_AES_KEY=your_base64_32_byte_key_here
"""
    
    with open(install_dir / ".env", "w") as f:
        f.write(docker_env)
    
    print("  Created .env.example and .env")


def create_directories(install_dir: Path):
    """Create necessary directories"""
    print("Creating directories...")
    
    dirs = ["cache", "source", "logs", "data/gov/cache", "data/gov/source", 
            "data/commercial/cache", "data/commercial/source"]
    
    for dir_name in dirs:
        dir_path = install_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created {dir_name}/")


def main():
    parser = argparse.ArgumentParser(description="Install HybridCache Services")
    parser.add_argument("--install-dir", default="./HybridCache-Install", 
                       help="Installation directory")
    parser.add_argument("--skip-deps", action="store_true", 
                       help="Skip dependency installation")
    
    args = parser.parse_args()
    
    install_dir = Path(args.install_dir).resolve()
    
    print(f"Installing HybridCache Services to: {install_dir}")
    print(f"Platform: {get_platform()}")
    
    # Create installation directory
    install_dir.mkdir(parents=True, exist_ok=True)
    
    # Create virtual environment
    venv_path, pip_path, python_path = create_venv(install_dir)
    
    # Install dependencies
    if not args.skip_deps:
        install_dependencies(pip_path)
    
    # Copy files
    copy_files(install_dir)
    
    # Create scripts
    create_scripts(install_dir, python_path)
    create_batch_files(install_dir, python_path)
    create_shell_scripts(install_dir, python_path)
    
    # Create config files
    create_config_files(install_dir)
    
    # Create directories
    create_directories(install_dir)
    
    print("\n" + "="*50)
    print("Installation completed successfully!")
    print(f"Installation directory: {install_dir}")
    print("\nTo start services:")
    if platform.system() == "Windows":
        print("  Windows: Run start_fast.bat or start_gov.bat")
        print("  Benchmark: Run run_benchmark.bat")
    else:
        print("  Unix: ./start_fast.sh or ./start_gov.sh")
        print("  Benchmark: ./run_benchmark.sh")
    print("\nDocker: docker-compose up --build")
    print("="*50)


if __name__ == "__main__":
    main()



