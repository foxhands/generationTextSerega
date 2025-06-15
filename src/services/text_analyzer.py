import re
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)

@dataclass
class TextAnalysisResult:
    """Результат анализа текста"""
    readability_score: float
    keyword_density: Dict[str, float]
    overused_words: List[str]
    html_report: str

class TextAnalyzer:
    """Анализатор текста"""
    
    def __init__(self):
        """Инициализация анализатора"""
        self.min_word_count = 300
        self.max_word_count = 2000
        self.target_readability = 5.0
        
    def analyze_text(self, text: str, is_html: bool = False) -> TextAnalysisResult:
        """
        Анализ текста
        
        Args:
            text: Текст для анализа
            is_html: Флаг, указывающий что входной текст в формате HTML
            
        Returns:
            TextAnalysisResult: Результат анализа
        """
        try:
            # Очистка текста от HTML если нужно
            if is_html:
                text = self._clean_html(text)
                
            # Базовые проверки
            words = text.split()
            if len(words) < self.min_word_count:
                return TextAnalysisResult(
                    readability_score=0.0,
                    keyword_density={},
                    overused_words=[],
                    html_report="<p>Текст слишком короткий</p>"
                )
                
            # Анализ читабельности
            readability_score = self._calculate_readability(text)
            
            # Анализ ключевых слов
            keyword_density = self._analyze_keywords(text)
            
            # Поиск переиспользуемых слов
            overused_words = self._find_overused_words(text)
            
            # Генерация HTML-отчета
            html_report = self._generate_html_report(
                readability_score,
                keyword_density,
                overused_words
            )
            
            return TextAnalysisResult(
                readability_score=readability_score,
                keyword_density=keyword_density,
                overused_words=overused_words,
                html_report=html_report
            )
            
        except Exception as e:
            logger.error(f"Ошибка при анализе текста: {str(e)}")
            return TextAnalysisResult(
                readability_score=0.0,
                keyword_density={},
                overused_words=[],
                html_report=f"<p>Ошибка при анализе текста: {str(e)}</p>"
            )
            
    def _clean_html(self, text: str) -> str:
        """Очистка текста от HTML-тегов"""
        return re.sub(r'<[^>]+>', '', text)
        
    def _calculate_readability(self, text: str) -> float:
        """Расчет читабельности текста"""
        try:
            # Разбиваем на предложения
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
            words = text.split()
            
            if not sentences or not words:
                return 0.0
                
            # Считаем среднюю длину предложения
            avg_sentence_length = len(words) / len(sentences)
            
            # Считаем среднюю длину слова
            avg_word_length = sum(len(word) for word in words) / len(words)
            
            # Считаем количество сложных слов (более 6 букв)
            complex_words = sum(1 for word in words if len(word) > 6)
            complex_word_ratio = complex_words / len(words)
            
            # Оценка читабельности - более мягкие критерии
            sentence_score = max(0, 10 - (avg_sentence_length / 5))  # Более мягкая оценка длины предложений
            word_score = max(0, 10 - (avg_word_length))  # Более мягкая оценка длины слов
            complexity_score = max(0, 10 - (complex_word_ratio * 30))  # Более мягкая оценка сложности
            
            # Итоговая оценка - взвешенное среднее с большим весом для простоты
            final_score = (sentence_score * 0.3 + word_score * 0.3 + complexity_score * 0.4)
            
            # Добавляем базовый балл за структуру
            if len(sentences) > 5:  # Если есть хотя бы 5 предложений
                final_score += 2.0
                
            return max(0, min(10, final_score))
            
        except Exception as e:
            logger.error(f"Ошибка при расчете читабельности: {str(e)}")
            return 0.0
            
    def _analyze_keywords(self, text: str) -> Dict[str, float]:
        """Анализ ключевых слов"""
        try:
            # Очистка текста
            clean_text = re.sub(r'[^\w\s]', '', text.lower())
            words = clean_text.split()
            
            # Подсчет частоты слов
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Игнорируем короткие слова
                    word_freq[word] = word_freq.get(word, 0) + 1
                    
            # Нормализация частот
            total_words = len(words)
            if total_words > 0:
                return {word: freq/total_words for word, freq in word_freq.items()}
            return {}
            
        except Exception as e:
            logger.error(f"Ошибка при анализе ключевых слов: {str(e)}")
            return {}
            
    def _find_overused_words(self, text: str) -> List[str]:
        """Поиск переиспользуемых слов"""
        try:
            # Очистка текста
            clean_text = re.sub(r'[^\w\s]', '', text.lower())
            words = clean_text.split()
            
            # Подсчет частоты слов
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Игнорируем короткие слова
                    word_freq[word] = word_freq.get(word, 0) + 1
                    
            # Поиск переиспользуемых слов (более 5% от общего количества)
            total_words = len(words)
            if total_words > 0:
                threshold = total_words * 0.05
                return [word for word, freq in word_freq.items() if freq > threshold]
            return []
            
        except Exception as e:
            logger.error(f"Ошибка при поиске переиспользуемых слов: {str(e)}")
            return []
            
    def _generate_html_report(self, readability: float, keywords: Dict[str, float], overused: List[str]) -> str:
        """Генерация HTML-отчета"""
        try:
            report = []
            report.append("<div class='quality-report'>")
            
            # Читабельность
            report.append("<h3>Читабельность</h3>")
            report.append(f"<p>Оценка: {readability:.2f}/10</p>")
            
            # Ключевые слова
            report.append("<h3>Ключевые слова</h3>")
            if keywords:
                report.append("<ul>")
                for word, density in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]:
                    report.append(f"<li>{word}: {density:.2%}</li>")
                report.append("</ul>")
            else:
                report.append("<p>Ключевые слова не найдены</p>")
                
            # Переиспользуемые слова
            if overused:
                report.append("<h3>Переиспользуемые слова</h3>")
                report.append("<ul>")
                for word in overused:
                    report.append(f"<li>{word}</li>")
                report.append("</ul>")
                
            report.append("</div>")
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Ошибка при генерации HTML-отчета: {str(e)}")
            return "<p>Ошибка при генерации отчета</p>" 