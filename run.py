#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Файл запуска генератора статей для страйкбола
"""
import os
import sys
import json
import logging
import requests
import time
from pathlib import Path
import argparse
import webbrowser
import subprocess
import threading

# Добавляем директорию проекта в PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8',
    handlers=[
        logging.FileHandler('run.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_lm_studio_connection(url: str = "http://localhost:1234/v1/models", max_retries: int = 5) -> bool:
    """
    Проверяет соединение с LM Studio
    
    Args:
        url (str): URL для проверки
        max_retries (int): Максимальное количество попыток
        
    Returns:
        bool: True если соединение установлено, иначе False
    """
    logger.info("Проверка соединения с LM Studio...")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                logger.info("Соединение с LM Studio установлено успешно")
                return True
            else:
                logger.warning(f"Неудачная попытка соединения с LM Studio: HTTP {response.status_code}")
        except requests.RequestException as e:
            logger.warning(f"Попытка {attempt + 1}/{max_retries} соединения с LM Studio не удалась: {e}")
        
        # Пауза перед следующей попыткой
        if attempt < max_retries - 1:
            logger.info("Попытка переподключения через 2 секунды...")
            time.sleep(2)
    
    logger.error(f"Не удалось установить соединение с LM Studio после {max_retries} попыток")
    return False

def start_web_app(host: str = "localhost", port: int = 5000):
    """
    Запускает веб-приложение
    
    Args:
        host (str): Хост для запуска
        port (int): Порт для запуска
    """
    try:
        from src.web_app import app

        # Запускаем веб-приложение
        logger.info(f"Запуск веб-приложения на http://{host}:{port}")
        app.run(host=host, port=port, debug=False)
    except Exception as e:
        logger.error(f"Ошибка при запуске веб-приложения: {e}", exc_info=True)
        sys.exit(1)

def open_browser(url: str, delay: int = 2):
    """
    Открывает браузер после задержки
    
    Args:
        url (str): URL для открытия
        delay (int): Задержка в секундах
    """
    def _open_browser():
        time.sleep(delay)
        logger.info(f"Открытие браузера с URL: {url}")
        webbrowser.open(url)
    
    thread = threading.Thread(target=_open_browser)
    thread.daemon = True
    thread.start()

def main():
    """Основная функция запуска"""
    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(description="Запуск генератора статей для страйкбола")
    parser.add_argument('--host', default='localhost', help='Хост для запуска веб-приложения')
    parser.add_argument('--port', type=int, default=5000, help='Порт для запуска веб-приложения')
    parser.add_argument('--no-browser', action='store_true', help='Не открывать браузер автоматически')
    parser.add_argument('--skip-check', action='store_true', help='Пропустить проверку соединения с LM Studio')
    
    args = parser.parse_args()
    
    # Проверяем соединение с LM Studio (если не указан флаг --skip-check)
    if not args.skip_check and not check_lm_studio_connection():
        print("\n========================================================")
        print("ОШИБКА: Не удалось установить соединение с LM Studio")
        print("Пожалуйста, убедитесь, что:")
        print("1. LM Studio запущен")
        print("2. Модель загружена и доступна")
        print("3. Локальный сервер запущен на порту 1234")
        print("\nЗапуск с пропуском проверки: python run.py --skip-check")
        print("========================================================\n")
        sys.exit(1)
    
    # Проверяем наличие необходимых директорий и файлов
    os.makedirs("articles", exist_ok=True)
    os.makedirs("src/data", exist_ok=True)
    
    # Открываем браузер, если не указан флаг --no-browser
    if not args.no_browser:
        open_browser(f"http://{args.host}:{args.port}")
    
    # Запускаем веб-приложение
    start_web_app(args.host, args.port)

if __name__ == "__main__":
    main() 