import os

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

# База данных (Postgres на Railway)
DATABASE_URL = os.getenv("DATABASE_URL")

# Часовой пояс для отчёта (можешь поменять при желании)
TIMEZONE = os.getenv("TIMEZONE", "Europe/Helsinki")

# RapidAPI – Instagram Scraper Stable API
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv(
    "RAPIDAPI_HOST",
    "instagram-scraper-stable-api.p.rapidapi.com"
)








