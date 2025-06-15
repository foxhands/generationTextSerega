import logging
from src.config.settings import Config
from src.core.article_generator import ArticleGenerator


def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('article_generator.log'),
            logging.StreamHandler()
        ]
    )

    try:
        # Инициализация конфигурации
        config = Config()

        # Создание генератора статей
        generator = ArticleGenerator(config)

        # Генерация статей
        results = generator.generate_daily_articles()

        # Вывод результатов
        logging.info("=== Результаты генерации статей ===")
        logging.info(f"Успешно сгенерировано: {len(results['success'])} статей")
        for file in results['success']:
            logging.info(f"✓ {file}")

        if results['failed']:
            logging.warning(f"Не удалось сгенерировать: {len(results['failed'])} статей")
            for topic in results['failed']:
                logging.warning(f"✗ {topic}")

    except Exception as e:
        logging.error(f"Произошла ошибка: {e}", exc_info=True)


if __name__ == "__main__":
    main()
