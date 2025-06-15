from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid
import os

@dataclass
class ArticleMetadata:
    """Метаданные статьи"""
    title: str
    language: str
    category: str
    created_at: datetime = field(default_factory=datetime.now)
    word_count: int = 0
    readability_score: float = 0.0
    keywords: List[str] = field(default_factory=list)
    validation_passed: bool = False
    html_report: str = ""
    article_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование метаданных в словарь"""
        return {
            "title": self.title,
            "language": self.language,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "word_count": self.word_count,
            "readability_score": self.readability_score,
            "keywords": self.keywords,
            "validation_passed": self.validation_passed,
            "article_id": self.article_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArticleMetadata':
        """Создание метаданных из словаря"""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return cls(
            title=data.get("title", ""),
            language=data.get("language", ""),
            category=data.get("category", ""),
            created_at=created_at,
            word_count=data.get("word_count", 0),
            readability_score=data.get("readability_score", 0.0),
            keywords=data.get("keywords", []),
            validation_passed=data.get("validation_passed", False),
            html_report=data.get("html_report", ""),
            article_id=data.get("article_id", str(uuid.uuid4()))
        )

class Article:
    """Класс, представляющий статью"""
    
    def __init__(self, content: str, metadata: ArticleMetadata):
        self.content = content
        self.metadata = metadata
        if metadata.word_count == 0:
            self.metadata.word_count = len(content.split())

    def to_text(self) -> str:
        """Возвращает статью в текстовом формате"""
        return self._format_txt()

    def to_markdown(self) -> str:
        """Возвращает статью в markdown формате"""
        return self._format_markdown()
        
    def to_html(self) -> str:
        """Возвращает статью в HTML формате"""
        # Простое преобразование markdown в HTML
        html_content = self.content.replace("# ", "<h1>").replace("\n\n", "</h1>\n<p>")
        html_content = html_content.replace("\n\n", "</p>\n<p>")
        html_content = html_content.replace("## ", "</p>\n<h2>").replace("\n\n", "</h2>\n<p>")
        
        # Добавляем метаинформацию
        html = f"""<!DOCTYPE html>
<html lang="{self.metadata.language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.metadata.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #444; margin-top: 25px; }}
        p {{ margin-bottom: 16px; }}
        .metadata {{ background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="metadata">
        <p><strong>Язык:</strong> {self.metadata.language}</p>
        <p><strong>Категория:</strong> {self.metadata.category}</p>
        <p><strong>Дата создания:</strong> {self.metadata.created_at.strftime('%d.%m.%Y %H:%M')}</p>
        <p><strong>Количество слов:</strong> {self.metadata.word_count}</p>
        <p><strong>Оценка читабельности:</strong> {self.metadata.readability_score:.1f}</p>
        <p><strong>Ключевые слова:</strong> {', '.join(self.metadata.keywords)}</p>
    </div>

    {html_content}</p>
</body>
</html>"""
        return html

    def _format_txt(self) -> str:
        """Форматирует статью в текстовый формат"""
        return f"""Заголовок: {self.metadata.title}
Язык: {self.metadata.language}
Категория: {self.metadata.category}
Дата создания: {self.metadata.created_at.strftime('%d.%m.%Y %H:%M')}
Количество слов: {self.metadata.word_count}
Оценка читабельности: {self.metadata.readability_score:.1f}
Ключевые слова: {', '.join(self.metadata.keywords)}

{self.content}"""

    def _format_markdown(self) -> str:
        """Форматирует статью в markdown формат"""
        return f"""# {self.metadata.title}

*Язык:* {self.metadata.language}  
*Категория:* {self.metadata.category}  
*Дата создания:* {self.metadata.created_at.strftime('%d.%m.%Y %H:%M')}  
*Количество слов:* {self.metadata.word_count}  
*Оценка читабельности:* {self.metadata.readability_score:.1f}  
*Ключевые слова:* {', '.join(self.metadata.keywords)}

{self.content}"""
    
    def get_formatted_content(self, format_type: str) -> str:
        """Получение контента в выбранном формате
        
        Args:
            format_type (str): Тип формата ('txt', 'markdown', 'html')
            
        Returns:
            str: Отформатированный контент
        """
        format_methods = {
            'txt': self.to_text,
            'text': self.to_text,
            'md': self.to_markdown,
            'markdown': self.to_markdown,
            'html': self.to_html,
        }
        
        if format_type.lower() in format_methods:
            return format_methods[format_type.lower()]()
        else:
            return self.to_text()  # По умолчанию возвращаем текст
            
    def save(self, output_dir: str = "articles", format_types: List[str] = None) -> Dict[str, str]:
        """Сохраняет статью в указанных форматах
        
        Args:
            output_dir (str): Директория для сохранения
            format_types (List[str], optional): Список форматов. По умолчанию ['txt', 'markdown', 'html'].
            
        Returns:
            Dict[str, str]: Словарь с путями к сохраненным файлам
        """
        if format_types is None:
            format_types = ['txt', 'markdown', 'html']
            
        # Создаем директорию, если её нет
        os.makedirs(output_dir, exist_ok=True)
        
        # Формируем базовое имя файла
        base_filename = f"{self.metadata.title.replace(' ', '_')}_{self.metadata.language}_{self.metadata.created_at.strftime('%Y%m%d_%H%M%S')}"
        
        # Словарь для хранения путей к файлам
        saved_files = {}
        
        # Сохраняем в каждом формате
        for format_type in format_types:
            extension = format_type if format_type != 'markdown' else 'md'
            filename = f"{base_filename}.{extension}"
            filepath = os.path.join(output_dir, filename)
            
            content = self.get_formatted_content(format_type)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            saved_files[format_type] = filepath
            
        # Также сохраняем метаданные в JSON
        metadata_filename = f"{base_filename}_metadata.json"
        metadata_filepath = os.path.join(output_dir, metadata_filename)
        
        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metadata.to_dict(), f, ensure_ascii=False, indent=2)
            
        saved_files['metadata'] = metadata_filepath
        
        return saved_files
            
    @classmethod
    def load(cls, metadata_filepath: str) -> Optional['Article']:
        """Загружает статью из метаданных
        
        Args:
            metadata_filepath (str): Путь к файлу метаданных
            
        Returns:
            Optional[Article]: Загруженная статья или None в случае ошибки
        """
        try:
            # Загружаем метаданные
            with open(metadata_filepath, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
                
            metadata = ArticleMetadata.from_dict(metadata_dict)
            
            # Определяем возможные пути к файлам с контентом
            base_path = os.path.dirname(metadata_filepath)
            base_filename = os.path.basename(metadata_filepath).replace("_metadata.json", "")
            
            # Пробуем загрузить контент из различных форматов
            content = None
            for extension in ['md', 'txt', 'html']:
                content_filepath = os.path.join(base_path, f"{base_filename}.{extension}")
                if os.path.exists(content_filepath):
                    with open(content_filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    break
                    
            if content is None:
                return None
                
            # Создаем и возвращаем объект статьи
            return cls(content=content, metadata=metadata)
            
        except Exception as e:
            print(f"Ошибка загрузки статьи: {e}")
            return None 