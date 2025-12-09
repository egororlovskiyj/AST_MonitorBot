# config.py
import os

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # id канала/чата для авто-отчётов

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# RapidAPI
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "instagram-scraper-stable-api.p.rapidapi.com")

# Часовой пояс для отчёта (по умолчанию твой GMT+2)
REPORT_TZ_OFFSET = 2  # часы
REPORT_HOUR = 21      # во сколько делать авто-отчёт



