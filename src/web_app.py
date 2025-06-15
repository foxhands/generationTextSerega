import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path

from src.config.config import Config
from src.core.article_generator import ArticleGenerator
from src.models.article import Article, ArticleMetadata

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8',
    handlers=[
        logging.FileHandler('src/web_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация приложения
app = Flask(__name__)
config = Config()
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
        
        # Формируем ответ
        response = {
            "success": True,
            "article": {
                "content": article.content,
                "metadata": article.metadata.to_dict(),
                "files": {
                    "txt": f"/download/{os.path.basename(article.metadata.article_id)}.txt",
                    "markdown": f"/download/{os.path.basename(article.metadata.article_id)}.md",
                    "html": f"/download/{os.path.basename(article.metadata.article_id)}.html"
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
        # Проверяем наличие файла в директории articles
        filepath = os.path.join(ARTICLES_DIR, filename)
        if os.path.exists(filepath):
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename
            )
        
        # Если не нашли, проверяем путь article_id
        article_id = os.path.splitext(filename)[0]
        extension = os.path.splitext(filename)[1]
        
        # Ищем все файлы в директории, которые содержат этот article_id
        for file in os.listdir(ARTICLES_DIR):
            if article_id in file and file.endswith(extension):
                filepath = os.path.join(ARTICLES_DIR, file)
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=filename
                )
                
        # Если не нашли файл
        logger.error(f"Файл не найден: {filename}")
        return jsonify({"error": "Файл не найден"}), 404
    except Exception as e:
        logger.error(f"Ошибка при скачивании файла: {str(e)}")
        return jsonify({"error": "Файл не найден"}), 404

@app.route('/api/check-connection')
def check_connection():
    """Проверка соединения с LM Studio"""
    from services.lm_service import LanguageModelService
    
    try:
        lm_service = LanguageModelService()
        is_connected = lm_service.test_connection()
        
        if is_connected:
            return jsonify({"status": "connected", "message": "Соединение с LM Studio установлено"})
        else:
            return jsonify({"status": "disconnected", "message": "Не удалось установить соединение с LM Studio"}), 503
    except Exception as e:
        logger.error(f"Ошибка при проверке соединения: {str(e)}")
        return jsonify({"status": "error", "message": f"Ошибка при проверке соединения: {str(e)}"}), 500

@app.route('/api/models')
def get_models():
    """Получение списка доступных моделей"""
    from services.lm_service import LanguageModelService
    
    try:
        lm_service = LanguageModelService()
        models = lm_service.get_supported_models()
        
        return jsonify({"models": models})
    except Exception as e:
        logger.error(f"Ошибка при получении списка моделей: {str(e)}")
        return jsonify({"error": f"Ошибка при получении списка моделей: {str(e)}"}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Страница не найдена"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Внутренняя ошибка сервера"}), 500

if __name__ == '__main__':
    # Проверяем и создаем директорию для статей
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    
    # Получаем конфигурацию для веб-сервера
    web_host = config.get('web.host', '0.0.0.0')
    web_port = config.get('web.port', 5000)
    web_debug = config.get('web.debug', True)
    
    logger.info(f"Запуск веб-приложения на {web_host}:{web_port}, debug={web_debug}")
    app.run(host=web_host, port=web_port, debug=web_debug) 