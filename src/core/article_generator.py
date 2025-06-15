import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid

from src.config.config import Config
from src.models.article import Article, ArticleMetadata
from src.services.lm_service import LanguageModelService
from src.services.quality_checker import ArticleQualityChecker

logger = logging.getLogger(__name__)

class ArticleGenerator:
    """Генератор статей для страйкбола"""
    
    def __init__(self, config_file: str = None):
        """Инициализация генератора статей
        
        Args:
            config_file (str, optional): Путь к файлу конфигурации
        """
        self.config = Config(config_file)
        self.lm_service = LanguageModelService(config_file)
        self.quality_checker = ArticleQualityChecker()
        self._load_topics_data()
        
        logger.info("Инициализация ArticleGenerator завершена")
        
    def _load_topics_data(self):
        """Загружает данные о темах и категориях из файла или использует дефолтные"""
        self.topics_data = {
            "ua": {
                "обладнання": [
                    "Вибір тактичного жилета для страйкболу",
                    "Захисне спорядження для новачків",
                    "Модернізація газових приводів",
                    "Вибір оптичного прицілу",
                    "Догляд за акумуляторами LiPo",
                    "Системи розвантаження та носіння спорядження",
                    "Вибір правильного шолома та захисту голови"
                ],
                "технічне": [
                    "Налаштування hop-up в електроприводах",
                    "Тюнінг внутрішніх деталей приводу",
                    "Діагностика несправностей приводів",
                    "Модернізація ствола та резинки hop-up",
                    "Налаштування регулятора тиску в HPA системах"
                ],
                "тактика": [
                    "Тактика ведення бою в CQB",
                    "Камуфляж для лісових ігор",
                    "Снайперська стрільба в страйкболі",
                    "Командна робота та зв'язок",
                    "Позиціонування та переміщення в команді",
                    "Планування та виконання тактичних операцій"
                ]
            },
            "ru": {
                "снаряжение": [
                    "Выбор тактического жилета для страйкбола",
                    "Защитное снаряжение для новичков",
                    "Модернизация газовых приводов",
                    "Выбор оптического прицела",
                    "Уход за аккумуляторами LiPo",
                    "Системы разгрузки и ношения снаряжения",
                    "Выбор правильного шлема и защиты головы"
                ],
                "техническое": [
                    "Настройка hop-up в электроприводах",
                    "Тюнинг внутренних деталей привода",
                    "Диагностика неисправностей приводов",
                    "Модернизация ствола и резинки hop-up",
                    "Настройка регулятора давления в HPA системах"
                ],
                "тактика": [
                    "Тактика ведения боя в CQB",
                    "Камуфляж для лесных игр",
                    "Снайперская стрельба в страйкболе",
                    "Командная работа и связь",
                    "Позиционирование и перемещение в команде",
                    "Планирование и выполнение тактических операций"
                ]
            }
        }
        
        # Проверяем наличие пользовательского файла с темами
        topics_file = Path("src/data/topics.json")
        if topics_file.exists():
            try:
                with open(topics_file, "r", encoding="utf-8") as f:
                    self.topics_data = json.load(f)
                logger.info(f"Загружены пользовательские темы из {topics_file}")
            except Exception as e:
                logger.warning(f"Ошибка загрузки пользовательских тем: {e}")
        
    def generate_article(self, topic: str, language: str = 'ru', category: str = None) -> Optional[Article]:
        """Генерация статьи по заданной теме
        
        Args:
            topic (str): Тема статьи
            language (str, optional): Язык статьи ('ru' или 'ua'). По умолчанию 'ru'.
            category (str, optional): Категория статьи
            
        Returns:
            Optional[Article]: Сгенерированная статья или None при ошибке
        """
        try:
            logger.info(f"Начинаем генерацию статьи: topic='{topic}', language='{language}', category='{category}'")
            
            # Генерация текста
            system_prompt = self._create_system_prompt(language, category)
            user_prompt = f"Напиши статью на тему: {topic}"
            
            content = self.lm_service.generate_text(system_prompt, user_prompt)
            if not content:
                logger.error("Не удалось сгенерировать текст статьи")
                return None
                
            # Проверка качества
            is_valid, quality_metrics = self.quality_checker.comprehensive_check(content, language)
            
            # Создание метаданных
            metadata = ArticleMetadata(
                title=topic,
                language=language,
                category=category or "общее",
                created_at=datetime.now(),
                word_count=len(content.split()),
                readability_score=quality_metrics.get("readability_score", 0),
                keywords=quality_metrics.get("keywords", [])[:10],
                validation_passed=is_valid,
                html_report=quality_metrics.get("html_report", "")
            )
            
            article = Article(content=content, metadata=metadata)
            
            # Сохраняем статью
            output_dir = self.config.get("output.articles_dir", "articles")
            formats = self.config.get("output.formats", ["txt", "markdown", "html"])
            article.save(output_dir, formats)
            
            return article
            
        except Exception as e:
            logger.error(f"Ошибка при генерации статьи: {str(e)}", exc_info=True)
            return None
            
    def get_categories(self) -> Dict[str, List[str]]:
        """Получение списка категорий
        
        Returns:
            Dict[str, List[str]]: Словарь с категориями по языкам
        """
        try:
            result = {}
            
            # Заполняем категории из topics_data
            for lang, categories in self.topics_data.items():
                result[lang] = list(categories.keys())
                
            logger.debug(f"Получены категории: {result}")
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении категорий: {str(e)}")
            return {"ru": [], "ua": []}
            
    def get_topics(self, category: str) -> Dict[str, List[str]]:
        """Получение списка тем для категории
        
        Args:
            category (str): Название категории
            
        Returns:
            Dict[str, List[str]]: Словарь с темами по языкам
        """
        try:
            logger.debug(f"Получение тем для категории: {category}")
            result = {}
            
            # Ищем категорию в каждом языке
            for lang, categories in self.topics_data.items():
                if category in categories:
                    result[lang] = categories[category]
            
            logger.debug(f"Результат: {result}")
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении тем: {str(e)}")
            return {}
            
    def _create_system_prompt(self, language: str, category: str = None) -> str:
        """Создание системного промпта для языковой модели
        
        Args:
            language (str): Язык ('ru' или 'ua')
            category (str, optional): Категория
            
        Returns:
            str: Промпт для языковой модели
        """
        # Базовые промпты для разных языков
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
        
        # Дополнения к промптам в зависимости от категории
        category_additions = {
            # Украинские категории
            "обладнання": "\n\nФОКУС НА ОБЛАДНАННІ:\n- Детальні характеристики типів спорядження\n- Критерії вибору для різних умов гри\n- Поради з підгонки та налаштування\n- Співвідношення ціна/якість без згадки брендів",
            "технічне": "\n\nТЕХНІЧНИЙ ФОКУС:\n- Покрокові інструкції налаштування\n- Діагностика проблем та їх вирішення\n- Безпека при роботі з технікою\n- Інструменти та матеріали для робіт",
            "тактика": "\n\nТАКТИЧНИЙ ФОКУС:\n- Практичні сценарії та ситуації\n- Командна взаємодія\n- Адаптація до різних типів місцевості\n- Психологічні аспекти гри",
            
            # Русские категории
            "снаряжение": "\n\nФОКУС НА СНАРЯЖЕНИИ:\n- Детальные характеристики типов снаряжения\n- Критерии выбора для разных условий игры\n- Советы по подгонке и настройке\n- Соотношение цена/качество без упоминания брендов",
            "техническое": "\n\nТЕХНИЧЕСКИЙ ФОКУС:\n- Пошаговые инструкции настройки\n- Диагностика проблем и их решение\n- Безопасность при работе с техникой\n- Инструменты и материалы для работ",
            "тактика": "\n\nТАКТИЧЕСКИЙ ФОКУС:\n- Практические сценарии и ситуации\n- Командное взаимодействие\n- Адаптация к разным типам местности\n- Психологические аспекты игры"
        }
        
        prompt = prompts.get(language, prompts['ru'])
        
        # Добавляем специфику категории, если она указана
        if category and category in category_additions:
            prompt += category_additions[category]
            
        return prompt
        
    def generate_daily_articles(self, count: int = 1, languages: List[str] = None) -> Dict[str, List[Article]]:
        """Генерация заданного количества статей на каждом языке
        
        Args:
            count (int, optional): Количество статей для каждого языка. По умолчанию 1.
            languages (List[str], optional): Список языков. По умолчанию ['ru', 'ua'].
            
        Returns:
            Dict[str, List[Article]]: Словарь с сгенерированными статьями по языкам
        """
        if languages is None:
            languages = ['ru', 'ua']
            
        result = {lang: [] for lang in languages}
        
        for lang in languages:
            logger.info(f"Генерация {count} статей на языке '{lang}'")
            
            # Получаем все категории для языка
            categories = self.get_categories().get(lang, [])
            
            for i in range(count):
                try:
                    # Выбираем случайную категорию и тему
                    if not categories:
                        logger.warning(f"Нет доступных категорий для языка '{lang}'")
                        continue
                        
                    import random
                    category = random.choice(categories)
                    
                    # Получаем темы для категории
                    topics_by_lang = self.get_topics(category)
                    topics = topics_by_lang.get(lang, [])
                    
                    if not topics:
                        logger.warning(f"Нет доступных тем для категории '{category}' и языка '{lang}'")
                        continue
                        
                    topic = random.choice(topics)
                    
                    # Генерируем статью
                    article = self.generate_article(topic, lang, category)
                    
                    if article:
                        result[lang].append(article)
                        logger.info(f"Статья успешно сгенерирована: '{topic}' ({lang})")
                    else:
                        logger.error(f"Не удалось сгенерировать статью для темы '{topic}'")
                        
                except Exception as e:
                    logger.error(f"Ошибка при генерации статьи на языке '{lang}': {str(e)}", exc_info=True)
                    
        return result 