# HybridCache PowerShell Installer
# Создает все необходимые файлы для установки

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   HybridCache PowerShell Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Определяем рабочую директорию
$workDir = "C:\Users\Артем\доп проект"
Write-Host "Рабочая директория: $workDir" -ForegroundColor Yellow

# Переходим в рабочую директорию
Set-Location $workDir

# 1. Создаем requirements.txt
Write-Host "Создаю requirements.txt..." -ForegroundColor Green
$requirements = @"
# Основные веб-фреймворки
quart>=0.18.4
quart-wtf>=0.5.0

# Асинхронная работа с файлами
aiofiles>=23.2.1

# База данных
sqlalchemy>=2.0.23
psycopg2-binary>=2.9.9

# Кэширование и Redis
redis>=5.0.1

# Мониторинг и метрики
prometheus-flask-exporter>=0.23.0

# Шифрование
cryptography>=41.0.7

# Машинное обучение
scikit-learn>=1.3.2
numpy>=1.24.3

# AWS SDK
boto3>=1.34.0

# Планировщик задач
schedule>=1.2.0

# Ограничение запросов
flask-limiter>=3.5.0

# Продакшн сервер
gunicorn>=21.2.0

# Тестирование
pytest>=7.4.3
pytest-asyncio>=0.21.1
"@

$requirements | Out-File -FilePath "requirements.txt" -Encoding UTF8

# 2. Создаем install.bat
Write-Host "Создаю install.bat..." -ForegroundColor Green
$installBat = @"
@echo off
setlocal enabledelayedexpansion

REM HybridCache Windows Installer
echo ========================================
echo    HybridCache Windows Installer
echo ========================================

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python не установлен. Пожалуйста, установите Python 3.8+ с https://python.org
    pause
    exit /b 1
)

REM Проверка pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip не найден. Пожалуйста, переустановите Python
    pause
    exit /b 1
)

echo [INFO] Создание виртуального окружения...
python -m venv hybridcache_env
if errorlevel 1 (
    echo [ERROR] Не удалось создать виртуальное окружение
    pause
    exit /b 1
)

echo [INFO] Активация виртуального окружения...
call hybridcache_env\Scripts\activate.bat

echo [INFO] Обновление pip...
python -m pip install --upgrade pip setuptools wheel

echo [INFO] Установка зависимостей...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo [ERROR] Файл requirements.txt не найден
    pause
    exit /b 1
)

echo [INFO] Создание директорий...
if not exist "C:\HybridCache" mkdir "C:\HybridCache"
if not exist "C:\HybridCache\ssd" mkdir "C:\HybridCache\ssd"
if not exist "C:\HybridCache\cold" mkdir "C:\HybridCache\cold"
if not exist "C:\HybridCache\logs" mkdir "C:\HybridCache\logs"

echo [INFO] Создание batch файла для запуска...
(
echo @echo off
echo cd /d "%~dp0"
echo call hybridcache_env\Scripts\activate.bat
echo python hybridcache_symlink_hotcache_project_Version10.py
echo pause
) > start_hybridcache.bat

echo.
echo ========================================
echo    Установка завершена!
echo ========================================
echo.
echo [SUCCESS] HybridCache установлен успешно!
echo.
echo Для запуска используйте:
echo   - start_hybridcache.bat (ручной запуск)
echo.
echo Сервис будет доступен по адресу:
echo   http://localhost:8080
echo.
pause
"@

$installBat | Out-File -FilePath "install.bat" -Encoding ASCII

# 3. Создаем README.md
Write-Host "Создаю README.md..." -ForegroundColor Green
$readme = @"
# HybridCache

Гибридная система кэширования с поддержкой RAM, SSD и HDD с использованием машинного обучения для оптимизации производительности.

## Возможности

- **Трехуровневое кэширование**: RAM (Redis) → SSD → HDD
- **Шифрование**: AES-256 с AWS KMS
- **ML-оптимизация**: Предиктивное перемещение файлов
- **Веб-интерфейс**: Удобное управление через браузер
- **Мониторинг**: Prometheus метрики
- **Масштабируемость**: Поддержка кластеров

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

## Лицензия

MIT
"@

$readme | Out-File -FilePath "README.md" -Encoding UTF8
