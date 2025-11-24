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


# ------------------- Telegram Sender -------------------

async def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, data={"chat_id": CHAT_ID, "text": text})


# ------------------- Generate report -------------------

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


# ------------------- Daily Scheduler -------------------

async def scheduler():
    tz = pytz.timezone(TIMEZONE)
    TARGET_HOUR = 21
    TARGET_MINUTE = 0

    while True:
        now = datetime.now(tz)
        target = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)

        if now > target:
            target += timedelta(days=1)

        print(f"[scheduler] Next report at: {target}")
        await asyncio.sleep((target - now).total_seconds())

        try:
            await run_report()
        except Exception as e:
            print("ERROR:", e)

        await asyncio.sleep(60)


# ------------------- Command Listener -------------------

async def telegram_listener():
    print("[telegram] Listener started...")
    offset = None

    while True:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

        params = {"timeout": 20}
        if offset:
            params["offset"] = offset

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
        except:
            await asyncio.sleep(5)
            continue

        if "result" in data:
            for upd in data["result"]:
                offset = upd["update_id"] + 1

                if "message" in upd:
                    msg = upd["message"]
                    text = msg.get("text", "")

                    # Trigger by "отчет" OR "отчёт"
                    if text.lower() in ["отчет", "отчёт"]:
                        await send_message("Готовлю отчёт ⏳...")
                        await run_report()

        await asyncio.sleep(1)


# ------------------- MAIN -------------------

async def main():
    await asyncio.gather(
        scheduler(),
        telegram_listener()
    )


if __name__ == "__main__":
    asyncio.run(main())

