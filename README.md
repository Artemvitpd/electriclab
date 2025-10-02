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