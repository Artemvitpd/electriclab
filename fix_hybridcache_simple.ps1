# HybridCache Auto-Fix Script
# Automatically fixes all dependency and code issues

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   HybridCache Auto-Fix Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Set working directory
$workDir = "C:\Users\Артем\доп проект"
Write-Host "Working directory: $workDir" -ForegroundColor Yellow

# Change to working directory
Set-Location $workDir

# 1. Fix requirements.txt
Write-Host "Fixing requirements.txt..." -ForegroundColor Green
$requirements = @"
# Web frameworks
quart==0.18.4
quart-wtf==0.5.0
werkzeug==2.3.7

# Async file operations
aiofiles>=23.2.1

# Database
sqlalchemy>=2.0.23
psycopg2-binary>=2.9.9

# Caching and Redis
redis>=5.0.1

# Monitoring and metrics
prometheus-flask-exporter>=0.23.0

# Encryption
cryptography>=41.0.7

# Machine learning
scikit-learn>=1.3.2
numpy>=1.24.3

# AWS SDK
boto3>=1.34.0

# Task scheduler
schedule>=1.2.0

# Request limiting
flask-limiter[async]>=3.5.0

# Production server
gunicorn>=21.2.0

# Testing
pytest>=7.4.3
pytest-asyncio>=0.21.1
"@

$requirements | Out-File -FilePath "requirements.txt" -Encoding UTF8

# 2. Fix start_hybridcache.bat
Write-Host "Fixing start_hybridcache.bat..." -ForegroundColor Green
$startBat = @"
@echo off
cd /d "%~dp0"
call hybridcache_env\Scripts\activate.bat
python hybridcache_symlink_hotcache_project_Version10.py
pause
"@

$startBat | Out-File -FilePath "start_hybridcache.bat" -Encoding ASCII

# 3. Fix main Python file
Write-Host "Fixing main Python file..." -ForegroundColor Green

# Read existing file
$pythonFile = Get-Content "hybridcache_symlink_hotcache_project_Version10.py" -Raw

# Add missing Limiter import after quart_wtf line
$pythonFile = $pythonFile -replace "from quart_wtf import QuartForm, CSRFProtect", "from quart_wtf import QuartForm, CSRFProtect`nfrom flask_limiter import Limiter`nfrom flask_limiter.util import get_remote_address"

# Save fixed file
$pythonFile | Out-File -FilePath "hybridcache_symlink_hotcache_project_Version10.py" -Encoding UTF8

# 4. Recreate virtual environment
Write-Host "Recreating virtual environment..." -ForegroundColor Green
if (Test-Path "hybridcache_env") {
    Remove-Item -Recurse -Force "hybridcache_env"
}

# Create new virtual environment
python -m venv hybridcache_env

# 5. Activate virtual environment and install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Green
& "hybridcache_env\Scripts\activate.bat"
& "hybridcache_env\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

# Install dependencies in order
$packages = @(
    "werkzeug==2.3.7",
    "quart==0.18.4", 
    "quart-wtf==0.5.0",
    "flask-limiter[async]>=3.5.0",
    "aiofiles>=23.2.1",
    "sqlalchemy>=2.0.23",
    "psycopg2-binary>=2.9.9",
    "redis>=5.0.1",
    "prometheus-flask-exporter>=0.23.0",
    "cryptography>=41.0.7",
    "scikit-learn>=1.3.2",
    "numpy>=1.24.3",
    "boto3>=1.34.0",
    "schedule>=1.2.0",
    "gunicorn>=21.2.0",
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Yellow
    & "hybridcache_env\Scripts\python.exe" -m pip install $package
}

# 6. Create cache directories
Write-Host "Creating cache directories..." -ForegroundColor Green
if (!(Test-Path "C:\HybridCache")) { New-Item -ItemType Directory -Path "C:\HybridCache" -Force }
if (!(Test-Path "C:\HybridCache\ssd")) { New-Item -ItemType Directory -Path "C:\HybridCache\ssd" -Force }
if (!(Test-Path "C:\HybridCache\cold")) { New-Item -ItemType Directory -Path "C:\HybridCache\cold" -Force }
if (!(Test-Path "C:\HybridCache\logs")) { New-Item -ItemType Directory -Path "C:\HybridCache\logs" -Force }

# 7. Check installed packages
Write-Host "`nChecking installed packages..." -ForegroundColor Yellow
& "hybridcache_env\Scripts\python.exe" -m pip list

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   Fixes completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nFixed files:" -ForegroundColor Yellow
Write-Host "  • requirements.txt - updated with compatible versions" -ForegroundColor White
Write-Host "  • start_hybridcache.bat - fixed encoding" -ForegroundColor White
Write-Host "  • hybridcache_symlink_hotcache_project_Version10.py - added Limiter import" -ForegroundColor White
Write-Host "  • hybridcache_env/ - recreated virtual environment" -ForegroundColor White

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Run: .\start_hybridcache.bat" -ForegroundColor White
Write-Host "  2. Open: http://localhost:8080" -ForegroundColor White

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
Read-Host

