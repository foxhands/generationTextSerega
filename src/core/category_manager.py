import json
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class CategoryManager:
    """Менеджер категорий статей"""
    
    def __init__(self, categories_file: str = None):
        """
        Инициализация менеджера категорий
        
        Args:
            categories_file: Путь к файлу с категориями
        """
        if categories_file is None:
            categories_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'data',
                'categories.json'
            )
        
        self.categories_file = categories_file
        self.categories = self._load_categories()
        
    def _load_categories(self) -> Dict:
        """
        Загрузка категорий из файла
        
        Returns:
            Dict: Словарь с категориями
        """
        try:
            with open(self.categories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки категорий: {str(e)}")
            return {}
            
    def get_categories(self, language: str = 'ru') -> List[Dict]:
        """
        Получение всех категорий для указанного языка
        
        Args:
            language: Код языка (ru/en)
            
        Returns:
            List[Dict]: Список категорий в формате [{'id': str, 'name': str, 'description': str}]
        """
        categories = self.categories.get(language, {})
        return [
            {
                'id': category_id,
                'name': category_data['name'],
                'description': category_data['description']
            }
            for category_id, category_data in categories.items()
        ]
        
    def get_category(self, category_id: str, language: str = 'ru') -> Optional[Dict]:
        """
        Получение информации о конкретной категории
        
        Args:
            category_id: Идентификатор категории
            language: Код языка (ru/en)
            
        Returns:
            Optional[Dict]: Информация о категории или None
        """
        categories = self.categories.get(language, {})
        category_data = categories.get(category_id)
        if category_data:
            return {
                'id': category_id,
                'name': category_data['name'],
                'description': category_data['description']
            }
        return None
        
    def get_topics(self, category_id: str, language: str = 'ru') -> List[str]:
        """
        Получение списка тем для категории
        
        Args:
            category_id: Идентификатор категории
            language: Код языка (ru/en)
            
        Returns:
            List[str]: Список тем
        """
        category = self.categories.get(language, {}).get(category_id)
        if category:
            return category.get('topics', [])
        return []
        
    def get_all_topics(self, language: str = 'ru') -> List[str]:
        """
        Получение всех тем для указанного языка
        
        Args:
            language: Код языка (ru/en)
            
        Returns:
            List[str]: Список всех тем
        """
        topics = []
        for category in self.categories.get(language, {}).values():
            topics.extend(category.get('topics', []))
        return topics 