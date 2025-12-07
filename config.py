# config.py
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID", "0"))

DATABASE_URL = os.getenv("DATABASE_URL")

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "instagram-scraper-stable-api.p.rapidapi.com")

# Базовый URL API
RAPIDAPI_BASE_URL = f"https://{RAPIDAPI_HOST}"

# Эндпоинты — проверь по RapidAPI и при необходимости поправь пути:
IG_USER_POSTS_PATH = "/get_ig_user_posts.php"
IG_USER_REELS_PATH = "/get_ig_user_reels.php"
IG_USER_STORIES_PATH = "/get_ig_user_stories.php"
IG_USER_INFO_PATH = "/ig_get_profile_data.php"   # ПРОВЕРЬ в доке, как у них называется профильный эндпоинт

# Часовой пояс для «сегодня» (Финляндия)
TIMEZONE = "Europe/Helsinki"

# Сколько часов считать «сегодняшним контентом»
HOURS_WINDOW = 24




