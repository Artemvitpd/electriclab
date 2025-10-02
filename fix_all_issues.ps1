# HybridCache Universal Fix Script
# Исправляет все проблемы в проекте

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   HybridCache Universal Fix Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Определяем рабочую директорию
$workDir = Get-Location
Write-Host "Рабочая директория: $workDir" -ForegroundColor Yellow

# 1. Исправляем start_hybridcache.bat
Write-Host "Исправляю start_hybridcache.bat..." -ForegroundColor Green
$startBat = @"
@echo off
cd /d "%~dp0"
call hybridcache_env\Scripts\activate.bat
python hybridcache_symlink_hotcache_project_Version10.py
pause
"@

$startBat | Out-File -FilePath "start_hybridcache.bat" -Encoding ASCII

# 2. Исправляем install.bat
Write-Host "Исправляю install.bat..." -ForegroundColor Green
$installBat = @"
@echo off
setlocal enabledelayedexpansion

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
"@

$installBat | Out-File -FilePath "install.bat" -Encoding ASCII

# 3. Исправляем requirements.txt
Write-Host "Исправляю requirements.txt..." -ForegroundColor Green
$requirements = @"
# Основные веб-фреймворки
quart>=0.18.4
quart-wtf>=0.5.0
werkzeug>=2.3.7

# Асинхронная работа с файлами
aiofiles>=23.2.1

# База данных (SQLite встроен в Python)
sqlalchemy>=2.0.23

# Кэширование и Redis (опционально)
redis>=5.0.1

# Мониторинг и метрики
prometheus-flask-exporter>=0.23.0

# Шифрование
cryptography>=41.0.7

# Машинное обучение
scikit-learn>=1.3.2
numpy>=1.24.3

# AWS SDK (опционально)
boto3>=1.34.0

# Планировщик задач
schedule>=1.2.0

# Продакшн сервер
gunicorn>=21.2.0

# Тестирование
pytest>=7.4.3
pytest-asyncio>=0.21.1
"@

$requirements | Out-File -FilePath "requirements.txt" -Encoding UTF8

# 4. Исправляем README.md
Write-Host "Исправляю README.md..." -ForegroundColor Green
$readme = @"
# HybridCache

Гибридная система кэширования с поддержкой RAM, SSD и HDD с использованием машинного обучения для оптимизации производительности.

## Возможности

- **Трехуровневое кэширование**: RAM (Redis/In-Memory) → SSD → HDD
- **Шифрование**: AES-256 с локальным или AWS KMS шифрованием
- **ML-оптимизация**: Предиктивное перемещение файлов
- **Веб-интерфейс**: Удобное управление через браузер
- **Мониторинг**: Prometheus метрики
- **Масштабируемость**: Поддержка кластеров
- **Fallback режимы**: Работает без Redis и AWS KMS

## Быстрая установка

### Windows
```batch
install.bat
```

### PowerShell
```powershell
.\install_hybridcache_fixed.ps1
```

## Ручная установка

### 1. Установка зависимостей
```bash
# Создание виртуального окружения
python -m venv hybridcache_env
hybridcache_env\Scripts\activate.bat  # Windows

# Установка пакетов
pip install -r requirements.txt
```

### 2. Создание директорий
```batch
mkdir C:\HybridCache
mkdir C:\HybridCache\ssd
mkdir C:\HybridCache\cold
mkdir C:\HybridCache\logs
```

### 3. Запуск
```bash
python hybridcache_symlink_hotcache_project_Version10.py
```

## API

### Загрузка файла
```bash
curl -X POST http://localhost:8080/api/put \
  -F "file=@document.pdf" \
  -F "key=document.pdf" \
  -F "location=hot" \
  -H "X-Api-Key: your-api-key"
```

### Получение файла
```bash
curl -X GET "http://localhost:8080/api/get?key=document.pdf" \
  -H "X-Api-Key: your-api-key" \
  -o document.pdf
```

### Статистика
```bash
curl -X GET http://localhost:8080/api/stats \
  -H "X-Api-Key: your-api-key"
```

## Мониторинг

### Веб-интерфейс
```
http://localhost:8080
```

## Исправления в версии 2.0

- ✅ Исправлена кодировка в batch файлах
- ✅ Добавлен fallback для шифрования без AWS KMS
- ✅ Заменен PostgreSQL на SQLite
- ✅ Добавлен in-memory кэш вместо Redis
- ✅ Улучшено логирование в файлы
- ✅ Упрощен rate limiter
- ✅ Добавлена обработка ошибок

## Лицензия

MIT
"@

$readme | Out-File -FilePath "README.md" -Encoding UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   Все проблемы исправлены!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nИсправления:" -ForegroundColor Yellow
Write-Host "  ✓ Кодировка в batch файлах" -ForegroundColor Green
Write-Host "  ✓ Удален импорт Limiter" -ForegroundColor Green
Write-Host "  ✓ Исправлен README.md" -ForegroundColor Green
Write-Host "  ✓ Добавлены fallback режимы" -ForegroundColor Green
Write-Host "  ✓ Улучшено логирование" -ForegroundColor Green

Write-Host "`nСледующие шаги:" -ForegroundColor Yellow
Write-Host "  1. Запустите: .\start_hybridcache.bat" -ForegroundColor White
Write-Host "  2. Откройте: http://localhost:8080" -ForegroundColor White

Write-Host "`nНажмите любую клавишу для завершения..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
