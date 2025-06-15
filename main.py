import random
import json
import os
import requests
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('article_generator.log'),
        logging.StreamHandler()
    ]
)


@dataclass
class ArticleMetadata:
    title: str
    language: str
    category: str
    created_at: str
    word_count: int
    readability_score: float
    keywords: List[str]
    validation_passed: bool


class ArticleGenerator:
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.topics = self.load_topics()
        self.quality_checker = ArticleQualityChecker()

    def load_config(self, config_file: str) -> dict:
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

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # Рекурсивное обновление конфигурации
                self._deep_update(default_config, user_config)
                logging.info(f"Конфигурация загружена из {config_file}")
            except Exception as e:
                logging.warning(f"Ошибка загрузки конфигурации: {e}, используется дефолтная")
        else:
            # Сохраняем дефолтную конфигурацию
            try:
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                logging.info(f"Создан файл конфигурации: {config_file}")
            except Exception as e:
                logging.warning(f"Не удалось создать файл конфигурации: {e}")

        return default_config

    def _deep_update(self, base_dict: dict, update_dict: dict) -> None:
        """Рекурсивно обновляет словарь"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def load_topics(self) -> dict:
        """Расширенный список тем с категориями"""
        return {
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

    def create_enhanced_system_prompt(self, language: str = "ua", category: str = None) -> str:
        """Создает улучшенный системный промпт с учетом категории"""

        base_prompts = {
            "ua": """Ти експерт зі страйкболу з 15-річним досвідом. Пишеш високоякісні статті українською мовою.

ОБОВ'ЯЗКОВІ ПРАВИЛА:
1. Пиши ТІЛЬКИ про страйкбол (airsoft), НІ В ЯКОМУ РАЗІ не про пейнтбол
2. Використовуй правильну українську термінологію:
   - Привод = airsoft gun/replica (автомат, пістолет, кулемет)
   - Захист = protection/armor (броня, жилет, маска)
   - Розвантаження = chest rig/battle belt (система носіння спорядження)
   - Тактичний жилет = plate carrier/tactical vest
   - Hop-up = система підкручування кульки
   - Кулечки 6мм = 6mm BBs (боєприпаси)
   - Магазин = magazine (не обойма!)
   - Цівка = handguard/rail system

3. Технічні характеристики для України:
   - Кулечки: 6мм (0.20г-0.43г)
   - Швидкість: до 1.5 Дж для CQB, до 2.5 Дж для відкритих ігор
   - Акумулятори: LiPo 7.4V, 11.1V, LiFe 9.9V
   - Популярні платформи: М4, АК, G36, MP5, P90

4. Структура статті:
   - Заголовок (привабливий, без слова "стаття")
   - Вступ (2-3 речення, чіткий хук)
   - 4-6 розділів з підзаголовками
   - Практичні поради з нумерованими списками
   - Висновок з основними тезами
   - Обсяг: 900-1200 слів""",

            "ru": """Ты эксперт по страйкболу с 15-летним опытом. Пишешь качественные статьи на русском языке.

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:
1. Пиши ТОЛЬКО о страйкболе (airsoft), НИ В КОЕМ СЛУЧАЕ не о пейнтболе
2. Используй правильную русскую терминологию:
   - Привод = airsoft gun/replica (автомат, пистолет, пулемет)
   - Защита = protection/armor (броня, жилет, маска)
   - Разгрузка = chest rig/battle belt (система ношения снаряжения)
   - Тактический жилет = plate carrier/tactical vest
   - Hop-up = система подкрутки шарика
   - Шарики 6мм = 6mm BBs (боеприпасы)
   - Магазин = magazine (не обойма!)
   - Цевье = handguard/rail system

3. Технические характеристики для России:
   - Шарики: 6мм (0.20г-0.43г)
   - Скорость: до 1.5 Дж для CQB, до 3 Дж для открытых игр
   - Аккумуляторы: LiPo 7.4V, 11.1V, LiFe 9.9V
   - Популярные платформы: М4, АК, G36, MP5, P90

