import os
from dotenv import load_dotenv
from typing import Any, Dict, Optional

# Загружаем переменные окружения из .env файла
load_dotenv()

class Config:
    """Конфигурация приложения"""
    
    # Базовые настройки
    DEBUG = True
    TESTING = False
    
    # Настройки LM Studio
    LM_STUDIO_URL = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1/chat/completions')
    LM_MODEL = os.getenv('LM_STUDIO_MODEL', 'gemma-3-4b-it-qat')
    LM_TEMPERATURE = float(os.getenv('LM_STUDIO_TEMPERATURE', '0.7'))
    LM_MAX_TOKENS = int(os.getenv('LM_STUDIO_MAX_TOKENS', '2000'))
    LM_TOP_P = float(os.getenv('LM_STUDIO_TOP_P', '0.9'))
    LM_FREQUENCY_PENALTY = float(os.getenv('LM_STUDIO_FREQUENCY_PENALTY', '0.0'))
    LM_PRESENCE_PENALTY = float(os.getenv('LM_STUDIO_PRESENCE_PENALTY', '0.0'))
    LM_TIMEOUT = int(os.getenv('LM_STUDIO_TIMEOUT', '30'))
    
    # Настройки генерации статей
    ARTICLE_MIN_LENGTH = int(os.getenv('ARTICLE_MIN_LENGTH', '800'))
    ARTICLE_MAX_LENGTH = int(os.getenv('ARTICLE_MAX_LENGTH', '1200'))
    ARTICLE_TARGET_READABILITY = float(os.getenv('ARTICLE_TARGET_READABILITY', '5.0'))
    ARTICLE_MIN_SENTENCE_LENGTH = int(os.getenv('ARTICLE_MIN_SENTENCE_LENGTH', '5'))
    ARTICLE_MAX_SENTENCE_LENGTH = int(os.getenv('ARTICLE_MAX_SENTENCE_LENGTH', '25'))
    
    # Настройки веб-приложения
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('WEB_PORT', '5000'))
    WEB_DEBUG = DEBUG

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получение значения конфигурации по ключу
        
        Args:
            key: Ключ конфигурации в формате 'section.key'
            default: Значение по умолчанию, если ключ не найден
            
        Returns:
            Any: Значение конфигурации
        """
        try:
            # Разбиваем ключ на секцию и параметр
            section, param = key.split('.')
            
            # Получаем секцию конфигурации
            section_config = getattr(self, section, {})
            
            # Если секция - словарь, получаем значение по ключу
            if isinstance(section_config, dict):
                return section_config.get(param, default)
                
            # Если секция - объект, получаем атрибут
            return getattr(section_config, param, default)
            
        except (ValueError, AttributeError):
            return default
            
    def __getitem__(self, key: str) -> Any:
        """
        Получение значения конфигурации через синтаксис словаря
        
        Args:
            key: Ключ конфигурации
            
        Returns:
            Any: Значение конфигурации
        """
        return self.get(key)
        
    def __contains__(self, key: str) -> bool:
        """
        Проверка наличия ключа в конфигурации
        
        Args:
            key: Ключ конфигурации
            
        Returns:
            bool: True если ключ существует
        """
        return self.get(key) is not None

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