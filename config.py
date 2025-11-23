import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("TG_CHAT"))   # <-- фикс
DATABASE_URL = os.getenv("DATABASE_URL")
TIMEZONE = "Europe/Kiev"


