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


async def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, data={"chat_id": CHAT_ID, "text": text})


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


async def scheduler():
    tz = pytz.timezone(TIMEZONE)
    TARGET_HOUR = 21
    TARGET_MINUTE = 0

    while True:
        now = datetime.now(tz)
        target = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0)

        if now > target:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        print(f"[scheduler] Next report at: {target}")

        await asyncio.sleep(wait_seconds)

        try:
            await run_report()
        except Exception as e:
            print("ERROR:", e)

        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(scheduler())

