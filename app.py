from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
from genius_helper import GeniusHelper
from openai_processor import OpenAIProcessor
import uuid
import time
import json
import os

# Инициализация приложения
app = Flask(__name__)
app.config.from_object(Config)

# Создаем папки
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Инициализация помощников
genius = GeniusHelper()
openai_processor = OpenAIProcessor()

# Простое хранилище задач
tasks = {}


# Обработка favicon.ico
@app.route('/favicon.ico')
def favicon():
    return '', 200  # Возвращаем пустой ответ с кодом 200


# Маршруты
@app.route('/')
def index():
    """Главная страница с поиском"""
    return render_template('index.html')


# Страница обработки
@app.route('/processing')
def processing():
    """Страница отображения процесса обработки"""
    return render_template('processing.html')


@app.route('/search', methods=['POST'])
def search_song():
    """Поиск песни и начало обработки"""
    try:
        # Проверяем, что это JSON запрос
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type должен быть application/json'
            }), 415

        # Получаем данные
        data = request.get_json()
        artist = data.get('artist', '').strip()
        title = data.get('title', '').strip()

        if not artist or not title:
            return jsonify({
                'success': False,
                'error': 'Укажите исполнителя и название песни'
            }), 400

        # Создаем уникальный ID задачи
        task_id = str(uuid.uuid4())

        # Сохраняем задачу
        tasks[task_id] = {
            'id': task_id,
            'artist': artist,
            'title': title,
            'status': 'searching',
            'created_at': time.time(),
            'step': 'Поиск текста на Genius...',
            'progress': 10
        }

        # Запускаем обработку в фоне
        import threading
        thread = threading.Thread(
            target=process_song,
            args=(task_id, artist, title)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'redirect': url_for('processing_with_id', task_id=task_id)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ошибка сервера: {str(e)}'
        }), 500



# Изменяем эту функцию - убираем параметр по умолчанию для task_id
@app.route('/processing/<task_id>')
def processing_with_id(task_id):
    """Страница отображения процесса обработки с конкретной задачей"""
    if task_id not in tasks:
        return render_template('error.html',
                               error='Задача не найдена или устарела'), 404

    task = tasks[task_id]
    return render_template('processing.html', task=task)


@app.route('/result/<task_id>')
def result(task_id):
    """Страница с результатом"""
    if task_id not in tasks:
        return render_template('error.html',
                               error='Результат не найден'), 404

    task = tasks[task_id]

    if task['status'] != 'completed':
        # Если задача еще не завершена, перенаправляем на страницу обработки
        return redirect(url_for('processing_with_id', task_id=task_id))

    return render_template('result.html', result=task)


@app.route('/api/status/<task_id>')
def api_status(task_id):
    """API для проверки статуса задачи"""
    if task_id not in tasks:
        return jsonify({
            'success': False,
            'error': 'Задача не найдена'
        }), 404

    task = tasks[task_id].copy()

    # Убираем большие данные из ответа если они есть
    if 'lyrics' in task:
        task['lyrics_preview'] = task['lyrics'][:200] + '...' if len(task['lyrics']) > 200 else task['lyrics']
        del task['lyrics']

    return jsonify({
        'success': True,
        'task': task
    })


@app.route('/api/trending')
def trending_songs():
    """Получить популярные песни для примера"""
    try:
        # Пример популярных артистов
        artists = ['Taylor Swift', 'The Weeknd', 'Drake', 'Billie Eilish', 'Kanye West']
        import random
        artist = random.choice(artists)

        songs = genius.get_popular_songs(artist, limit=5)

        return jsonify({
            'success': True,
            'artist': artist,
            'songs': songs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Фоновая обработка
def process_song(task_id, artist, title):
    """Фоновая задача обработки песни"""
    task = tasks[task_id]

    try:
        # 1. Поиск текста на Genius
        task['step'] = 'Поиск текста на Genius...'
        task['progress'] = 20

        song_data = genius.search_song(artist, title)

        if 'error' in song_data:
            task['status'] = 'error'
            task['error'] = song_data['error']
            return

        # 2. Сохраняем данные песни
        task.update(song_data)
        task['step'] = 'Анализ текста с помощью AI...'
        task['progress'] = 40

        # 3. Анализ текста через OpenAI
        analysis_result = openai_processor.analyze_lyrics(
            song_data['lyrics'],
            artist,
            title
        )

        if not analysis_result.get('success'):
            task['status'] = 'error'
            task['error'] = analysis_result.get('error', 'Ошибка анализа текста')
            return

        # 4. Сохраняем анализ
        task['analysis'] = analysis_result['analysis']
        task['generated_prompt'] = analysis_result['full_prompt']
        task['step'] = 'Генерация изображения...'
        task['progress'] = 70

        # 5. Генерация изображения через DALL-E
        image_result = openai_processor.generate_image(
            analysis_result['full_prompt']
        )

        if not image_result.get('success'):
            task['status'] = 'error'
            task['error'] = image_result.get('error', 'Ошибка генерации изображения')
            return

        # 6. Сохраняем результат
        task['image_url'] = image_result['image_url']
        task['local_image'] = image_result['local_path']
        task['revised_prompt'] = image_result.get('revised_prompt', '')
        task['step'] = 'Готово!'
        task['progress'] = 100
        task['status'] = 'completed'
        task['completed_at'] = time.time()
        task['processing_time'] = task['completed_at'] - task['created_at']

        # Логируем успех
        print(f"Задача {task_id} завершена успешно!")

    except Exception as e:
        task['status'] = 'error'
        task['error'] = f'Критическая ошибка: {str(e)}'
        print(f"Ошибка в задаче {task_id}: {e}")


@app.route('/about')
def about():
    """В разработке" """
    return render_template('under_construction.html')


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Страница не найдена'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('error.html', error='Внутренняя ошибка сервера'), 500


if __name__ == '__main__':
    # Создаем папку для изображений
    os.makedirs('static/images', exist_ok=True)

    app.run(
        debug=Config.DEBUG,
        host='0.0.0.0',
        port=5000
    )