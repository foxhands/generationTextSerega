import re
from typing import Dict, List, Tuple
import logging
import textstat
from dataclasses import dataclass
from .text_analyzer import TextAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Метрики качества статьи"""
    readability: float
    keyword_density: Dict[str, float]
    overused_words: List[str]
    errors: List[str]
    html_report: str

class ArticleQualityChecker:
    """Проверка качества статьи"""
    
    def __init__(self):
        """Инициализация проверки качества"""
        self.target_readability = 5.0  # Снижаем порог читабельности
        self.text_analyzer = TextAnalyzer()
        
    def comprehensive_check(self, article_text: str, is_html: bool = False) -> Tuple[bool, QualityMetrics]:
        """
        Комплексная проверка качества статьи
        
        Args:
            article_text: Текст статьи
            is_html: Флаг, указывающий что входной текст в формате HTML
            
        Returns:
            Tuple[bool, QualityMetrics]: (прошла ли проверку, метрики качества)
        """
        try:
            # Анализ текста
            analysis_result = self.text_analyzer.analyze_text(article_text, is_html)
            
            # Проверка читабельности
            if analysis_result.readability_score < self.target_readability:
                logger.warning(f"Низкая читабельность: {analysis_result.readability_score:.2f} < {self.target_readability}")
                return False, QualityMetrics(
                    readability=analysis_result.readability_score,
                    keyword_density=analysis_result.keyword_density,
                    overused_words=analysis_result.overused_words,
                    errors=["Низкая читабельность"],
                    html_report=analysis_result.html_report
                )
                
            # Проверка на переиспользование слов
            if analysis_result.overused_words:
                logger.warning(f"Найдены переиспользуемые слова: {len(analysis_result.overused_words)}")
                return False, QualityMetrics(
                    readability=analysis_result.readability_score,
                    keyword_density=analysis_result.keyword_density,
                    overused_words=analysis_result.overused_words,
                    errors=["Обнаружены переиспользуемые слова"],
                    html_report=analysis_result.html_report
                )
                
            return True, QualityMetrics(
                readability=analysis_result.readability_score,
                keyword_density=analysis_result.keyword_density,
                overused_words=analysis_result.overused_words,
                errors=[],
                html_report=analysis_result.html_report
            )
            
        except Exception as e:
            logger.error(f"Ошибка при проверке качества: {str(e)}")
            return False, QualityMetrics(
                readability=0.0,
                keyword_density={},
                overused_words=[],
                errors=[str(e)],
                html_report="<p>Ошибка при анализе текста</p>"
            )

    def _analyze_readability(self, content: str, language: str) -> Dict:
        """Анализирует читабельность текста"""
        # Разбиваем на предложения, учитывая различные знаки препинания
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        words = [w.strip() for w in content.split() if w.strip()]
        
        if not sentences or not words:
            return {
                "score": 0,
                "avg_sentence_length": 0,
                "avg_word_length": 0,
                "sentence_count": 0,
                "word_count": 0
            }
        
        # Считаем среднюю длину предложения
        avg_sentence_length = len(words) / len(sentences)
        
        # Считаем среднюю длину слова
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Считаем количество сложных слов (более 6 букв)
        complex_words = sum(1 for word in words if len(word) > 6)
        complex_word_ratio = complex_words / len(words)
        
        # Используем textstat для оценки читабельности
        try:
            # Flesch Reading Ease для русского текста
            flesch_score = textstat.flesch_reading_ease(content)
            # Нормализуем оценку в диапазон 0-10
            normalized_flesch = max(0, min(10, flesch_score / 10))
            
            # Дополнительные метрики
            sentence_score = max(0, 10 - (avg_sentence_length / 3))  # 10 баллов за короткие предложения
            word_score = max(0, 10 - (avg_word_length * 1.5))  # 10 баллов за короткие слова
            complexity_score = max(0, 10 - (complex_word_ratio * 50))  # 10 баллов за простые слова
            
            # Итоговая оценка - взвешенное среднее
            final_score = (normalized_flesch * 0.4 + sentence_score * 0.3 + word_score * 0.2 + complexity_score * 0.1)
            
        except Exception as e:
            logging.warning(f"Ошибка при использовании textstat: {e}")
            # Если textstat не сработал, используем нашу формулу
            sentence_score = max(0, 10 - (avg_sentence_length / 3))
            word_score = max(0, 10 - (avg_word_length * 1.5))
            complexity_score = max(0, 10 - (complex_word_ratio * 50))
            final_score = (sentence_score + word_score + complexity_score) / 3
        
        return {
            "score": final_score,
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length,
            "sentence_count": len(sentences),
            "word_count": len(words),
            "complex_word_ratio": complex_word_ratio,
            "sentence_score": sentence_score,
            "word_score": word_score,
            "complexity_score": complexity_score
        }

    def _extract_keywords(self, content: str, language: str) -> Dict:
        """Извлекает ключевые слова из текста"""
        # Удаляем знаки препинания и приводим к нижнему регистру
        clean_content = re.sub(r'[^\w\s]', '', content.lower())
        words = clean_content.split()
        
        # Игнорируем стоп-слова
        stop_words = {'и', 'в', 'на', 'с', 'по', 'для', 'не', 'что', 'это', 'от', 'до', 'при', 'к', 'а', 'но', 'или'}
        words = [word for word in words if len(word) > 3 and word not in stop_words]
        
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Сортируем слова по частоте
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "main_keywords": [word for word, freq in sorted_words[:5]],
            "word_frequencies": word_freq
        }

    def _check_structure(self, content: str) -> Dict:
        """Проверяет структуру статьи"""
        # Проверяем наличие заголовка (может быть с # или без)
        has_title = bool(re.search(r'^#\s+.+$', content, re.MULTILINE)) or bool(re.search(r'^[А-Я][^\n]+$', content, re.MULTILINE))
        
        # Проверяем наличие подзаголовков (может быть с ## или без)
        has_sections = len(re.findall(r'^##\s+.+$', content, re.MULTILINE)) >= 3 or len(re.findall(r'^[А-Я][^\n]+$', content, re.MULTILINE)) >= 4
        
        # Проверяем наличие заключения
        has_conclusion = bool(re.search(r'(?i)заключение|вывод|итог|подведем итоги', content))
        
        return {
            "has_proper_structure": all([has_title, has_sections, has_conclusion]),
            "has_title": has_title,
            "has_sections": has_sections,
            "has_conclusion": has_conclusion
        }

    def _meets_quality_standards(self, metrics: Dict) -> bool:
        """Проверяет соответствие стандартам качества"""
        return (
            metrics["readability"]["score"] >= self.target_readability and
            len(metrics["keywords"]["main_keywords"]) >= 3 and
            metrics["structure"]["has_proper_structure"]
        ) 