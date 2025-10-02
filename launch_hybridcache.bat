@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    🚀 HybridCache Launcher
echo ========================================

REM Переходим в директорию скрипта
cd /d "%~dp0"

echo [INFO] Проверка виртуального окружения...
if not exist "hybridcache_env\Scripts\python.exe" (
    echo [ERROR] Виртуальное окружение не найдено
    echo Запустите сначала install.bat
    pause
    exit /b 1
)

echo [INFO] Запуск HybridCache...
echo.
echo 🌐 Сервер будет доступен по адресу: http://localhost:8080
echo 📱 Веб-интерфейс: http://localhost:8080
echo 🔧 API: http://localhost:8080/api/test
echo 📊 Статистика: http://localhost:8080/api/stats
echo.
echo 🛑 Для остановки нажмите Ctrl+C
echo.

REM Запуск тестового сервера (рабочая версия)
hybridcache_env\Scripts\python.exe simple_test.py

echo.
echo HybridCache остановлен
pause
