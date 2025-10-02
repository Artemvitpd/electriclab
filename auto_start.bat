@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    HybridCache Auto Start
echo ========================================

REM Переходим в директорию скрипта
cd /d "%~dp0"

REM Проверяем существование виртуального окружения
if not exist "hybridcache_env\Scripts\python.exe" (
    echo [ERROR] Виртуальное окружение не найдено
    echo Запустите сначала install.bat
    pause
    exit /b 1
)

REM Проверяем существование основного файла
if not exist "hybridcache_symlink_hotcache_project_Version10.py" (
    echo [ERROR] Основной файл не найден
    pause
    exit /b 1
)

echo [INFO] Запуск HybridCache с автоматическими параметрами...
echo.

REM Создаем временный файл с вводом
echo 1> temp_input.txt

REM Запускаем проект с автоматическим вводом
echo [INFO] Выбираем профиль: Корпоративный (1)
hybridcache_env\Scripts\python.exe hybridcache_symlink_hotcache_project_Version10.py < temp_input.txt

REM Удаляем временный файл
del temp_input.txt

echo.
echo HybridCache остановлен
pause
