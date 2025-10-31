#!/usr/bin/env python3
"""
Система демо-лицензий для HybridCache
Поддерживает ограниченный демо-режим с возможностью активации полной лицензии
"""

import os
import json
import time
import hashlib
import base64
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


@dataclass
class LicenseInfo:
    """Информация о лицензии"""
    license_type: str  # "demo", "trial", "full"
    expires_at: datetime
    max_files: int
    max_cache_size_mb: int
    max_requests_per_hour: int
    features: list
    customer_id: str
    issued_at: datetime
    license_key: str


class DemoLicenseSystem:
    """Система управления демо-лицензиями"""
    
    def __init__(self, license_file: str = "hybridcache.license"):
        self.license_file = Path(license_file)
        self.usage_file = Path("usage_stats.json")
        self.license_info: Optional[LicenseInfo] = None
        self.usage_stats = self._load_usage_stats()
        
        # Мастер-ключ для подписи лицензий (в продакшене должен быть в безопасном месте)
        self.master_key = os.getenv("HYBRIDCACHE_MASTER_KEY", "demo_master_key_2024")
        
        # Загружаем лицензию при инициализации
        self._load_license()
    
    def _load_usage_stats(self) -> Dict:
        """Загружаем статистику использования"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            "files_processed": 0,
            "requests_made": 0,
            "cache_size_bytes": 0,
            "last_reset": time.time(),
            "hourly_requests": {}
        }
    
    def _save_usage_stats(self):
        """Сохраняем статистику использования"""
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_stats, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save usage stats: {e}")
    
    def _load_license(self):
        """Загружаем лицензию из файла"""
        if not self.license_file.exists():
            # Создаем демо-лицензию по умолчанию
            self._create_demo_license()
            return
        
        try:
            with open(self.license_file, 'r', encoding='utf-8') as f:
                license_data = json.load(f)
            
            # Проверяем подпись лицензии
            if not self._verify_license_signature(license_data):
                print("Warning: License signature verification failed. Creating demo license.")
                self._create_demo_license()
                return
            
            # Восстанавливаем объект лицензии
            self.license_info = LicenseInfo(
                license_type=license_data['license_type'],
                expires_at=datetime.fromisoformat(license_data['expires_at']),
                max_files=license_data['max_files'],
                max_cache_size_mb=license_data['max_cache_size_mb'],
                max_requests_per_hour=license_data['max_requests_per_hour'],
                features=license_data['features'],
                customer_id=license_data['customer_id'],
                issued_at=datetime.fromisoformat(license_data['issued_at']),
                license_key=license_data['license_key']
            )
            
            print(f"License loaded: {self.license_info.license_type} (expires: {self.license_info.expires_at})")
            
        except Exception as e:
            print(f"Error loading license: {e}. Creating demo license.")
            self._create_demo_license()
    
    def _create_demo_license(self):
        """Создаем демо-лицензию с ограничениями"""
        demo_license = LicenseInfo(
            license_type="demo",
            expires_at=datetime.now() + timedelta(days=30),  # 30 дней демо
            max_files=100,  # Максимум 100 файлов
            max_cache_size_mb=1024,  # Максимум 1GB кэша
            max_requests_per_hour=1000,  # 1000 запросов в час
            features=["basic_caching", "aes_encryption"],  # Базовые функции
            customer_id="demo_user",
            issued_at=datetime.now(),
            license_key=self._generate_license_key()
        )
        
        self.license_info = demo_license
        self._save_license()
        print("Demo license created with 30-day trial period")
    
    def _generate_license_key(self) -> str:
        """Генерируем уникальный ключ лицензии"""
        unique_id = str(uuid.uuid4())
        timestamp = str(int(time.time()))
        data = f"{unique_id}:{timestamp}"
        return base64.b64encode(data.encode()).decode()[:32]
    
    def _sign_license(self, license_data: Dict) -> str:
        """Подписываем лицензию"""
        # Создаем хеш от содержимого лицензии
        license_json = json.dumps(license_data, sort_keys=True)
        signature = hashlib.sha256(f"{license_json}:{self.master_key}".encode()).hexdigest()
        return signature
    
    def _verify_license_signature(self, license_data: Dict) -> bool:
        """Проверяем подпись лицензии"""
        if 'signature' not in license_data:
            return False
        
        provided_signature = license_data['signature']
        del license_data['signature']  # Убираем подпись для вычисления хеша
        
        expected_signature = self._sign_license(license_data)
        license_data['signature'] = provided_signature  # Восстанавливаем подпись
        
        return provided_signature == expected_signature
    
    def _save_license(self):
        """Сохраняем лицензию в файл"""
        if not self.license_info:
            return
        
        license_data = {
            'license_type': self.license_info.license_type,
            'expires_at': self.license_info.expires_at.isoformat(),
            'max_files': self.license_info.max_files,
            'max_cache_size_mb': self.license_info.max_cache_size_mb,
            'max_requests_per_hour': self.license_info.max_requests_per_hour,
            'features': self.license_info.features,
            'customer_id': self.license_info.customer_id,
            'issued_at': self.license_info.issued_at.isoformat(),
            'license_key': self.license_info.license_key,
            'version': '1.0'
        }
        
        # Добавляем подпись
        license_data['signature'] = self._sign_license(license_data)
        
        try:
            with open(self.license_file, 'w', encoding='utf-8') as f:
                json.dump(license_data, f, indent=2)
            print(f"License saved: {self.license_info.license_type}")
        except Exception as e:
            print(f"Error saving license: {e}")
    
    def check_license_status(self) -> Tuple[bool, str]:
        """Проверяем статус лицензии"""
        if not self.license_info:
            return False, "No license found"
        
        # Проверяем срок действия
        if datetime.now() > self.license_info.expires_at:
            return False, f"License expired on {self.license_info.expires_at}"
        
        # Проверяем ограничения
        if self.license_info.license_type == "demo":
            days_left = (self.license_info.expires_at - datetime.now()).days
            return True, f"Demo license active ({days_left} days remaining)"
        elif self.license_info.license_type == "full":
            return True, "Full license active"
        else:
            return True, f"{self.license_info.license_type} license active"
    
    def check_file_limit(self, current_files: int) -> Tuple[bool, str]:
        """Проверяем лимит файлов"""
        if not self.license_info:
            return False, "No license"
        
        if current_files >= self.license_info.max_files:
            return False, f"File limit exceeded ({self.license_info.max_files} max)"
        
        return True, f"Files: {current_files}/{self.license_info.max_files}"
    
    def check_cache_size_limit(self, current_size_bytes: int) -> Tuple[bool, str]:
        """Проверяем лимит размера кэша"""
        if not self.license_info:
            return False, "No license"
        
        max_size_bytes = self.license_info.max_cache_size_mb * 1024 * 1024
        
        if current_size_bytes >= max_size_bytes:
            return False, f"Cache size limit exceeded ({self.license_info.max_cache_size_mb}MB max)"
        
        return True, f"Cache: {current_size_bytes // (1024*1024)}MB/{self.license_info.max_cache_size_mb}MB"
    
    def check_request_limit(self) -> Tuple[bool, str]:
        """Проверяем лимит запросов в час"""
        if not self.license_info:
            return False, "No license"
        
        current_hour = int(time.time() // 3600)
        current_requests = self.usage_stats.get('hourly_requests', {}).get(str(current_hour), 0)
        
        if current_requests >= self.license_info.max_requests_per_hour:
            return False, f"Request limit exceeded ({self.license_info.max_requests_per_hour}/hour)"
        
        return True, f"Requests: {current_requests}/{self.license_info.max_requests_per_hour}"
    
    def increment_request_count(self):
        """Увеличиваем счетчик запросов"""
        current_hour = int(time.time() // 3600)
        
        if 'hourly_requests' not in self.usage_stats:
            self.usage_stats['hourly_requests'] = {}
        
        if str(current_hour) not in self.usage_stats['hourly_requests']:
            self.usage_stats['hourly_requests'][str(current_hour)] = 0
        
        self.usage_stats['hourly_requests'][str(current_hour)] += 1
        self.usage_stats['requests_made'] += 1
        
        # Очищаем старые записи (старше 24 часов)
        cutoff_hour = current_hour - 24
        for hour in list(self.usage_stats['hourly_requests'].keys()):
            if int(hour) < cutoff_hour:
                del self.usage_stats['hourly_requests'][hour]
        
        self._save_usage_stats()
    
    def increment_file_count(self):
        """Увеличиваем счетчик файлов"""
        self.usage_stats['files_processed'] += 1
        self._save_usage_stats()
    
    def update_cache_size(self, size_bytes: int):
        """Обновляем размер кэша"""
        self.usage_stats['cache_size_bytes'] = size_bytes
        self._save_usage_stats()
    
    def has_feature(self, feature: str) -> bool:
        """Проверяем доступность функции"""
        if not self.license_info:
            return False
        
        return feature in self.license_info.features
    
    def activate_full_license(self, license_key: str) -> Tuple[bool, str]:
        """Активируем полную лицензию"""
        # В реальной реализации здесь была бы проверка с сервером лицензий
        # Для демонстрации проверяем формат ключа
        
        if not license_key or len(license_key) != 32:
            return False, "Invalid license key format"
        
        # Создаем полную лицензию
        full_license = LicenseInfo(
            license_type="full",
            expires_at=datetime.now() + timedelta(days=365),  # 1 год
            max_files=1000000,  # Практически без ограничений
            max_cache_size_mb=1000000,  # 1TB
            max_requests_per_hour=1000000,  # Практически без ограничений
            features=["basic_caching", "aes_encryption", "gost_encryption", "advanced_analytics", "api_access"],
            customer_id="licensed_user",
            issued_at=datetime.now(),
            license_key=license_key
        )
        
        self.license_info = full_license
        self._save_license()
        
        return True, "Full license activated successfully"
    
    def get_license_info(self) -> Dict:
        """Получаем информацию о лицензии для API"""
        if not self.license_info:
            return {"status": "no_license"}
        
        is_valid, status_msg = self.check_license_status()
        
        return {
            "license_type": self.license_info.license_type,
            "status": "active" if is_valid else "expired",
            "status_message": status_msg,
            "expires_at": self.license_info.expires_at.isoformat(),
            "max_files": self.license_info.max_files,
            "max_cache_size_mb": self.license_info.max_cache_size_mb,
            "max_requests_per_hour": self.license_info.max_requests_per_hour,
            "features": self.license_info.features,
            "customer_id": self.license_info.customer_id,
            "usage_stats": self.usage_stats
        }


# Глобальный экземпляр системы лицензий
license_system = DemoLicenseSystem()


def get_license_system() -> DemoLicenseSystem:
    """Получаем экземпляр системы лицензий"""
    return license_system


if __name__ == "__main__":
    # Демонстрация работы системы лицензий
    print("=== HybridCache License System Demo ===")
    
    system = get_license_system()
    
    # Проверяем статус
    is_valid, status = system.check_license_status()
    print(f"License Status: {status}")
    
    # Получаем информацию о лицензии
    info = system.get_license_info()
    print(f"License Info: {json.dumps(info, indent=2)}")
    
    # Проверяем ограничения
    file_ok, file_msg = system.check_file_limit(50)
    print(f"File Limit: {file_msg}")
    
    cache_ok, cache_msg = system.check_cache_size_limit(512 * 1024 * 1024)  # 512MB
    print(f"Cache Limit: {cache_msg}")
    
    req_ok, req_msg = system.check_request_limit()
    print(f"Request Limit: {req_msg}")
    
    # Проверяем функции
    print(f"Basic Caching: {system.has_feature('basic_caching')}")
    print(f"GOST Encryption: {system.has_feature('gost_encryption')}")
    print(f"Advanced Analytics: {system.has_feature('advanced_analytics')}")

