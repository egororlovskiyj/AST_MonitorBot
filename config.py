import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

TIMEZONE = os.getenv("TIMEZONE", "Europe/Helsinki")

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "instagram-scraper-stable-api.p.rapidapi.com")







