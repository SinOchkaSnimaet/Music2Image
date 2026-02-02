import requests
from config import Config


class GeniusHelper:
    """Класс для работы с Genius API"""

    def __init__(self):
        self.api_key = Config.GENIUS_API_KEY
        self.base_url = "https://api.genius.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "MusicToImage/1.0"
        }

    def search_song(self, artist, title):
        """
        Ищет песню на Genius и возвращает текст

        Args:
            artist (str): Исполнитель
            title (str): Название песни

        Returns:
            dict: Информация о песне и текст
        """
        try:
            # 1. Ищем песню
            search_query = f"{artist} {title}"
            search_url = f"{self.base_url}/search"
            params = {"q": search_query}

            response = requests.get(
                search_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            search_data = response.json()

            # 2. Находим наиболее релевантный результат
            song_hits = search_data.get("response", {}).get("hits", [])

            if not song_hits:
                return {"error": "Песня не найдена на Genius"}

            # Берем первую песню (наиболее релевантную)
            song_info = song_hits[0]["result"]
            song_id = song_info["id"]

            # 3. Получаем текст песни
            lyrics = self._get_lyrics(song_info["url"])

            if not lyrics:
                return {"error": "Не удалось получить текст песни"}

            # 4. Формируем результат
            return {
                "success": True,
                "artist": song_info["primary_artist"]["name"],
                "title": song_info["title"],
                "lyrics": lyrics,
                "genius_url": song_info["url"],
                "album_art": song_info.get("song_art_image_url", ""),
                "release_date": song_info.get("release_date_for_display", "")
            }

        except requests.exceptions.RequestException as e:
            return {"error": f"Ошибка сети: {str(e)}"}
        except Exception as e:
            return {"error": f"Неизвестная ошибка: {str(e)}"}

    def _get_lyrics(self, song_url):
        """
        Парсит текст песни со страницы Genius

        Args:
            song_url (str): URL страницы с текстом

        Returns:
            str: Текст песни
        """
        try:
            response = requests.get(song_url, timeout=10)
            response.raise_for_status()

            # Ищем текст в HTML (упрощенный парсинг)
            html = response.text

            # Грубый метод поиска текста
            # В реальном проекте лучше использовать BeautifulSoup
            import re

            # Ищем текст между тегами с lyrics
            lyrics_pattern = r'<div[^>]*data-lyrics-container="true"[^>]*>(.*?)</div>'
            lyrics_sections = re.findall(lyrics_pattern, html, re.DOTALL)

            if not lyrics_sections:
                return None

            # Собираем все секции
            full_lyrics = ""
            for section in lyrics_sections:
                # Очищаем HTML теги
                clean_section = re.sub(r'<[^>]+>', '', section)
                clean_section = re.sub(r'\[.*?\]', '', clean_section)  # Убираем [Припев]
                full_lyrics += clean_section.strip() + "\n\n"

            return full_lyrics.strip()

        except Exception:
            return None

    def get_popular_songs(self, artist, limit=5):
        """
        Получает популярные песни артиста

        Args:
            artist (str): Имя исполнителя
            limit (int): Количество песен

        Returns:
            list: Список популярных песен
        """
        try:
            search_url = f"{self.base_url}/search"
            params = {"q": artist}

            response = requests.get(
                search_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            hits = data.get("response", {}).get("hits", [])

            songs = []
            for hit in hits[:limit]:
                if hit["type"] == "song":
                    songs.append({
                        "title": hit["result"]["title"],
                        "artist": hit["result"]["primary_artist"]["name"],
                        "url": hit["result"]["url"],
                        "image": hit["result"].get("song_art_image_thumbnail_url", "")
                    })

            return songs

        except Exception as e:
            print(f"Ошибка получения популярных песен: {e}")
            return []