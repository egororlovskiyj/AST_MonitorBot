import os
print("ENV TG_CHAT =", os.getenv("TG_CHAT"))
print("ENV BOT_TOKEN =", os.getenv("BOT_TOKEN"))
print("ENV DATABASE_URL =", os.getenv("DATABASE_URL"))
import json
import asyncio
from config import BOT_TOKEN, CHAT_ID
from monitor import check_account
from report import build_report
from db import init_db, update_cache
import aiohttp
import pytz
from datetime import datetime
import os

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

if __name__ == "__main__":
    asyncio.run(run_report())

