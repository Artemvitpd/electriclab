#!/usr/bin/env python3
"""
Генератор лицензионных ключей для HybridCache
Создает ключи для различных типов лицензий
"""

import os
import json
import time
import hashlib
import base64
import uuid
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class LicenseGenerator:
    """Генератор лицензионных ключей"""
    
    def __init__(self, master_key: str = "hybridcache_master_2024"):
        self.master_key = master_key
    
    def generate_license_key(self, license_type: str, customer_id: str = None) -> str:
        """Генерируем лицензионный ключ"""
        # Создаем уникальный ID
        unique_id = str(uuid.uuid4())
        timestamp = str(int(time.time()))
        customer = customer_id or "anonymous"
        
        # Формируем данные для ключа
        key_data = f"{license_type}:{customer}:{unique_id}:{timestamp}"
        
        # Создаем хеш
        key_hash = hashlib.sha256(f"{key_data}:{self.master_key}".encode()).hexdigest()
        
        # Берем первые 32 символа и кодируем в base64
        license_key = base64.b64encode(key_hash[:24].encode()).decode()[:32]
        
        return license_key
    
    def create_license_file(self, license_type: str, customer_id: str, 
                          duration_days: int = 365, output_file: str = None) -> dict:
        """Создаем файл лицензии"""
        
        # Определяем ограничения в зависимости от типа лицензии
        if license_type == "demo":
            limits = {
                "max_files": 100,
                "max_cache_size_mb": 1024,
                "max_requests_per_hour": 1000,
                "features": ["basic_caching", "aes_encryption"],
                "duration_days": 30
            }
        elif license_type == "standard":
            limits = {
                "max_files": 10000,
                "max_cache_size_mb": 10000,
                "max_requests_per_hour": 10000,
                "features": ["basic_caching", "aes_encryption", "gost_encryption"],
                "duration_days": duration_days
            }
        elif license_type == "professional":
            limits = {
                "max_files": 100000,
                "max_cache_size_mb": 100000,
                "max_requests_per_hour": 100000,
                "features": ["basic_caching", "aes_encryption", "gost_encryption", "advanced_analytics"],
                "duration_days": duration_days
            }
        elif license_type == "enterprise":
            limits = {
                "max_files": 1000000,
                "max_cache_size_mb": 1000000,
                "max_requests_per_hour": 1000000,
                "features": ["basic_caching", "aes_encryption", "gost_encryption", 
                           "advanced_analytics", "api_access", "cluster_support"],
                "duration_days": duration_days
            }
        else:
            raise ValueError(f"Unknown license type: {license_type}")
        
        # Генерируем ключ
        license_key = self.generate_license_key(license_type, customer_id)
        
        # Создаем лицензию
        license_data = {
            "license_type": license_type,
            "customer_id": customer_id,
            "license_key": license_key,
            "issued_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=limits["duration_days"])).isoformat(),
            "max_files": limits["max_files"],
            "max_cache_size_mb": limits["max_cache_size_mb"],
            "max_requests_per_hour": limits["max_requests_per_hour"],
            "features": limits["features"],
            "version": "1.0"
        }
        
        # Добавляем подпись
        license_data["signature"] = self._sign_license(license_data)
        
        # Сохраняем файл
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(license_data, f, indent=2)
            print(f"License saved to: {output_file}")
        
        return license_data
    
    def _sign_license(self, license_data: dict) -> str:
        """Подписываем лицензию"""
        license_json = json.dumps(license_data, sort_keys=True)
        signature = hashlib.sha256(f"{license_json}:{self.master_key}".encode()).hexdigest()
        return signature
    
    def create_bulk_licenses(self, license_requests: list, output_dir: str = "licenses"):
        """Создаем множественные лицензии"""
        os.makedirs(output_dir, exist_ok=True)
        
        created_licenses = []
        
        for request in license_requests:
            license_type = request.get("type", "demo")
            customer_id = request.get("customer_id", f"customer_{len(created_licenses) + 1}")
            duration = request.get("duration_days", 365)
            
            filename = f"{license_type}_{customer_id}_{int(time.time())}.license"
            filepath = os.path.join(output_dir, filename)
            
            license_data = self.create_license_file(license_type, customer_id, duration, filepath)
            created_licenses.append({
                "file": filename,
                "license_key": license_data["license_key"],
                "customer_id": customer_id,
                "type": license_type,
                "expires_at": license_data["expires_at"]
            })
        
        # Создаем индексный файл
        index_file = os.path.join(output_dir, "licenses_index.json")
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(created_licenses, f, indent=2)
        
        print(f"Created {len(created_licenses)} licenses in {output_dir}/")
        return created_licenses


def main():
    """Демонстрация генератора лицензий"""
    print("🔑 HybridCache License Generator")
    print("=" * 40)
    
    generator = LicenseGenerator()
    
    # Создаем различные типы лицензий
    license_types = [
        ("demo", "demo_customer", 30),
        ("standard", "company_abc", 365),
        ("professional", "enterprise_xyz", 365),
        ("enterprise", "mega_corp", 730)  # 2 года
    ]
    
    print("\nСоздание лицензий:")
    for license_type, customer_id, duration in license_types:
        print(f"\n{license_type.upper()} лицензия для {customer_id}:")
        
        license_data = generator.create_license_file(
            license_type, customer_id, duration,
            f"{license_type}_{customer_id}.license"
        )
        
        print(f"  Ключ: {license_data['license_key']}")
        print(f"  Действует до: {license_data['expires_at']}")
        print(f"  Макс. файлов: {license_data['max_files']}")
        print(f"  Макс. кэш: {license_data['max_cache_size_mb']} MB")
        print(f"  Функции: {', '.join(license_data['features'])}")
    
    # Создаем пакетные лицензии
    print("\n" + "=" * 40)
    print("Создание пакетных лицензий:")
    
    bulk_requests = [
        {"type": "demo", "customer_id": "startup_1"},
        {"type": "demo", "customer_id": "startup_2"},
        {"type": "standard", "customer_id": "company_1", "duration_days": 365},
        {"type": "professional", "customer_id": "company_2", "duration_days": 365},
        {"type": "enterprise", "customer_id": "enterprise_1", "duration_days": 730}
    ]
    
    created_licenses = generator.create_bulk_licenses(bulk_requests)
    
    print(f"\nСоздано {len(created_licenses)} лицензий:")
    for license_info in created_licenses:
        print(f"  {license_info['type']}: {license_info['customer_id']} -> {license_info['license_key']}")
    
    print("\n✅ Генерация лицензий завершена!")
    print("\nДля активации лицензии используйте:")
    print("POST /api/license/activate")
    print('{"license_key": "YOUR_LICENSE_KEY"}')


if __name__ == "__main__":
    main()

