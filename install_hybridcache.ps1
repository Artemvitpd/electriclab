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
.\install_hybridcache.ps1
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

## Лицензия

MIT License

## Поддержка

- Issues: https://github.com/hybridcache/hybridcache/issues
- Email: support@hybridcache.com
"@

$readme | Out-File -FilePath "README.md" -Encoding UTF8

# 4. Создаем setup.py
Write-Host "Создаю setup.py..." -ForegroundColor Green
$setupPy = @"
from setuptools import setup, find_packages
import os

def read_readme():
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    return "HybridCache - Гибридная система кэширования RAM-SSD-HDD"

def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="hybridcache",
    version="1.0.0",
    author="HybridCache Team",
    author_email="support@hybridcache.com",
    description="Гибридная система кэширования с поддержкой RAM, SSD и HDD",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/hybridcache/hybridcache",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Filesystems",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "prod": [
            "gunicorn>=21.2.0",
            "uvicorn>=0.24.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "hybridcache=hybridcache.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "hybridcache": ["config/*.yaml", "templates/*.html", "static/*"],
    },
)
"@

$setupPy | Out-File -FilePath "setup.py" -Encoding UTF8

# 5. Создаем Dockerfile
Write-Host "Создаю Dockerfile..." -ForegroundColor Green
$dockerfile = @"
# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN groupadd -r hybridcache && useradd -r -g hybridcache hybridcache

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt pyproject.toml ./

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем необходимые директории
RUN mkdir -p /var/cache/ssd /var/cache/cold /app/logs \
    && chown -R hybridcache:hybridcache /app /var/cache

# Переключаемся на пользователя
USER hybridcache

# Открываем порт
EXPOSE 8080

# Переменные окружения
ENV PYTHONPATH=/app
ENV HYBRIDCACHE_ENV=production

# Команда запуска
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--worker-class", "quart.workers.GunicornWorker", "hybridcache_symlink_hotcache_project_Version10:app"]
"@

$dockerfile | Out-File -FilePath "Dockerfile" -Encoding ASCII

# 6. Создаем docker-compose.yml
Write-Host "Создаю docker-compose.yml..." -ForegroundColor Green
$dockerCompose = @"
version: '3.8'

services:
  hybridcache:
    build: .
    ports:
      - "8080:8080"
    environment:
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=hybridcache
      - POSTGRES_USER=hybridcache
      - POSTGRES_PASSWORD=hybridcache_pass
      - AWS_REGION=us-east-1
      - KMS_KEY_ID=alias/hybridcache-key
    volumes:
      - ssd_cache:/var/cache/ssd
      - cold_storage:/var/cache/cold
      - ./logs:/app/logs
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    networks:
      - hybridcache_network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - hybridcache_network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=hybridcache
      - POSTGRES_USER=hybridcache
      - POSTGRES_PASSWORD=hybridcache_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - hybridcache_network

volumes:
  ssd_cache:
  cold_storage:
  redis_data:
  postgres_data:

networks:
  hybridcache_network:
    driver: bridge
"@

$dockerCompose | Out-File -FilePath "docker-compose.yml" -Encoding UTF8

# 7. Создаем .gitignore
Write-Host "Создаю .gitignore..." -ForegroundColor Green
$gitignore = @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
hybridcache_env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/
hybridcache.log

# Cache directories
/var/cache/ssd/
/var/cache/cold/
C:/HybridCache/

# Database
*.db
*.sqlite3

# SSL certificates
ssl/
*.pem
*.key
*.crt

# Docker
.dockerignore

# Environment variables
.env
.env.local
.env.production

# Temporary files
*.tmp
*.temp
temp/
tmp/
"@

$gitignore | Out-File -FilePath ".gitignore" -Encoding UTF8

# Проверяем созданные файлы
Write-Host "`nПроверяю созданные файлы..." -ForegroundColor Yellow
Get-ChildItem -Path $workDir -Name "*.txt", "*.bat", "*.md", "*.py", "Dockerfile", "docker-compose.yml", ".gitignore" | ForEach-Object {
    Write-Host "✓ $_" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   Установочные файлы созданы!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nСозданные файлы:" -ForegroundColor Yellow
Write-Host "  • requirements.txt - зависимости Python" -ForegroundColor White
Write-Host "  • install.bat - установщик для Windows" -ForegroundColor White
Write-Host "  • README.md - документация" -ForegroundColor White
Write-Host "  • setup.py - установщик Python пакета" -ForegroundColor White
Write-Host "  • Dockerfile - контейнеризация" -ForegroundColor White
Write-Host "  • docker-compose.yml - оркестрация контейнеров" -ForegroundColor White
Write-Host "  • .gitignore - исключения для Git" -ForegroundColor White

Write-Host "`nСледующие шаги:" -ForegroundColor Yellow
Write-Host "  1. Запустите: .\install.bat" -ForegroundColor White
Write-Host "  2. Или используйте Docker: docker-compose up -d" -ForegroundColor White
Write-Host "  3. Откройте: http://localhost:8080" -ForegroundColor White

Write-Host "`nНажмите любую клавишу для завершения..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
```

## Как использовать:

1. **Создайте файл** `install_hybridcache.ps1` в директории `C:\Users\Артем\доп проект\`
2. **Скопируйте содержимое** скрипта выше в этот файл
3. **Запустите PowerShell** от имени администратора
4. **Выполните команду:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\install_hybridcache.ps1
   ```


   Этот скрипт автоматически создаст все необходимые файлы для установки HybridCache в вашей директории!
