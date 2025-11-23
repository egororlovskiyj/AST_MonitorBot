import os
import json
import asyncio
from datetime import datetime, timedelta
import pytz
import aiohttp

from config import BOT_TOKEN, CHAT_ID, TIMEZONE
from monitor import check_account
from report import build_report
from db import init_db, update_cache


# ============ Telegram Sender ============

async def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, data={"chat_id": CHAT_ID, "text": text})


# ============ Generate daily report ============

async def run_report():
    await init_db()

    with open("accounts.json", "r") as f:
        accounts = json.load(f)

    results = {}

    for country, lst in accounts.items():
        results[country] = []
        for user in lst:
            username, story, reels, post = await check_account(user)
            await update_cache(username, reels, post, story)
            results[country].append((username, story, reels, post))

    text = build_report(results)
    await send_message(text)


# ============ Daily scheduler (24/7 worker) ============

async def scheduler():
    """
    Работает 24/7.
    Ждёт каждый день 21:00 по Киеву и запускает отчёт.
    """

    tz = pytz.timezone(TIMEZONE)
    TARGET_HOUR = 21
    TARGET_MINUTE = 0

    while True:
        now = datetime.now(tz)

        target = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)

        if now > target:
            # если текущее время уже позже 21:00 — переносим на завтра
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()

        print(f"[scheduler] Next report at: {target} | waiting {wait_seconds} seconds")

        await asyncio.sleep(wait_seconds)

        # запускаем отчёт
        try:
            print("[scheduler] Running daily report...")
            await run_report()
            print("[scheduler] Report sent.")
        except Exception as e:
            print(f"[scheduler] ERROR: {e}")

        # ждём минуту, чтобы случайно не повторить отчёт
        await asyncio.sleep(60)


# ============ Entry point ============
if __name__ == "__main__":
    asyncio.run(scheduler())
    