4. Структура статьи:
   - Заголовок (привлекательный, без слова "статья")
   - Вступление (2-3 предложения, четкий хук)
   - 4-6 разделов с подзаголовками
   - Практические советы с нумерованными списками
   - Заключение с основными тезисами
   - Объем: 900-1200 слов"""
        }

        category_additions = {
            "обладнання": "\n\nФОКУС НА ОБЛАДНАННІ:\n- Детальні характеристики типів спорядження\n- Критерії вибору для різних умов гри\n- Поради з підгонки та налаштування\n- Співвідношення ціна/якість без згадки брендів",
            "снаряжение": "\n\nФОКУС НА СНАРЯЖЕНИИ:\n- Детальные характеристики типов снаряжения\n- Критерии выбора для разных условий игры\n- Советы по подгонке и настройке\n- Соотношение цена/качество без упоминания брендов",
            "технічне": "\n\nТЕХНІЧНИЙ ФОКУС:\n- Покрокові інструкції налаштування\n- Діагностика проблем та їх вирішення\n- Безпека при роботі з технікою\n- Інструменти та матеріали для робіт",
            "техническое": "\n\nТЕХНИЧЕСКИЙ ФОКУС:\n- Пошаговые инструкции настройки\n- Диагностика проблем и их решение\n- Безопасность при работе с техникой\n- Инструменты и материалы для работ",
            "тактика": "\n\nТАКТИЧНИЙ ФОКУС:\n- Практичні сценарії та ситуації\n- Командна взаємодія\n- Адаптація до різних типів місцевості\n- Психологічні аспекти гри"
        }

        prompt = base_prompts.get(language, base_prompts["ua"])

        if category and category in category_additions:
            prompt += category_additions[category]

        return prompt

    def call_lm_studio_with_retry(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Вызов LM Studio с повторными попытками и улучшенной обработкой ошибок"""

        max_retries = self.config["article_settings"]["max_retries"]
        timeout = self.config["lm_studio"]["timeout"]

        for attempt in range(max_retries):
            try:
                payload = {
                    "model": self.config["lm_studio"]["model"],
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": self.config["lm_studio"]["max_tokens"],
                    "temperature": self.config["lm_studio"]["temperature"]
                }

                response = requests.post(
                    self.config["lm_studio"]["url"],
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=timeout
                )

                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        logging.info(f"Статья сгенерирована успешно (попытка {attempt + 1})")
                        return content
                    else:
                        logging.warning(f"Неожиданный формат ответа (попытка {attempt + 1})")
                else:
                    logging.warning(f"Ошибка API {response.status_code} (попытка {attempt + 1}): {response.text}")

            except requests.exceptions.Timeout:
                logging.warning(f"Таймаут запроса (попытка {attempt + 1})")
            except requests.exceptions.ConnectionError:
                logging.error("Не удается подключиться к LM Studio")
                break
            except Exception as e:
                logging.error(f"Ошибка при генерации (попытка {attempt + 1}): {e}")

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logging.info(f"Ожидание {wait_time} секунд перед повторной попыткой...")
                time.sleep(wait_time)

        return None

    def select_topic_by_category(self, language: str) -> Tuple[str, str]:
        """Выбирает тему с учетом категории"""
        if language not in self.topics:
            logging.error(f"Неподдерживаемый язык: {language}")
            return None, None

        categories = list(self.topics[language].keys())
        selected_category = random.choice(categories)
        topics_in_category = self.topics[language][selected_category]
        selected_topic = random.choice(topics_in_category)

        return selected_topic, selected_category

    def generate_article(self, topic: str, language: str, category: str = None) -> Optional[str]:
        """Генерирует статью с учетом категории"""

        system_prompt = self.create_enhanced_system_prompt(language, category)

        if language == "ua":
            user_prompt = f"""Напиши детальну та захоплюючу статтю на тему: "{topic}"

Обов'язково включи:
- Цікавий вступ, який зацікавить читача
- Детальні технічні аспекти з конкретними параметрами
- Практичні поради у вигляді нумерованих списків
- Реальні приклади ситуацій та рішень
- Поради для початківців та досвідчених гравців
- Аспекти безпеки та правильного використання
- Висновок з ключовими тезами

Пиши професійно, але доступно. Використовуй підзаголовки для структурування."""
        else:
            user_prompt = f"""Напиши подробную и увлекательную статью на тему: "{topic}"

Обязательно включи:
- Интересное вступление, которое заинтересует читателя
- Подробные технические аспекты с конкретными параметрами
- Практические советы в виде нумерованных списков
- Реальные примеры ситуаций и решений
- Советы для новичков и опытных игроков
- Аспекты безопасности и правильного использования
- Заключение с ключевыми тезисами

Пиши профессионально, но доступно. Используй подзаголовки для структурирования."""

        return self.call_lm_studio_with_retry(system_prompt, user_prompt)

    def save_article_multiple_formats(self, metadata: ArticleMetadata, content: str) -> List[str]:
        """Сохраняет статью в нескольких форматах"""

        saved_files = []

        try:
            # Создаем папки
            articles_dir = Path(self.config["output"]["articles_dir"])
            articles_dir.mkdir(exist_ok=True)

            # Создаем имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = re.sub(r'[^\w\s-]', '', metadata.title)[:50]
            safe_title = re.sub(r'[-\s]+', '_', safe_title)

            base_filename = f"{timestamp}_{metadata.language}_{safe_title}"

            for format_type in self.config["output"]["formats"]:
                if format_type == "txt":
                    filepath = articles_dir / f"{base_filename}.txt"
                    self._save_txt_format(filepath, metadata, content)
                    saved_files.append(str(filepath))
                    logging.info(f"✓ Сохранен TXT файл: {filepath}")

                elif format_type == "markdown":
                    filepath = articles_dir / f"{base_filename}.md"
                    self._save_markdown_format(filepath, metadata, content)
                    saved_files.append(str(filepath))
                    logging.info(f"✓ Сохранен MD файл: {filepath}")

        except Exception as e:
            logging.error(f"Ошибка при сохранении файлов: {e}")

        return saved_files

    def _save_txt_format(self, filepath: Path, metadata: ArticleMetadata, content: str):
        """Сохраняет в текстовом формате"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("МЕТАДАННЫЕ\n")
                f.write("=" * 60 + "\n")
                f.write(json.dumps(asdict(metadata), ensure_ascii=False, indent=2))
                f.write("\n\n")
                f.write("=" * 60 + "\n")
                f.write("СТАТЬЯ\n")
                f.write("=" * 60 + "\n")
                f.write(content)
        except Exception as e:
            logging.error(f"Ошибка сохранения TXT файла {filepath}: {e}")
            raise

    def _save_markdown_format(self, filepath: Path, metadata: ArticleMetadata, content: str):
        """Сохраняет в формате Markdown"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"---\n")
                f.write(f"title: {metadata.title}\n")
                f.write(f"language: {metadata.language}\n")
                f.write(f"category: {metadata.category}\n")
                f.write(f"created_at: {metadata.created_at}\n")
                f.write(f"word_count: {metadata.word_count}\n")
                f.write(f"readability_score: {metadata.readability_score}\n")
                f.write(f"keywords: {', '.join(metadata.keywords)}\n")
                f.write(f"---\n\n")
                f.write(content)
        except Exception as e:
            logging.error(f"Ошибка сохранения Markdown файла {filepath}: {e}")
            raise

    def test_connection(self) -> bool:
        """Тестирует подключение к LM Studio"""
        try:
            test_payload = {
                "model": self.config["lm_studio"]["model"],
                "messages": [
                    {"role": "user", "content": "Тест"}
                ],
                "max_tokens": 10
            }

            response = requests.post(
                self.config["lm_studio"]["url"],
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            logging.error(f"Ошибка тестирования подключения: {e}")
            return False

    def generate_daily_articles(self) -> Dict[str, List[str]]:
        """Генерирует статьи на одну тему на разных языках"""

        results = {"ua": [], "ru": []}

        # Создаем мапинг тем между языками
        topic_mapping = self.create_topic_mapping()

        # Выбираем одну тему на украинском
        ua_topic, ua_category = self.select_topic_by_category("ua")
        if not ua_topic or not ua_category:
            logging.error("Не удалось выбрать тему на украинском")
            return results

        # Находим соответствующую тему на русском
        ru_topic = topic_mapping.get(ua_topic)
        if not ru_topic:
            logging.error(f"Не найден перевод для темы: {ua_topic}")
            return results

        # Определяем категорию на русском
        ru_category = self.get_russian_category(ua_category)

        logging.info(f"Выбранная тема: UA='{ua_topic}' / RU='{ru_topic}'")
        logging.info(f"Категории: UA='{ua_category}' / RU='{ru_category}'")

        # Генерируем статьи на обоих языках
        for language in ["ua", "ru"]:
            topic = ua_topic if language == "ua" else ru_topic
            category = ua_category if language == "ua" else ru_category

            logging.info(f"Генерация статьи на {language}: {topic}")

            article_content = self.generate_article(topic, language, category)

            if article_content:
                # Проверяем качество
                is_valid, validation_errors, quality_metrics = self.quality_checker.comprehensive_check(
                    article_content, language
                )

                logging.info(f"Проверка качества для {language}: валидация={'пройдена' if is_valid else 'НЕ пройдена'}")
                if validation_errors:
                    logging.warning(f"Ошибки валидации: {validation_errors}")

                # Сохраняем статью
                metadata = ArticleMetadata(
                    title=topic,
                    language=language,
                    category=category,
                    created_at=datetime.now().isoformat(),
                    word_count=len(article_content.split()),
                    readability_score=quality_metrics.get("readability", 0.0),
                    keywords=quality_metrics.get("keywords", []),
                    validation_passed=is_valid
                )

                saved_files = self.save_article_multiple_formats(metadata, article_content)
                results[language] = saved_files

                if is_valid:
                    logging.info(f"✓ Статья {language} сохранена и прошла валидацию: {len(saved_files)} файлов")
                else:
                    logging.warning(f"⚠ Статья {language} сохранена, но НЕ прошла валидацию: {len(saved_files)} файлов")

            else:
                logging.error(f"✗ Не удалось сгенерировать статью для {language}")

        return results

    def create_topic_mapping(self) -> Dict[str, str]:
        """Создает мапинг тем между украинским и русским языками"""

        mapping = {
            # Категория: обладнання / снаряжение
            "Вибір тактичного жилета для страйкболу": "Выбор тактического жилета для страйкбола",
            "Захисне спорядження для новачків": "Защитное снаряжение для новичков",
            "Модернізація газових приводів": "Модернизация газовых приводов",
            "Вибір оптичного прицілу": "Выбор оптического прицела",
            "Догляд за акумуляторами LiPo": "Уход за аккумуляторами LiPo",
            "Системи розвантаження та носіння спорядження": "Системы разгрузки и ношения снаряжения",
            "Вибір правильного шолема та захисту голови": "Выбор правильного шлема и защиты головы",

            # Категория: технічне / техническое
            "Налаштування hop-up в електроприводах": "Настройка hop-up в электроприводах",
            "Тюнінг внутрішніх деталей приводу": "Тюнинг внутренних деталей привода",
            "Діагностика несправностей приводів": "Диагностика неисправностей приводов",
            "Модернізація ствола та резинки hop-up": "Модернизация ствола и резинки hop-up",
            "Налаштування регулятора тиску в HPA системах": "Настройка регулятора давления в HPA системах",

            # Категория: тактика / тактика
            "Тактика ведення бою в CQB": "Тактика ведения боя в CQB",
            "Камуфляж для лісових ігор": "Камуфляж для лесных игр",
            "Снайперська стрільба в страйкболі": "Снайперская стрельба в страйкболе",
            "Командна робота та зв'язок": "Командная работа и связь",
            "Позиціонування та переміщення в команді": "Позиционирование и перемещение в команде",
            "Планування та виконання тактичних операцій": "Планирование и выполнение тактических операций"
        }

        return mapping

    def get_russian_category(self, ua_category: str) -> str:
        """Переводит категорию с украинского на русский"""

        category_mapping = {
            "обладнання": "снаряжение",
            "технічне": "техническое",
            "тактика": "тактика"
        }

        return category_mapping.get(ua_category, ua_category)

class ArticleQualityChecker:
    """Расширенная проверка качества статей с более мягкими критериями"""

    def __init__(self):
        self.forbidden_words = [
            "пейнтбол", "paintball", "7.62", "5.56", "краска", "paint"
        ]

        self.required_elements = {
            "ua": ["страйкбол", "6мм"],  # Упрощенные требования
            "ru": ["страйкбол", "6мм"]
        }

        # Убираем проверку брендов - это может быть слишком строго
        self.brand_keywords = []

    def comprehensive_check(self, content: str, language: str) -> Tuple[bool, List[str], Dict]:
        """Комплексная проверка качества статьи с более мягкими критериями"""

        errors = []
        quality_metrics = {}

        # Базовые проверки
        if len(content) < 300:  # Снижаем минимальный лимит
            errors.append("Статья слишком короткая")

        # Проверка на запрещенные слова
        content_lower = content.lower()
        for word in self.forbidden_words:
            if word.lower() in content_lower:
                errors.append(f"Найдено запрещенное слово: {word}")

        # Упрощенная проверка обязательных элементов
        required = self.required_elements.get(language, [])
        missing_elements = []
        for element in required:
            if element.lower() not in content_lower:
                missing_elements.append(element)

        if missing_elements:
            errors.append(f"Отсутствуют обязательные элементы: {', '.join(missing_elements)}")

        # Анализ качества
        quality_metrics.update(self._analyze_readability(content, language))
        quality_metrics.update(self._extract_keywords(content, language))
        quality_metrics.update(self._check_structure(content))

        # Более мягкие критерии качества
        is_valid = len(errors) == 0 and self._meets_quality_standards(quality_metrics)

        return is_valid, errors, quality_metrics

    def _analyze_readability(self, content: str, language: str) -> Dict:
        """Простой анализ читабельности"""
        sentences = content.count('.') + content.count('!') + content.count('?')
        words = len(content.split())

        if sentences == 0:
            return {"readability": 0.0, "avg_sentence_length": 0}

        avg_sentence_length = words / sentences
        readability_score = max(0, 10 - (avg_sentence_length / 3))  # Простая формула

        return {
            "readability": round(readability_score, 1),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "total_sentences": sentences
        }

    def _extract_keywords(self, content: str, language: str) -> Dict:
        """Извлечение ключевых слов"""
        airsoft_keywords = {
            "ua": ["страйкбол", "привод", "тактичний", "захист", "розвантаження", "hop-up", "акумулятор"],
            "ru": ["страйкбол", "привод", "тактический", "защита", "разгрузка", "hop-up", "аккумулятор"]
        }

        found_keywords = []
        keywords_to_check = airsoft_keywords.get(language, [])
        content_lower = content.lower()

        for keyword in keywords_to_check:
            if keyword.lower() in content_lower:
                found_keywords.append(keyword)

        return {"keywords": found_keywords, "keyword_density": len(found_keywords)}

    def _check_structure(self, content: str) -> Dict:
        """Проверка структуры статьи"""
        headers = content.count('#') + content.count('**')  # Простая проверка заголовков
        lists = content.count('1.') + content.count('-') + content.count('*')

        return {
            "has_structure": headers > 1,  # Более мягкие требования
            "has_lists": lists > 1,
            "estimated_headers": headers
        }

    def _meets_quality_standards(self, metrics: Dict) -> bool:
        """Проверяет соответствие стандартам качества - более мягкие критерии"""
        return (
                metrics.get("readability", 0) >= 3.0 and  # Снижен порог
                metrics.get("keyword_density", 0) >= 1 and  # Снижен порог
                metrics.get("estimated_headers", 0) >= 1  # Хотя бы один заголовок
        )

def main():
    """Главная функция с улучшенным интерфейсом"""

    print("🎯 Генератор статей о страйкболе v2.0")
    print("=" * 50)

    try:
        generator = ArticleGenerator()

        print("Выберите действие:")
        print("1. Сгенерировать статьи на сегодня")
        print("2. Сгенерировать статью по выбранной теме")
        print("3. Показать статистику тем")
        print("4. Тест подключения к LM Studio")
        print("5. Настройки")

        choice = input("\nВведите номер (1-5): ").strip()

        if choice == "1":
            print("\n🚀 Запуск генерации статей...")
            results = generator.generate_daily_articles()

            print("\n📊 Результаты:")
            for lang, files in results.items():
                if files:
                    print(f"✅ {lang.upper()}: сохранено {len(files)} файлов")
                    for file in files:
                        print(f"   📄 {file}")
                else:
                    print(f"❌ {lang.upper()}: статья не создана")

        elif choice == "2":
            # Интерактивный выбор темы
            print("\nВыберите язык:")
            print("1. Украинский")
            print("2. Русский")

            lang_choice = input("Введите номер: ").strip()
            language = "ua" if lang_choice == "1" else "ru"

            # Показываем категории
            categories = list(generator.topics[language].keys())
            print(f"\nКатегории для {language}:")
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat}")

            cat_choice = input("Выберите категорию: ").strip()

            try:
                selected_category = categories[int(cat_choice) - 1]
                topics = generator.topics[language][selected_category]

                print(f"\nТемы в категории '{selected_category}':")
                for i, topic in enumerate(topics, 1):
                    print(f"{i}. {topic}")

                topic_choice = input("Выберите тему: ").strip()
                selected_topic = topics[int(topic_choice) - 1]

                print(f"\n🚀 Генерация статьи: {selected_topic}")
                content = generator.generate_article(selected_topic, language, selected_category)

                if content:
                    print("✅ Статья сгенерирована успешно!")
                    # Сохранение и проверка качества...

            except (ValueError, IndexError):
                print("❌ Неверный выбор")

        elif choice == "4":
            # Тест подключения
            test_passed = generator.test_connection()
            if test_passed:
                print("✅ Подключение к LM Studio работает!")
            else:
                print("❌ Проблемы с подключением к LM Studio")

        else:
            print("🤔 Функция в разработке...")

    except KeyboardInterrupt:
        print("\n\n👋 Работа прервана пользователем")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        print(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()