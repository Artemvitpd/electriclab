@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

REM HybridCache Windows Installer
echo ========================================
echo    HybridCache Windows Installer
echo ========================================

REM Переходим в рабочую директорию
cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip not found. Please reinstall Python
    pause
    exit /b 1
)

echo [INFO] Creating virtual environment...
python -m venv hybridcache_env
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...
call hybridcache_env\Scripts\activate.bat

echo [INFO] Updating pip...
python -m pip install --upgrade pip setuptools wheel

echo [INFO] Installing dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo [ERROR] requirements.txt file not found
    echo Current directory: %CD%
    dir
    pause
    exit /b 1
)

echo [INFO] Creating directories...
if not exist "C:\HybridCache" mkdir "C:\HybridCache"
if not exist "C:\HybridCache\ssd" mkdir "C:\HybridCache\ssd"
if not exist "C:\HybridCache\cold" mkdir "C:\HybridCache\cold"
if not exist "C:\HybridCache\logs" mkdir "C:\HybridCache\logs"

echo [INFO] Creating batch file for startup...
(
echo @echo off
echo cd /d "%%~dp0"
echo call hybridcache_env\Scripts\activate.bat
echo python hybridcache_symlink_hotcache_project_Version10.py
echo pause
) > start_hybridcache.bat

echo.
echo ========================================
echo    Installation completed!
echo ========================================
echo.
echo [SUCCESS] HybridCache installed successfully!
echo.
echo To start use:
echo   - start_hybridcache.bat (manual start)
echo.
echo Service will be available at:
echo   http://localhost:8080
echo.
pause
