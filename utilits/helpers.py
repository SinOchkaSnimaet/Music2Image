import os
import json
import hashlib
from datetime import datetime


def generate_filename(artist, title, extension='png'):
    """Генерирует имя файла на основе артиста и названия"""
    # Создаем хэш
    base_string = f"{artist}_{title}_{datetime.now().timestamp()}"
    file_hash = hashlib.md5(base_string.encode()).hexdigest()[:12]

    # Очищаем имя файла от недопустимых символов
    safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()

    filename = f"{safe_artist}_{safe_title}_{file_hash}.{extension}"
    return filename.replace(' ', '_')


def save_json(data, filename):
    """Сохраняет данные в JSON файл"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filename):
    """Загружает данные из JSON файла"""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def format_time(seconds):
    """Форматирует время в читаемый вид"""
    if seconds < 60:
        return f"{seconds:.1f} сек"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} мин"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} час"


def clean_text(text, max_length=1000):
    """Очищает и обрезает текст"""
    if not text:
        return ""

    # Убираем лишние пробелы и переносы
    text = ' '.join(text.split())

    # Обрезаем если слишком длинный
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text