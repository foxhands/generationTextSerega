from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

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
    html_report: str = ""  # Добавляем поле для HTML-отчета

class Article:
    def __init__(self, content: str, metadata: ArticleMetadata):
        self.content = content
        self.metadata = metadata

    def to_text(self) -> str:
        """Возвращает статью в текстовом формате"""
        return self._format_txt()

    def to_markdown(self) -> str:
        """Возвращает статью в markdown формате"""
        return self._format_markdown()

    def _format_txt(self) -> str:
        """Форматирует статью в текстовый формат"""
        return f"""Заголовок: {self.metadata.title}
Язык: {self.metadata.language}
Категория: {self.metadata.category}
Дата создания: {self.metadata.created_at}
Количество слов: {self.metadata.word_count}
Оценка читабельности: {self.metadata.readability_score}
Ключевые слова: {', '.join(self.metadata.keywords)}

{self.content}"""

    def _format_markdown(self) -> str:
        """Форматирует статью в markdown формат"""
        return f"""# {self.metadata.title}

*Язык:* {self.metadata.language}  
*Категория:* {self.metadata.category}  
*Дата создания:* {self.metadata.created_at}  
*Количество слов:* {self.metadata.word_count}  
*Оценка читабельности:* {self.metadata.readability_score}  
*Ключевые слова:* {', '.join(self.metadata.keywords)}

{self.content}""" 