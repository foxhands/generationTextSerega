import requests
import logging
import time
from typing import Optional, Dict, Any, List
from src.config.config import Config

logger = logging.getLogger(__name__)

class LanguageModelService:
    """Сервис для работы с языковыми моделями через LM Studio API"""
    
    def __init__(self, config_file: str = None):
        """Инициализация сервиса
        
        Args:
            config_file (str, optional): Путь к файлу конфигурации
        """
        self.config = Config(config_file)
        self.api_url = self.config.get("lm_studio.url", "http://localhost:1234/v1/chat/completions")
        logger.info(f"Инициализирован LanguageModelService с API URL: {self.api_url}")
        
    def generate_text(self, system_prompt: str, user_prompt: str, 
                     max_retries: int = None) -> Optional[str]:
        """Генерирует текст с помощью языковой модели
        
        Args:
            system_prompt (str): Системный промпт для модели
            user_prompt (str): Пользовательский запрос
            max_retries (int, optional): Максимальное количество попыток при ошибке
            
        Returns:
            Optional[str]: Сгенерированный текст или None при ошибке
        """
        if max_retries is None:
            max_retries = self.config.get("article_settings.max_retries", 3)
            
        for attempt in range(max_retries):
            try:
                logger.debug(f"Попытка {attempt + 1}/{max_retries} генерации текста")
                
                # Подготовка запроса
                payload = self._prepare_request_payload(system_prompt, user_prompt)
                
                # Отправка запроса с таймаутом
                timeout = self.config.get("lm_studio.timeout", 60)
                logger.debug(f"Отправка запроса к LM Studio с таймаутом {timeout} сек")
                
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=timeout
                )
                
                # Анализ ответа
                if response.status_code == 200:
                    # Получение текста из ответа
                    content = self._extract_response_content(response.json())
                    if content:
                        logger.info("Текст успешно сгенерирован")
                        return content
                    else:
                        logger.warning("Получен пустой ответ от LM Studio")
                else:
                    logger.warning(f"Ошибка от LM Studio API: статус {response.status_code}, {response.text}")
                    
            except requests.RequestException as e:
                logger.error(f"Ошибка соединения с LM Studio: {str(e)}")
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при генерации текста: {str(e)}", exc_info=True)
            
            # Подождем перед следующей попыткой
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Экспоненциальное увеличение времени ожидания
                logger.info(f"Ожидание {wait_time} сек перед следующей попыткой...")
                time.sleep(wait_time)
                
        logger.error(f"Не удалось сгенерировать текст после {max_retries} попыток")
        return None
        
    def _prepare_request_payload(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Подготовка payload для запроса к API
        
        Args:
            system_prompt (str): Системный промпт
            user_prompt (str): Пользовательский промпт
            
        Returns:
            Dict[str, Any]: Подготовленный payload
        """
        return {
            "model": self.config.get("lm_studio.model", "gemma-3-4b-it-qat"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": self.config.get("lm_studio.max_tokens", 2500),
            "temperature": self.config.get("lm_studio.temperature", 0.7)
        }
        
    def _extract_response_content(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Извлечение контента из ответа API
        
        Args:
            response_data (Dict[str, Any]): Данные ответа API
            
        Returns:
            Optional[str]: Извлеченный текст или None
        """
        try:
            choices = response_data.get("choices", [])
            if choices and len(choices) > 0:
                message = choices[0].get("message", {})
                content = message.get("content", "")
                return content
                
            logger.warning("Неправильная структура ответа от LM Studio")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении содержимого ответа: {str(e)}")
            return None
            
    def test_connection(self) -> bool:
        """Проверка соединения с API
        
        Returns:
            bool: True если соединение установлено, иначе False
        """
        try:
            # Простой запрос для проверки соединения
            test_payload = self._prepare_request_payload(
                "Ты помощник.", 
                "Привет! Это проверка соединения."
            )
            
            # Устанавливаем небольшое количество токенов для быстрого ответа
            test_payload["max_tokens"] = 10
            
            response = requests.post(
                self.api_url,
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=5  # Короткий таймаут для теста
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Ошибка при проверке соединения с LM Studio: {str(e)}")
            return False
            
    def get_supported_models(self) -> List[str]:
        """Получение списка поддерживаемых моделей (если API поддерживает такой запрос)
        
        Returns:
            List[str]: Список названий доступных моделей или пустой список при ошибке
        """
        try:
            # В контексте LM Studio проверяем доступность endpoint /models
            response = requests.get(
                "http://localhost:1234/v1/models",
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                models_data = response.json()
                model_names = [model.get("id") for model in models_data.get("data", [])]
                return model_names
            else:
                logger.warning(f"Не удалось получить список моделей: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей: {str(e)}")
            return [] 