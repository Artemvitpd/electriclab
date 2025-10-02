@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    HybridCache Launcher
echo ========================================

REM Переходим в директорию скрипта
cd /d "%~dp0"

REM Проверяем существование виртуального окружения
if not exist "hybridcache_env\Scripts\python.exe" (
    echo [ERROR] Виртуальное окружение не найдено
    echo Запустите сначала install.bat для создания виртуального окружения
    pause
    exit /b 1
)

REM Проверяем существование основного файла
if not exist "hybridcache_symlink_hotcache_project_Version10.py" (
    echo [ERROR] Основной файл не найден
    pause
    exit /b 1
)

echo [INFO] Активация виртуального окружения...
call hybridcache_env\Scripts\activate.bat

echo [INFO] Запуск HybridCache...
echo.
echo Сервис будет доступен по адресу: http://localhost:8080
echo Для остановки нажмите Ctrl+C
echo.

python hybridcache_symlink_hotcache_project_Version10.py

echo.
echo HybridCache остановлен
pause