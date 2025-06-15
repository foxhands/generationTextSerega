import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path

from config.config import Config
from core.article_generator import ArticleGenerator
from core.category_manager import CategoryManager
from services.quality_checker import ArticleQualityChecker

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Константы
ARTICLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'articles')

# Инициализация генератора статей
article_generator = ArticleGenerator()

@app.route('/')
def index():
    """Главная страница"""
    try:
        # Получаем список категорий
        categories = article_generator.get_categories()
        # Преобразуем категории в список для шаблона
        categories_list = []
        for lang, cats in categories.items():
            for cat in cats:
                categories_list.append({
                    'id': cat,
                    'name': cat,
                    'language': lang
                })
        return render_template('index.html', categories=categories_list)
    except Exception as e:
        logger.error(f"Ошибка при загрузке главной страницы: {str(e)}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@app.route('/api/categories')
def get_categories():
    """API для получения списка категорий"""
    try:
        language = request.args.get('language', 'ru')
        categories = article_generator.get_categories()
        return jsonify({"categories": categories.get(language, [])})
    except Exception as e:
        logger.error(f"Ошибка при получении категорий: {str(e)}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@app.route('/api/topics')
def get_topics():
    """Получение списка тем для категории"""
    try:
        category = request.args.get('category')
        language = request.args.get('language', 'ru')
        
        logger.debug(f"Запрос тем для категории: {category}, язык: {language}")
        
        if not category:
            logger.error("Не указана категория")
            return jsonify({"error": "Не указана категория"}), 400
            
        topics = article_generator.get_topics(category)
        logger.debug(f"Получены темы: {topics}")
        
        if not topics:
            logger.error(f"Категория не найдена: {category}")
            return jsonify({"error": "Категория не найдена"}), 404
            
        # Возвращаем темы для указанного языка
        language_topics = topics.get(language, [])
        logger.debug(f"Темы для языка {language}: {language_topics}")
        return jsonify({"topics": language_topics})
    except Exception as e:
        logger.error(f"Ошибка при получении списка тем: {str(e)}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@app.route('/api/generate', methods=['POST'])
def generate_article():
    """Генерация статьи"""
    try:
        data = request.get_json()
        logger.debug(f"Получены данные для генерации: {json.dumps(data, ensure_ascii=False)}")
        
        if not data:
            logger.error("Не получены данные в запросе")
            return jsonify({"error": "Не получены данные"}), 400
            
        topic = data.get('topic')
        language = data.get('language', 'ru')
        category = data.get('category')
        
        logger.info(f"Параметры генерации: topic='{topic}', language='{language}', category='{category}'")
        
        if not all([topic, category]):
            logger.error(f"Не указаны все необходимые параметры: topic={topic}, category={category}")
            return jsonify({"error": "Не указаны все необходимые параметры"}), 400
            
        logger.info(f"Начинаем генерацию статьи на {language}")
        logger.info(f"Выбранная тема: {topic} (категория: {category})")
        
        # Генерация статьи
        article = article_generator.generate_article(topic, language, category)
        
        if not article:
            logger.error("Не удалось сгенерировать статью")
            return jsonify({"error": "Не удалось сгенерировать статью"}), 500
            
        # Сохранение статьи
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"article_{timestamp}"
        
        # Создаем директорию для статей, если её нет
        os.makedirs(ARTICLES_DIR, exist_ok=True)
        
        # Сохраняем в разных форматах
        txt_path = os.path.join(ARTICLES_DIR, f"{filename_base}.txt")
        md_path = os.path.join(ARTICLES_DIR, f"{filename_base}.md")
        html_path = os.path.join(ARTICLES_DIR, f"{filename_base}.html")
        
        logger.info(f"Сохраняем статью в файлы: {txt_path}, {md_path}, {html_path}")
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(article.to_text())
            
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(article.to_markdown())
            
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(article.metadata.html_report)
        
        logger.info(f"Статья успешно сгенерирована и сохранена")
        
        # Формируем ответ
        response = {
            "success": True,
            "article": {
                "content": article.content,
                "metadata": {
                    "title": article.metadata.title,
                    "language": article.metadata.language,
                    "category": article.metadata.category,
                    "created_at": article.metadata.created_at.isoformat(),
                    "word_count": article.metadata.word_count,
                    "readability_score": article.metadata.readability_score,
                    "keywords": article.metadata.keywords,
                    "validation_passed": article.metadata.validation_passed
                },
                "files": {
                    "txt": f"/download/{filename_base}.txt",
                    "markdown": f"/download/{filename_base}.md",
                    "html": f"/download/{filename_base}.html"
                }
            }
        }
        
        logger.debug(f"Отправляем ответ: {json.dumps(response, ensure_ascii=False)}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Ошибка при генерации статьи: {str(e)}", exc_info=True)
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Скачивание сгенерированного файла"""
    try:
        return send_file(
            os.path.join(ARTICLES_DIR, filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Ошибка при скачивании файла: {str(e)}")
        return jsonify({"error": "Файл не найден"}), 404

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Страница не найдена"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Внутренняя ошибка сервера"}), 500

if __name__ == '__main__':
    app.run(debug=True) 