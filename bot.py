# bot.py
import os
import json
import time
import pytz
import requests
from datetime import datetime, timedelta

from config import BOT_TOKEN, CHAT_ID, TIMEZONE
from monitor import check_account
from report import build_report
from db import init_db, update_cache


# ================= Telegram Sender =================

def send_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("[Telegram] Error sending message:", e)


# ================= Report generator =================

def run_report():
    print("[report] Initializing DB...")
    try:
        # DB is async so we call it through event loop
        import asyncio
        asyncio.run(init_db())
    except:
        pass

    print("[report] Loading accounts.json...")
    with open("accounts.json", "r") as f:
        accounts = json.load(f)

    results = {}

    print("[report] Checking accounts...")
    for country, lst in accounts.items():
        results[country] = []
        for user in lst:
            username, story, reels, post = check_account(user)

            # update DB
            try:
                import asyncio
                asyncio.run(update_cache(username, reels, post, story))
            except:
                pass

            results[country].append((username, story, reels, post))

    print("[report] Building report...")
    text = build_report(results)

    print("[report] Sending telegram message...")
    send_message(text)
    print("[report] Report sent!")


# ================= Scheduler (24/7 worker) =================

def scheduler():
    tz = pytz.timezone(TIMEZONE)

    TARGET_HOUR = 21     # Kiev time
    TARGET_MINUTE = 0

    print("[scheduler] Worker started. Waiting for daily report...")

    while True:
        now = datetime.now(tz)

        target = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)

        # если уже прошло 21:00, переносим на завтра
        if now > target:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()

        print(f"[scheduler] Next run at {target}. Waiting {int(wait_seconds)} sec")
        time.sleep(wait_seconds)

        # запуск отчёта
        try:
            print("[scheduler] Running daily report...")
            run_report()
        except Exception as e:
            print("[scheduler] ERROR:", e)

        # защита от двойного запуска
        time.sleep(60)


# ================= Entry point =================

if __name__ == "__main__":
    scheduler()

