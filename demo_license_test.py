#!/usr/bin/env python3
"""
Демонстрация системы лицензий HybridCache
Показывает работу демо-режима и активацию полной лицензии
"""

import os
import sys
import time
import requests
import json
import tempfile
from pathlib import Path
from demo_license_system import DemoLicenseSystem


def create_test_files(source_dir: str, num_files: int = 5):
    """Создаем тестовые файлы"""
    Path(source_dir).mkdir(parents=True, exist_ok=True)
    
    files = []
    for i in range(num_files):
        filename = f"test_file_{i}.txt"
        filepath = Path(source_dir) / filename
        with open(filepath, 'w') as f:
            f.write(f"Test content for file {i}\n" * 100)  # ~2KB файл
        files.append(filename)
    
    return files


def test_license_system():
    """Тестируем систему лицензий"""
    print("=== Тестирование системы лицензий HybridCache ===\n")
    
    # Создаем систему лицензий
    license_system = DemoLicenseSystem("test.license")
    
    # 1. Проверяем статус демо-лицензии
    print("1. Статус демо-лицензии:")
    is_valid, status_msg = license_system.check_license_status()
    print(f"   Валидна: {is_valid}")
    print(f"   Статус: {status_msg}\n")
    
    # 2. Получаем информацию о лицензии
    print("2. Информация о лицензии:")
    info = license_system.get_license_info()
    print(f"   Тип: {info['license_type']}")
    print(f"   Макс. файлов: {info['max_files']}")
    print(f"   Макс. размер кэша: {info['max_cache_size_mb']} MB")
    print(f"   Макс. запросов/час: {info['max_requests_per_hour']}")
    print(f"   Функции: {info['features']}\n")
    
    # 3. Тестируем ограничения
    print("3. Тестирование ограничений:")
    
    # Тест лимита файлов
    file_ok, file_msg = license_system.check_file_limit(50)
    print(f"   Файлы (50): {file_msg}")
    
    file_ok, file_msg = license_system.check_file_limit(150)  # Превышение лимита
    print(f"   Файлы (150): {file_msg}")
    
    # Тест лимита размера кэша
    cache_ok, cache_msg = license_system.check_cache_size_limit(512 * 1024 * 1024)  # 512MB
    print(f"   Кэш (512MB): {cache_msg}")
    
    cache_ok, cache_msg = license_system.check_cache_size_limit(2048 * 1024 * 1024)  # 2GB - превышение
    print(f"   Кэш (2GB): {cache_msg}")
    
    # Тест лимита запросов
    req_ok, req_msg = license_system.check_request_limit()
    print(f"   Запросы: {req_msg}\n")
    
    # 4. Тестируем доступ к функциям
    print("4. Доступ к функциям:")
    features = ["basic_caching", "aes_encryption", "gost_encryption", "advanced_analytics"]
    for feature in features:
        has_access = license_system.has_feature(feature)
        status = "✓" if has_access else "✗"
        print(f"   {status} {feature}")
    
    print("\n" + "="*50 + "\n")
    
    # 5. Активация полной лицензии
    print("5. Активация полной лицензии:")
    fake_license_key = "ABCD1234EFGH5678IJKL9012MNOP3456"
    
    success, message = license_system.activate_full_license(fake_license_key)
    print(f"   Результат: {message}")
    
    if success:
        # Проверяем новую информацию
        info = license_system.get_license_info()
        print(f"   Новый тип: {info['license_type']}")
        print(f"   Новые функции: {info['features']}")
        
        # Проверяем доступ к расширенным функциям
        print("\n   Доступ к расширенным функциям:")
        for feature in features:
            has_access = license_system.has_feature(feature)
            status = "✓" if has_access else "✗"
            print(f"   {status} {feature}")
    
    print("\n" + "="*50 + "\n")


