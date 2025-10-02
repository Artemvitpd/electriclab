# HybridCache Auto-Fix Script
# Автоматически исправляет все проблемы с зависимостями и кодом

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   HybridCache Auto-Fix Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Определяем рабочую директорию
$workDir = "C:\Users\Артем\доп проект"
Write-Host "Рабочая директория: $workDir" -ForegroundColor Yellow

# Переходим в рабочую директорию
Set-Location $workDir

# 1. Исправляем requirements.txt
Write-Host "Исправляю requirements.txt..." -ForegroundColor Green
$requirements = @"
# Основные веб-фреймворки
quart==0.18.4
quart-wtf==0.5.0
werkzeug==2.3.7

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
flask-limiter[async]>=3.5.0

# Продакшн сервер
gunicorn>=21.2.0

# Тестирование
pytest>=7.4.3
pytest-asyncio>=0.21.1
"@

$requirements | Out-File -FilePath "requirements.txt" -Encoding UTF8

# 2. Исправляем start_hybridcache.bat
Write-Host "Исправляю start_hybridcache.bat..." -ForegroundColor Green
$startBat = @"
@echo off
cd /d "%~dp0"
call hybridcache_env\Scripts\activate.bat
python hybridcache_symlink_hotcache_project_Version10.py
pause
"@

$startBat | Out-File -FilePath "start_hybridcache.bat" -Encoding ASCII

# 3. Исправляем основной Python файл
Write-Host "Исправляю основной Python файл..." -ForegroundColor Green

# Читаем существующий файл
$pythonFile = Get-Content "hybridcache_symlink_hotcache_project_Version10.py" -Raw

# Добавляем недостающий импорт Limiter после строки с quart_wtf
$pythonFile = $pythonFile -replace "from quart_wtf import QuartForm, CSRFProtect", "from quart_wtf import QuartForm, CSRFProtect`nfrom flask_limiter import Limiter`nfrom flask_limiter.util import get_remote_address"

# Сохраняем исправленный файл
$pythonFile | Out-File -FilePath "hybridcache_symlink_hotcache_project_Version10.py" -Encoding UTF8

## Выполните эти команды по порядку:

### 1. Пересоздайте виртуальное окружение:
```powershell
Remove-Item -Recurse -Force hybridcache_env
python -m venv hybridcache_env
```

### 2. Активируйте виртуальное окружение:
```powershell
.\hybridcache_env\Scripts\Activate.ps1
```

### 3. Установите зависимости по порядку:
```powershell
pip install werkzeug==2.3.7
pip install quart==0.18.4
pip install quart-wtf==0.5.0
pip install flask-limiter[async]
pip install aiofiles
pip install sqlalchemy
pip install redis
pip install cryptography
pip install scikit-learn
pip install numpy
pip install boto3
pip install schedule
pip install prometheus-flask-exporter
pip install gunicorn
```

### 4. Создайте директории кэша:
```powershell
New-Item -ItemType Directory -Path "C:\HybridCache" -Force
New-Item -ItemType Directory -Path "C:\HybridCache\ssd" -Force
New-Item -ItemType Directory -Path "C:\HybridCache\cold" -Force
New-Item -ItemType Directory -Path "C:\HybridCache\logs" -Force
```

### 5. Запустите систему:
```powershell
python hybridcache_symlink_hotcache_project_Version10.py
```

**Выполняйте команды по одной, чтобы избежать проблем с кодировкой!** 🚀
