import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()


class Config:
    # Ключи API
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GENIUS_API_KEY = os.getenv('GENIUS_API_KEY')

    # Настройки Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # Настройки приложения
    DEFAULT_IMAGE_STYLE = os.getenv('DEFAULT_IMAGE_STYLE', 'digital art')
    IMAGE_SIZE = os.getenv('IMAGE_SIZE', '1024x1024')

    # Папки
    STATIC_FOLDER = 'static'
    UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'images')

    # Максимальный размер запроса
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    GENIUS_TIMEOUT = 10
    OPENAI_TIMEOUT = 30

    # Максимальное время выполнения задачи
    TASK_TIMEOUT = 300  # 5 минут