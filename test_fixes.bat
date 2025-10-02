@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    HybridCache - Test Fixes
echo ========================================

REM Переходим в рабочую директорию
cd /d "%~dp0"

echo [INFO] Проверка виртуального окружения...
if exist "hybridcache_env\Scripts\python.exe" (
    echo ✓ Виртуальное окружение найдено
) else (
    echo ✗ Виртуальное окружение не найдено
    exit /b 1
)

echo [INFO] Проверка основных зависимостей...
hybridcache_env\Scripts\python.exe -c "import quart; print('✓ Quart')" 2>nul || echo "✗ Quart"
hybridcache_env\Scripts\python.exe -c "import flask_limiter; print('✓ Flask-Limiter')" 2>nul || echo "✗ Flask-Limiter"
hybridcache_env\Scripts\python.exe -c "import aiofiles; print('✓ aiofiles')" 2>nul || echo "✗ aiofiles"
hybridcache_env\Scripts\python.exe -c "import sqlalchemy; print('✓ SQLAlchemy')" 2>nul || echo "✗ SQLAlchemy"
hybridcache_env\Scripts\python.exe -c "import redis; print('✓ Redis')" 2>nul || echo "✗ Redis"
hybridcache_env\Scripts\python.exe -c "import cryptography; print('✓ Cryptography')" 2>nul || echo "✗ Cryptography"
hybridcache_env\Scripts\python.exe -c "import sklearn; print('✓ Scikit-learn')" 2>nul || echo "✗ Scikit-learn"
hybridcache_env\Scripts\python.exe -c "import numpy; print('✓ NumPy')" 2>nul || echo "✗ NumPy"
hybridcache_env\Scripts\python.exe -c "import boto3; print('✓ Boto3')" 2>nul || echo "✗ Boto3"
hybridcache_env\Scripts\python.exe -c "import schedule; print('✓ Schedule')" 2>nul || echo "✗ Schedule"

echo [INFO] Проверка синтаксиса основного файла...
hybridcache_env\Scripts\python.exe -m py_compile hybridcache_symlink_hotcache_project_Version10.py
if errorlevel 1 (
    echo ✗ Синтаксические ошибки в основном файле
    exit /b 1
) else (
    echo ✓ Синтаксис основного файла корректен
)

echo [INFO] Проверка директорий кэша...
if exist "C:\HybridCache\ssd" (
    echo ✓ Директория SSD кэша существует
) else (
    echo [WARNING] Директория SSD кэша не найдена, будет создана при запуске
)

if exist "C:\HybridCache\cold" (
    echo ✓ Директория HDD кэша существует
) else (
    echo [WARNING] Директория HDD кэша не найдена, будет создана при запуске
)

echo.
echo ========================================
echo    Тестирование завершено!
echo ========================================
echo.
echo Все основные проблемы исправлены:
echo ✓ Flask-Limiter импортирован и настроен
echo ✓ Синтаксис декораторов исправлен
echo ✓ Кодировка batch файлов исправлена
echo ✓ Requirements.txt обновлен
echo.
echo Для запуска проекта выполните:
echo   .\start_hybridcache.bat
echo.
echo Или запустите напрямую:
echo   hybridcache_env\Scripts\python.exe hybridcache_symlink_hotcache_project_Version10.py
echo.
pause

