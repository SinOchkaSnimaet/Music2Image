# openai_processor.py
import openai
from config import Config


class OpenAIProcessor:
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY

        # Настройка клиента для новой версии OpenAI API (>=1.0.0)
        self.client = openai.OpenAI(api_key=self.api_key)

        # Используем gpt-3.5-turbo вместо gpt-4
        self.chat_model = "gpt-4"  # Или "gpt-4", если у тебя есть доступ
        self.image_model = "dall-e-3"

    def analyze_lyrics(self, lyrics, artist, title):
        """Анализ текста песни и создание промпта для изображения"""
        try:
            system_prompt = """Ты - эксперт по анализу текстов песен и созданию художественных образов.
            Проанализируй текст песни и создай детальное описание для генерации изображения.

            В описании должны быть:
            1. Основная тема и настроение
            2. Ключевые символы и метафоры
            3. Цветовая палитра
            4. Стиль изображения (реализм, сюрреализм, абстракция и т.д.)
            5. Композиционные элементы

            Описание должно быть на русском языке."""

            user_prompt = f"""Песня: "{title}" исполнителя {artist}

            Текст песни:
            {lyrics[:3000]}  # Ограничиваем длину

            Проанализируй этот текст и создай детальное описание для изображения."""

            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            analysis = response.choices[0].message.content

            # Создаем промпт для DALL-E
            dalle_prompt = f"{analysis}\n\nСтиль: цифровое искусство, детализированное, высокое качество, 8k"

            return {
                'success': True,
                'analysis': analysis,
                'full_prompt': dalle_prompt
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка анализа текста: {str(e)}'
            }

    def generate_image(self, prompt):
        """Генерация изображения через DALL-E"""
        try:
            response = self.client.images.generate(
                model=self.image_model,
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )

            image_url = response.data[0].url

            # Сохраняем изображение локально
            import requests
            from datetime import datetime

            image_response = requests.get(image_url)
            filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = f"static/images/{filename}"

            with open(filepath, 'wb') as f:
                f.write(image_response.content)

            return {
                'success': True,
                'image_url': image_url,
                'local_path': f"/static/images/{filename}"
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка генерации изображения: {str(e)}'
            }