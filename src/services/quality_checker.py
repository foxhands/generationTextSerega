import re
import logging
from typing import Dict, List, Tuple, Any, Set
from collections import Counter
import textstat

logger = logging.getLogger(__name__)

class ArticleQualityChecker:
    """Класс для проверки качества сгенерированных статей"""
    
    def __init__(self):
        """Инициализация проверщика качества"""
        self.min_word_count = 500
        self.min_readability = 5.0
        self.min_headings = 3
        self.min_paragraphs = 5
        self.language_stop_words = {
            'ru': set(['и', 'в', 'на', 'с', 'по', 'для', 'от', 'к', 'за', 'из', 'о', 'что', 'как', 'это']),
            'ua': set(['і', 'в', 'на', 'з', 'по', 'для', 'від', 'до', 'за', 'із', 'про', 'що', 'як', 'це'])
        }
        logger.info("Инициализация ArticleQualityChecker завершена")
        
    def comprehensive_check(self, content: str, language: str = 'ru') -> Tuple[bool, Dict[str, Any]]:
        """Комплексная проверка качества статьи
        
        Args:
            content (str): Текст статьи
            language (str, optional): Язык статьи ('ru' или 'ua'). По умолчанию 'ru'.
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (результат проверки, метрики качества)
        """
        try:
            # Собираем все результаты анализа
            metrics = {}
            error_messages = []
            
            # Базовый анализ структуры и содержания
            structure_metrics = self._analyze_structure(content)
            metrics.update(structure_metrics)
            
            # Проверка длины статьи
            word_count = structure_metrics.get('word_count', 0)
            if word_count < self.min_word_count:
                error_messages.append(f"Статья слишком короткая: {word_count} слов (минимум {self.min_word_count})")
            metrics['has_sufficient_length'] = word_count >= self.min_word_count
            
            # Анализ читабельности
            readability_metrics = self._analyze_readability(content, language)
            metrics.update(readability_metrics)
            
            readability_score = readability_metrics.get('readability_score', 0)
            if readability_score < self.min_readability:
                error_messages.append(f"Низкий показатель читабельности: {readability_score:.1f} (минимум {self.min_readability})")
            metrics['has_good_readability'] = readability_score >= self.min_readability
            
            # Извлечение ключевых слов
            keyword_metrics = self._extract_keywords(content, language)
            metrics.update(keyword_metrics)
            
            # Проверка структуры
            if metrics.get('headings_count', 0) < self.min_headings:
                error_messages.append(f"Недостаточно заголовков: {metrics.get('headings_count', 0)} (минимум {self.min_headings})")
            metrics['has_good_structure'] = metrics.get('headings_count', 0) >= self.min_headings
            
            if metrics.get('paragraphs_count', 0) < self.min_paragraphs:
                error_messages.append(f"Недостаточно параграфов: {metrics.get('paragraphs_count', 0)} (минимум {self.min_paragraphs})")
            metrics['has_enough_paragraphs'] = metrics.get('paragraphs_count', 0) >= self.min_paragraphs
            
            # Генерация HTML-отчета
            metrics['html_report'] = self._generate_html_report(content, metrics)
            metrics['errors'] = error_messages
            
            # Итоговое решение о качестве
            passed = all([
                metrics.get('has_sufficient_length', False),
                metrics.get('has_good_readability', False),
                metrics.get('has_good_structure', False),
                metrics.get('has_enough_paragraphs', False)
            ])
            
            if passed:
                logger.info(f"Статья прошла проверку качества. Метрики: {metrics}")
            else:
                logger.warning(f"Статья не прошла проверку качества: {error_messages}")
            
            return passed, metrics
            
        except Exception as e:
            logger.error(f"Ошибка при проверке качества статьи: {str(e)}", exc_info=True)
            return False, {"errors": [f"Ошибка анализа: {str(e)}"]}
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """Анализ структуры текста
        
        Args:
            content (str): Текст статьи
            
        Returns:
            Dict[str, Any]: Метрики структуры
        """
        result = {}
        
        # Количество слов
        words = re.findall(r'\b\w+\b', content.lower())
        result['word_count'] = len(words)
        
        # Количество предложений
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        result['sentence_count'] = len(sentences)
        
        # Средняя длина предложения
        if result['sentence_count'] > 0:
            result['avg_sentence_length'] = result['word_count'] / result['sentence_count']
        else:
            result['avg_sentence_length'] = 0
            
        # Количество параграфов
        paragraphs = content.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        result['paragraphs_count'] = len(paragraphs)
        
        # Количество заголовков
        headings = re.findall(r'^#+\s+.+$', content, re.MULTILINE)
        result['headings_count'] = len(headings)
        
        # Выделенный текст
        bold_text = re.findall(r'\*\*.+?\*\*', content)
        result['bold_count'] = len(bold_text)
        
        # Списки
        list_items = re.findall(r'^[-*]\s+.+$', content, re.MULTILINE)
        result['list_item_count'] = len(list_items)
        
        return result
        
    def _analyze_readability(self, content: str, language: str) -> Dict[str, Any]:
        """Анализ читабельности текста
        
        Args:
            content (str): Текст статьи
            language (str): Язык статьи
            
        Returns:
            Dict[str, Any]: Метрики читабельности
        """
        result = {}
        
        try:
            # Настраиваем textstat в зависимости от языка
            if language == 'ru':
                textstat.set_lang('ru')
            elif language == 'ua':
                textstat.set_lang('uk')  # Украинский в textstat
            else:
                textstat.set_lang('ru')  # По умолчанию используем русский
                
            # Получаем различные метрики читабельности
            flesch_score = textstat.flesch_reading_ease(content)
            result['readability_score'] = flesch_score
            
            # Сложность чтения
            if flesch_score >= 80:
                result['readability_level'] = 'Очень легко читаемый'
            elif flesch_score >= 70:
                result['readability_level'] = 'Легко читаемый'
            elif flesch_score >= 60:
                result['readability_level'] = 'Средней сложности'
            elif flesch_score >= 50:
                result['readability_level'] = 'Умеренно сложный'
            else:
                result['readability_level'] = 'Сложный для чтения'
                
            # Дополнительные метрики, если доступны для языка
            try:
                result['smog_index'] = textstat.smog_index(content)
            except:
                result['smog_index'] = 0
                
            try:
                result['syllable_count'] = textstat.syllable_count(content)
            except:
                result['syllable_count'] = 0
                
        except Exception as e:
            logger.error(f"Ошибка при анализе читабельности: {str(e)}")
            result['readability_score'] = 0
            result['readability_level'] = 'Не удалось определить'
            
        return result
        
    def _extract_keywords(self, content: str, language: str) -> Dict[str, Any]:
        """Извлечение ключевых слов из текста
        
        Args:
            content (str): Текст статьи
            language (str): Язык статьи
            
        Returns:
            Dict[str, Any]: Метрики ключевых слов
        """
        result = {}
        
        try:
            # Получаем стоп-слова для указанного языка
            stop_words = self.language_stop_words.get(language, set())
            
            # Приводим текст к нижнему регистру и разделяем на слова
            words = re.findall(r'\b\w{3,}\b', content.lower())
            
            # Удаляем стоп-слова
            filtered_words = [word for word in words if word not in stop_words]
            
            # Подсчет частот слов
            word_counts = Counter(filtered_words)
            
            # Отбираем топ-20 наиболее часто встречающихся слов
            top_keywords = word_counts.most_common(20)
            
            # Создаем словарь частот для наиболее частых слов
            keyword_density = {word: count / len(filtered_words) for word, count in top_keywords}
            
            result['keywords'] = [word for word, _ in top_keywords]
            result['keyword_density'] = keyword_density
            result['keyword_count'] = len(result['keywords'])
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении ключевых слов: {str(e)}")
            result['keywords'] = []
            result['keyword_density'] = {}
            result['keyword_count'] = 0
            
        return result
        
    def _generate_html_report(self, content: str, metrics: Dict[str, Any]) -> str:
        """Генерация HTML-отчета о качестве статьи
        
        Args:
            content (str): Текст статьи
            metrics (Dict[str, Any]): Метрики качества
            
        Returns:
            str: HTML-отчет
        """
        # Форматирование отчета
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет о качестве статьи</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; color: #333; }}
        h1, h2, h3 {{ color: #444; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .metrics {{ display: flex; flex-wrap: wrap; margin: 20px 0; }}
        .metric-card {{ background: #f5f5f5; border-radius: 5px; padding: 15px; margin: 10px; flex: 1 1 200px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
        .good {{ color: green; }}
        .moderate {{ color: orange; }}
        .poor {{ color: red; }}
        .keyword-list {{ display: flex; flex-wrap: wrap; }}
        .keyword {{ background: #e9f7fe; padding: 5px 10px; margin: 5px; border-radius: 3px; }}
        .errors {{ background: #fff0f0; padding: 10px; border-left: 4px solid #ff6b6b; margin: 20px 0; }}
        .summary {{ background: #f9f9f9; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        
        @media (max-width: 600px) {{
            .metric-card {{ flex: 1 1 100%; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Отчет о качестве статьи</h1>
        
        <div class="summary">
            <h2>Общая оценка</h2>
            <p>Статья """
        
        # Добавляем общее заключение о качестве
        if all([
            metrics.get('has_sufficient_length', False),
            metrics.get('has_good_readability', False),
            metrics.get('has_good_structure', False)
        ]):
            html += '<span class="good">соответствует всем критериям качества</span>.'
        elif not metrics.get('has_sufficient_length', False):
            html += '<span class="poor">слишком короткая</span>.'
        elif not metrics.get('has_good_readability', False):
            html += '<span class="poor">сложна для чтения</span>.'
        elif not metrics.get('has_good_structure', False):
            html += '<span class="poor">имеет недостаточную структуру</span>.'
        else:
            html += '<span class="moderate">требует улучшения</span>.'
        
        html += """</p>
        </div>
        
        <h2>Основные метрики</h2>
        <div class="metrics">
            <div class="metric-card">
                <h3>Количество слов</h3>
                <div class="metric-value"""
                
        # Цвет для количества слов
        word_count = metrics.get('word_count', 0)
        if word_count >= self.min_word_count:
            html += ' good'
        else:
            html += ' poor'
            
        html += f'"{word_count}</div>'
        html += f'<p>Минимум: {self.min_word_count}</p>'
        html += '</div>'
        
        # Метрика читабельности
        html += """
            <div class="metric-card">
                <h3>Читабельность</h3>
                <div class="metric-value"""
                
        readability = metrics.get('readability_score', 0)
        if readability >= self.min_readability:
            html += ' good'
        else:
            html += ' poor'
            
        html += f'">{readability:.1f}</div>'
        html += f'<p>{metrics.get("readability_level", "Не определено")}</p>'
        html += '</div>'
        
        # Метрика структуры
        html += """
            <div class="metric-card">
                <h3>Структура</h3>
                <div class="metric-value"""
                
        headings = metrics.get('headings_count', 0)
        if headings >= self.min_headings:
            html += ' good'
        else:
            html += ' poor'
            
        html += f'">{headings}</div>'
        html += f'<p>Заголовков (минимум {self.min_headings})</p>'
        html += '</div>'
        
        # Метрика параграфов
        html += """
            <div class="metric-card">
                <h3>Параграфы</h3>
                <div class="metric-value"""
                
        paragraphs = metrics.get('paragraphs_count', 0)
        if paragraphs >= self.min_paragraphs:
            html += ' good'
        else:
            html += ' poor'
            
        html += f'">{paragraphs}</div>'
        html += f'<p>Параграфов (минимум {self.min_paragraphs})</p>'
        html += '</div>'
        
        # Закончим метрики
        html += """
        </div>
        
        <h2>Детальные метрики</h2>
        <div class="metrics">
            <div class="metric-card">
                <h3>Предложения</h3>
                <div class="metric-value">{}</div>
                <p>Средняя длина: {:.1f} слов</p>
            </div>
            
            <div class="metric-card">
                <h3>Стилистические элементы</h3>
                <p>Выделенный текст: {}</p>
                <p>Элементы списков: {}</p>
            </div>
        </div>
        """.format(
            metrics.get('sentence_count', 0),
            metrics.get('avg_sentence_length', 0),
            metrics.get('bold_count', 0),
            metrics.get('list_item_count', 0)
        )
        
        # Добавляем ключевые слова
        html += """
        <h2>Ключевые слова</h2>
        <div class="keyword-list">
        """
        
        for keyword in metrics.get('keywords', [])[:15]:
            html += f'<span class="keyword">{keyword}</span>'
            
        html += """
        </div>
        """
        
        # Добавляем ошибки, если они есть
        errors = metrics.get('errors', [])
        if errors:
            html += """
            <h2>Выявленные проблемы</h2>
            <div class="errors">
                <ul>
            """
            
            for error in errors:
                html += f'<li>{error}</li>'
                
            html += """
                </ul>
            </div>
            """
            
        # Завершаем HTML
        html += """
    </div>
</body>
</html>"""
        
        return html 