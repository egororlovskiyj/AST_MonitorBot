import json
import asyncio
from datetime import datetime, timedelta

import aiohttp
import pytz

from config import BOT_TOKEN, CHAT_ID, TIMEZONE
from monitor import check_account
from report import build_report, build_inactive_alert
from db import init_db, save_activity, save_followers, get_followers_diff, get_inactive_users


async def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, data={"chat_id": CHAT_ID, "text": text})


async def run_report():
    await init_db()

    with open("accounts.json", "r", encoding="utf-8") as f:
        accounts = json.load(f)

    results = {}

    for country, users in accounts.items():
        results[country] = []

        for username in users:
            u, story, reels, photo, status, followers = await check_account(username)

            await save_activity(u, story, reels, photo, status)
            await save_followers(u, followers)

            diff = await get_followers_diff(u)

            results[country].append(
                (u, story, reels, photo, status, diff)
            )

    report = build_report(results)
    await send_message(report)

    bad = await get_inactive_users(days=3)
    alert = build_inactive_alert(bad)
    if alert:
        await send_message(alert)


async def scheduler():
    tz = pytz.timezone(TIMEZONE)
    TARGET_HOUR = 21
    TARGET_MINUTE = 0

    while True:
        now = datetime.now(tz)
        target = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0)

        if now > target:
            target += timedelta(days=1)

        await asyncio.sleep((target - now).total_seconds())
        try:
            await run_report()
        except Exception as e:
            print("ERROR:", e)

        await asyncio.sleep(60)


async def listener():
    offset = None
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    while True:
        params = {"timeout": 25}
        if offset:
            params["offset"] = offset

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as r:
                    data = await r.json()
            except:
                await asyncio.sleep(3); continue

        if "result" in data:
            for upd in data["result"]:
                offset = upd["update_id"] + 1

                if "message" in upd:
                    msg = upd["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")

                    if text and text.lower().strip() in ("отчет", "отчёт", "report", "/report"):
                        await send_message("Готовлю отчёт…")
                        await run_report()

        await asyncio.sleep(1)


async def main():
    await asyncio.gather(scheduler(), listener())


if __name__ == "__main__":
    asyncio.run(main())

