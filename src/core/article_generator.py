import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import json

from config.config import Config
from models.article import Article, ArticleMetadata
from services.lm_service import LanguageModelService
from services.quality_checker import ArticleQualityChecker

logger = logging.getLogger(__name__)

class ArticleGenerator:
    def __init__(self):
        """Инициализация генератора статей"""
        self.config = Config()
        self.lm_service = LanguageModelService()
        self.quality_checker = ArticleQualityChecker()
        
        logger.info("Инициализация ArticleGenerator завершена")
        
    def generate_article(self, topic: str, language: str = 'ru', category: str = None) -> Optional[Article]:
        """Генерация статьи по заданной теме"""
        try:
            logger.info(f"Начинаем генерацию статьи: topic='{topic}', language='{language}', category='{category}'")
            
            # Генерация текста
            system_prompt = self._create_system_prompt(language)
            user_prompt = f"Напиши статью на тему: {topic}"
            
            content = self.lm_service.generate_text(system_prompt, user_prompt)
            if not content:
                logger.error("Не удалось сгенерировать текст статьи")
                return None
                
            # Проверка качества
            is_valid, quality_metrics = self.quality_checker.comprehensive_check(content)
            if not is_valid:
                logger.warning(f"Статья не прошла проверку качества: {quality_metrics.errors}")
                return None
                
            # Создание метаданных
            metadata = ArticleMetadata(
                title=topic,
                language=language,
                category=category,
                created_at=datetime.now(),
                word_count=len(content.split()),
                readability_score=quality_metrics.readability,
                keywords=list(quality_metrics.keyword_density.keys()),
                validation_passed=True,
                html_report=quality_metrics.html_report
            )
            
            return Article(content=content, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Ошибка при генерации статьи: {str(e)}", exc_info=True)
            return None
            
    def get_categories(self) -> Dict[str, List[str]]:
        """Получение списка категорий"""
        try:
            return {
                'ru': ['Страйкбол', 'Тактическое снаряжение', 'Оружие', 'Тактика и стратегия'],
                'ua': ['Страйкбол', 'Тактичне спорядження', 'Зброя', 'Тактика та стратегія']
            }
        except Exception as e:
            logger.error(f"Ошибка при получении категорий: {str(e)}")
            return {}
            
    def get_topics(self, category: str) -> Dict[str, List[str]]:
        """Получение списка тем для категории"""
        try:
            logger.debug(f"Получение тем для категории: {category}")
            topics = {
                'ru': {
                    'Страйкбол': [
                        'Выбор тактического жилета для страйкбола',
                        'Основы тактики в страйкболе',
                        'Уход за страйкбольным оружием'
                    ],
                    'Тактическое снаряжение': [
                        'Выбор тактического жилета',
                        'Тактические перчатки: критерии выбора',
                        'Тактические ботинки для страйкбола'
                    ],
                    'Оружие': [
                        'Выбор первой страйкбольной винтовки',
                        'Модернизация страйкбольного оружия',
                        'Сравнение популярных моделей страйкбольных пистолетов'
                    ],
                    'Тактика и стратегия': [
                        'Основы командной тактики в страйкболе',
                        'Тактические приемы для новичков',
                        'Продвинутые тактические схемы'
                    ]
                },
                'ua': {
                    'Страйкбол': [
                        'Вибір тактичного жилета для страйкболу',
                        'Основи тактики в страйкболі',
                        'Догляд за страйкбольною зброєю'
                    ],
                    'Тактичне спорядження': [
                        'Вибір тактичного жилета',
                        'Тактичні рукавички: критерії вибору',
                        'Тактичне взуття для страйкболу'
                    ],
                    'Зброя': [
                        'Вибір першої страйкбольної гвинтівки',
                        'Модернізація страйкбольної зброї',
                        'Порівняння популярних моделей страйкбольних пістолетів'
                    ],
                    'Тактика та стратегія': [
                        'Основи командної тактики в страйкболі',
                        'Тактичні прийоми для новачків',
                        'Просунуті тактичні схеми'
                    ]
                }
            }
            logger.debug(f"Доступные категории: {list(topics['ru'].keys())}")
            logger.debug(f"Запрошенная категория: {category}")
            
            # Проверяем категорию в каждом языке
            result = {}
            for lang, lang_topics in topics.items():
                if category in lang_topics:
                    result[lang] = lang_topics[category]
            
            logger.debug(f"Результат: {result}")
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении тем: {str(e)}")
            return {}
            
    def _create_system_prompt(self, language: str) -> str:
        """Создание системного промпта для языковой модели"""
        prompts = {
            'ru': """Ты - эксперт по страйкболу. Напиши информативную статью на тему "{topic}".

Требования к статье:
1. Структура:
   - Заголовок (используй # в начале)
   - Введение (2-3 абзаца)
   - Основные разделы (используй ## для подзаголовков)
   - Заключение
   - Список ключевых моментов

2. Содержание:
   - Используй точные технические термины
   - Укажи конкретные характеристики и параметры
   - Добавь практические советы
   - Включи информацию о безопасности
   - Упомяни популярные модели и бренды
   - Укажи примерные цены
   - Добавь информацию о совместимости

3. Технические детали:
   - Страйкбольные шары (BB) имеют калибр 6мм
   - Скорость шаров обычно 100-150 м/с
   - Энергия выстрела до 3 Дж
   - Дальность эффективной стрельбы 30-50 метров
   - Емкость магазинов 30-300 шаров
   - Вес шаров 0.20-0.43 грамма

4. Формат:
   - Используй Markdown разметку
   - Добавь списки и подсписки
   - Выделяй важные моменты жирным
   - Используй технические термины в кавычках

5. Стиль:
   - Профессиональный, но понятный
   - Без лишних технических деталей
   - С акцентом на практическое применение
   - С учетом опыта разных уровней игроков

6. Качество:
   - Проверь все технические данные
   - Убедись в актуальности информации
   - Проверь корректность терминологии
   - Убедись в логичности структуры

Статья должна быть полезной как для новичков, так и для опытных игроков.""",
            'ua': """Ти - експерт зі страйкболу. Напиши інформативну статтю на тему "{topic}".

Вимоги до статті:
1. Структура:
   - Заголовок (використовуй # на початку)
   - Вступ (2-3 абзаци)
   - Основні розділи (використовуй ## для підзаголовків)
   - Висновок
   - Список ключових моментів

2. Зміст:
   - Використовуй точні технічні терміни
   - Вкажи конкретні характеристики та параметри
   - Додай практичні поради
   - Включи інформацію про безпеку
   - Згадай популярні моделі та бренди
   - Вкажи приблизні ціни
   - Додай інформацію про сумісність

3. Технічні деталі:
   - Страйкбольні кулі (BB) мають калібр 6мм
   - Швидкість куль зазвичай 100-150 м/с
   - Енергія пострілу до 3 Дж
   - Дальність ефективної стрільби 30-50 метрів
   - Ємність магазинів 30-300 куль
   - Вага куль 0.20-0.43 грама

4. Формат:
   - Використовуй Markdown розмітку
   - Додай списки та підсписки
   - Виділяй важливі моменти жирним
   - Використовуй технічні терміни в лапках

5. Стиль:
   - Професійний, але зрозумілий
   - Без зайвих технічних деталей
   - З акцентом на практичне застосування
   - З урахуванням досвіду різних рівнів гравців

6. Якість:
   - Перевір усі технічні дані
   - Переконайся в актуальності інформації
   - Перевір коректність термінології
   - Переконайся в логічності структури

Стаття має бути корисною як для новачків, так і для досвідчених гравців."""
        }
        return prompts.get(language, prompts['ru'])

    def save_article(self, article: Article) -> List[str]:
        """Сохраняет статью в разных форматах"""
        saved_files = []
        base_dir = Path(self.config.get("output.articles_dir"))
        base_dir.mkdir(exist_ok=True)

        for format_type in self.config.get("output.formats"):
            filename = f"{article.metadata.title}_{article.metadata.language}.{format_type}"
            filepath = base_dir / filename
            
            content = article.get_formatted_content(format_type)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files.append(str(filepath))
            logging.info(f"Статья сохранена в {filepath}")

        return saved_files

    def generate_daily_articles(self) -> Dict[str, List[str]]:
        """Генерирует набор статей для ежедневной публикации"""
        results = {"success": [], "failed": []}
        
        for language in ["ru", "ua"]:
            for category in self.topics[language].keys():
                topic = self.topics[language][category][0]  # Берем первую тему из категории
                article = self.generate_article(topic, language, category)
                
                if article:
                    saved_files = self.save_article(article)
                    results["success"].extend(saved_files)
                else:
                    results["failed"].append(f"{topic} ({language})")

        return results 