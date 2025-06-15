import json
import os
from typing import Dict, Any
import logging

class Config:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из файла или использует дефолтную"""
        default_config = {
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
                "formats": ["txt", "markdown"]
            }
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                logging.info(f"Конфигурация загружена из {self.config_file}")
            except Exception as e:
                logging.warning(f"Ошибка загрузки конфигурации: {e}, используется дефолтная")
        else:
            self._save_config(default_config)

        return default_config

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Сохраняет конфигурацию в файл"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение конфигурации по ключу"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Устанавливает значение конфигурации по ключу"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config(self.config) 