def test_api_with_license():
    """Тестируем API с системой лицензий"""
    print("=== Тестирование API с системой лицензий ===\n")
    
    base_url = "http://127.0.0.1:8081"
    
    try:
        # 1. Проверяем статус лицензии через API
        print("1. Проверка лицензии через API:")
        response = requests.get(f"{base_url}/api/license", timeout=5)
        if response.status_code == 200:
            license_info = response.json()
            print(f"   Тип лицензии: {license_info['license_type']}")
            print(f"   Статус: {license_info['status']}")
            print(f"   Макс. файлов: {license_info['max_files']}")
        else:
            print(f"   Ошибка: {response.status_code}")
        
        # 2. Проверяем статистику
        print("\n2. Статистика использования:")
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   Файлов в кэше: {stats['cache_stats']['file_count']}")
            print(f"   Размер кэша: {stats['cache_stats']['total_size_mb']} MB")
            print(f"   Запросов сделано: {stats['license_info']['usage_stats']['requests_made']}")
        else:
            print(f"   Ошибка: {response.status_code}")
        
        # 3. Тестируем доступ к файлам
        print("\n3. Тестирование доступа к файлам:")
        response = requests.get(f"{base_url}/api/cache/test_file_0.txt", timeout=5)
        if response.status_code == 200:
            print("   ✓ Файл успешно получен")
        elif response.status_code == 402:
            print("   ✗ Ограничение лицензии")
        else:
            print(f"   Ошибка: {response.status_code}")
        
        # 4. Тестируем активацию лицензии
        print("\n4. Тестирование активации лицензии:")
        license_key = "DEMO1234TEST5678FULL9012LICENSE3456"
        payload = {"license_key": license_key}
        response = requests.post(f"{base_url}/api/license/activate", json=payload, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ {result['message']}")
        else:
            result = response.json()
            print(f"   ✗ {result['error']}")
        
        # 5. Проверяем статус после активации
        print("\n5. Статус после активации:")
        response = requests.get(f"{base_url}/api/license", timeout=5)
        if response.status_code == 200:
            license_info = response.json()
            print(f"   Новый тип: {license_info['license_type']}")
            print(f"   Функции: {license_info['features']}")
        
    except requests.exceptions.ConnectionError:
        print("   Ошибка: Не удалось подключиться к сервису")
        print("   Запустите сервис: python commercial_service_licensed.py")
    except Exception as e:
        print(f"   Ошибка: {e}")
    
    print("\n" + "="*50 + "\n")


def create_demo_environment():
    """Создаем демонстрационное окружение"""
    print("=== Создание демонстрационного окружения ===\n")
    
    # Создаем временные директории
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = os.path.join(temp_dir, "source")
        cache_dir = os.path.join(temp_dir, "cache")
        
        # Создаем тестовые файлы
        test_files = create_test_files(source_dir, 10)
        print(f"Создано {len(test_files)} тестовых файлов")
        
        # Настраиваем переменные окружения
        os.environ["HYBRIDCACHE_SOURCE"] = source_dir
        os.environ["HYBRIDCACHE_DIR"] = cache_dir
        os.environ["HYBRIDCACHE_ENCRYPTION"] = "0"  # Отключаем шифрование для демо
        
        print(f"Исходная директория: {source_dir}")
        print(f"Кэш директория: {cache_dir}")
        print("\nДля запуска сервиса используйте:")
        print("python commercial_service_licensed.py --host 127.0.0.1 --port 8081")


def main():
    """Основная функция демонстрации"""
    print("🚀 Демонстрация системы лицензий HybridCache")
    print("=" * 60)
    
    # Тестируем систему лицензий
    test_license_system()
    
    # Создаем демо-окружение
    create_demo_environment()
    
    # Тестируем API (если сервис запущен)
    test_api_with_license()
    
    print("✅ Демонстрация завершена!")
    print("\nДля полного тестирования:")
    print("1. Запустите сервис: python commercial_service_licensed.py")
    print("2. Запустите тест API: python demo_license_test.py")


if __name__ == "__main__":
    main()

