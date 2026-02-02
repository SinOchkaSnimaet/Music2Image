import openai
from transformers import pipeline
from config import Config


class PromptEngine:
    def __init__(self):
        self.use_openai = bool(Config.OPENAI_API_KEY)

        if self.use_openai:
            openai.api_key = Config.OPENAI_API_KEY
        else:
            # Локальные модели для анализа настроения
            try:
                self.sentiment = pipeline(
                    "text-classification",
                    model="seara/rubert-tiny2-russian-sentiment"
                )
            except:
                self.sentiment = None

    def create_prompt(self, lyrics, artist="", title=""):
        """Создает промпт для генерации изображения"""

        # Определяем основные темы и настроение
        themes = self._extract_themes(lyrics)
        mood = self._analyze_mood(lyrics)
        style = self._determine_style(artist, themes, mood)

        # Собираем промпт
        prompt_parts = []

        # Стиль изображения
        prompt_parts.append(f"{style} style")

        # Основная сцена на основе тем
        if themes:
            scene = ", ".join(themes[:3])
            prompt_parts.append(scene)

        # Детализация
        prompt_parts.append("highly detailed")
        prompt_parts.append("professional digital art")

        # Настроение
        prompt_parts.append(f"mood: {mood}")

        # Если есть артист, добавляем в стиль
        if artist:
            prompt_parts.append(f"inspired by {artist}")

        return ", ".join(prompt_parts)

    def _extract_themes(self, text):
        """Выделение ключевых тем (упрощённо)"""
        # Можно использовать TF-IDF или ключевые слова
        common_words = {'the', 'and', 'you', 'that', 'for', 'with', 'this', 'your'}
        words = [w.lower() for w in text.split() if w.isalpha() and w.lower() not in common_words]

        # Самые частые слова = темы
        from collections import Counter
        word_counts = Counter(words)
        return [word for word, _ in word_counts.most_common(5)]

    def _analyze_mood(self, text):
        """Анализ настроения текста"""
        if self.use_openai:
            # Используем GPT для анализа
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system",
                     "content": "Определи одним словом настроение этого текста песни. Только одно слово на русском: радостное, грустное, гневное, меланхоличное, энергичное, спокойное, романтичное, бунтарское."},
                    {"role": "user", "content": text[:1000]}
                ]
            )
            return response.choices[0].message.content
        elif self.sentiment:
            # Локальный анализ
            result = self.sentiment(text[:512])[0]
            label_map = {
                'positive': 'радостное',
                'negative': 'грустное',
                'neutral': 'спокойное'
            }
            return label_map.get(result['label'], 'спокойное')
        else:
            return 'загадочное'

    def _determine_style(self, artist, themes, mood):
        """Определение стиля изображения"""
        # Маппинг жанров на стили
        genre_hints = {
            'rock': 'dark fantasy, dramatic lighting',
            'pop': 'vibrant, colorful, pop art',
            'rap': 'urban, graffiti, street art',
            'electronic': 'cyberpunk, neon, futuristic',
            'indie': 'watercolor, dreamy, vintage',
            'classical': 'baroque painting, oil painting style'
        }

        # Маппинг настроений на стили
        mood_styles = {
            'радостное': 'bright, colorful, cheerful',
            'грустное': 'melancholic, blue tones, rainy',
            'гневное': 'chaotic, red tones, aggressive',
            'романтичное': 'soft, pastel colors, dreamy'
        }

        # Пробуем определить по артисту (можно расширить)
        artist_lower = artist.lower()
        for genre, style in genre_hints.items():
            if genre in artist_lower:
                return style

        # Иначе по настроению
        return mood_styles.get(mood, 'digital art, fantasy')