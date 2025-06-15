import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env файла
load_dotenv()

class Config:
    """Класс для управления конфигурацией приложения"""
    
    def __init__(self, config_file: str = None):
        """Инициализация конфигурации
        
        Args:
            config_file (str, optional): Путь к файлу конфигурации. По умолчанию ищет в корне проекта.
        """
        self.default_config = {
            "lm_studio": {
                "url": "http://localhost:1234/v1/chat/completions",
                "model": "gemma-3-4b-it-qat",
                "max_tokens": 2500,
                "temperature": 0.7,
                "timeout": 60
            },
            "article_settings": {
                "min_word_count": 800,
                "max_word_count": 1200,
                "target_readability": 7.0,
                "max_retries": 3
            },
            "output": {
                "articles_dir": "articles",
                "backup_dir": "backups",
                "formats": ["txt", "markdown", "html"]
            }
        }
        
        # Пытаемся найти файл конфигурации, если путь не указан явно
        if config_file is None:
            # Проверяем сначала в src/config
            possible_locations = [
                Path("config.json"),
                Path("src/config/config.json"),
                Path(os.path.dirname(__file__)) / "config.json"
            ]
            
            for location in possible_locations:
                if location.exists():
                    config_file = str(location)
                    logger.info(f"Найден файл конфигурации: {config_file}")
                    break
        
        # Загружаем пользовательскую конфигурацию, если такая есть
        self.config = self.default_config.copy()
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # Объединяем конфигурации
                self._deep_update(self.config, user_config)
                logger.info(f"Конфигурация загружена из {config_file}")
            except Exception as e:
                logger.warning(f"Ошибка загрузки конфигурации: {e}, используется дефолтная")
                
    def get(self, key_path: str, default=None):
        """Получение значения конфигурации по пути ключей
        
        Args:
            key_path (str): Путь ключей, разделенный точками (например, "lm_studio.url")
            default: Значение по умолчанию, если ключ не найден
            
        Returns:
            Значение по указанному пути или значение по умолчанию
        """
        keys = key_path.split('.')
        result = self.config
        
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return default
        
        return result
    
    def _deep_update(self, base_dict: dict, update_dict: dict) -> None:
        """Рекурсивное обновление словаря
        
        Args:
            base_dict (dict): Базовый словарь для обновления
            update_dict (dict): Словарь с обновлениями
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
                
    def save(self, config_file: str = "config.json"):
        """Сохранить текущую конфигурацию в файл
        
        Args:
            config_file (str, optional): Путь к файлу для сохранения. По умолчанию "config.json".
        """
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"Конфигурация сохранена в {config_file}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении конфигурации: {e}")
            return False

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    HOST = '127.0.0.1'

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = int(os.getenv('PORT', 5000))

class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    DEBUG = True

# Словарь с конфигурациями
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Получение конфигурации в зависимости от окружения"""
    env = os.getenv('FLASK_ENV', 'default')
    return config[env] 