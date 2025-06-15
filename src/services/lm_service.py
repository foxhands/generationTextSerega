import requests
import time
from typing import Optional, Dict, Any
import logging
import json
from config.config import Config

logger = logging.getLogger(__name__)

class LanguageModelService:
    def __init__(self):
        self.api_url = "http://localhost:1234/v1/completions"
        self.model = Config.LM_MODEL
        self.max_tokens = Config.LM_MAX_TOKENS
        self.temperature = Config.LM_TEMPERATURE
        self.top_p = Config.LM_TOP_P
        self.frequency_penalty = Config.LM_FREQUENCY_PENALTY
        self.presence_penalty = Config.LM_PRESENCE_PENALTY
        self.timeout = getattr(Config, 'LM_TIMEOUT', 30)
        self.max_retries = 3
        self.retry_delay = 1
        
        logger.info(f"Инициализация LanguageModelService с параметрами: model={self.model}, max_tokens={self.max_tokens}, temperature={self.temperature}")
        
    def generate_text(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Генерация текста с использованием языковой модели"""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"system_prompt: {system_prompt}")
                logger.debug(f"user_prompt: {user_prompt}")
                
                data = {
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "frequency_penalty": self.frequency_penalty,
                    "presence_penalty": self.presence_penalty
                }
                
                logger.debug(f"Отправка запроса к LM Studio: {json.dumps(data, ensure_ascii=False)}")
                response = self._make_request(data)
                
                if not response:
                    logger.error("LM Studio вернул пустой ответ")
                    continue
                    
                if "choices" not in response or not response["choices"]:
                    logger.error(f"Неожиданный формат ответа от LM Studio: {json.dumps(response, ensure_ascii=False)}")
                    continue
                    
                return response["choices"][0]["text"]
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка сети при запросе к LM Studio: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
            except Exception as e:
                logger.error(f"Неожиданная ошибка при генерации текста: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                    
        logger.error(f"Не удалось сгенерировать текст после {self.max_retries} попыток")
        return None
        
    def _make_request(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Выполнение HTTP запроса к API языковой модели"""
        try:
            response = requests.post(
                self.api_url,
                json=data,
                timeout=self.timeout
            )
            
            logger.debug(f"Получен ответ от LM Studio: {response.text}")
            
            if response.status_code != 200:
                logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return None
                
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error("Таймаут при запросе к LM Studio")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к LM Studio: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при разборе JSON ответа: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе: {str(e)}")
            return None 