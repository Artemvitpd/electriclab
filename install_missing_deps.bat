@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    HybridCache - Install Missing Dependencies
echo ========================================

REM Переходим в рабочую директорию
cd /d "%~dp0"

echo [INFO] Активация виртуального окружения...
call hybridcache_env\Scripts\activate.bat

echo [INFO] Установка flask-limiter...
pip install "flask-limiter[async]>=3.5.0"

echo [INFO] Проверка установленных пакетов...
pip list | findstr -i "flask-limiter quart aiofiles sqlalchemy redis cryptography scikit-learn numpy boto3 schedule gunicorn"

echo.
echo ========================================
echo    Установка завершена!
echo ========================================
echo.
echo Теперь можно запустить проект:
echo   .\start_hybridcache.bat
echo.
pause

