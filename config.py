import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("TG_CHAT"))
DATABASE_URL = os.getenv("DATABASE_URL")  # PostgreSQL URL от Railway
TIMEZONE = "Europe/Kiev"

