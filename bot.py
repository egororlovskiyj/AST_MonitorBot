import os
import json
import asyncio
from datetime import datetime, timedelta
import pytz
import aiohttp

from config import BOT_TOKEN, CHAT_ID, TIMEZONE
from monitor import check_account
from report import build_report
from db import init_db, update_cache, get_cache


# ---------------------- Telegram Sender ----------------------

async def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, data={"chat_id": CHAT_ID, "text": text})


# ---------------------- Manual report (/отчет) ----------------------

async def telegram_poll():
    """
    Long polling — слушаем команды от пользователя.
    """
    print("[telegram] Command listener started...")
    last_update_id = None

    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            if last_update_id:
                url += f"?offset={last_update_id + 1}"

            async with aiohttp.ClientSession() as session:
                r = await session.get(url)
                data = await r.json()

            if "result" in data:
                for upd in data["result"]:
                    last_update_id = upd["update_id"]

                    if "message" in upd:
                        text = upd["message"].get("text", "").lower()

                        if text == "/отчет" or text == "отчет":
                            await send_message("⏳ Готовлю отчёт...")
                            await run_report()
                            await send_message("✔️ Отчёт отправлен!")

        except Exception as e:
            print("[telegram] Polling error:", e)

        await asyncio.sleep(2)


# ---------------------- Daily report ----------------------

async def run_report():
    await init_db()

    with open("accounts.json", "r") as f:
        accounts = json.load(f)

    results = {}

    warnings = []  # аккаунты нарушители

    for country, lst in accounts.items():
        results[country] = []

        for user in lst:
            username, story, reels, post = await check_account(user)
            await update_cache(username, reels, post, story)
            results[country].append((username, story, reels, post))

            # --- проверка нарушений ---
            if not story and not reels and not post:
                row = await get_cache(username)
                if row:
                    misses = 0
                    if row["last_post_date"] is None:
                        misses += 1
                    if row["last_reels_date"] is None:
                        misses += 1
                    if not row["has_story"]:
                        misses += 1

                    if misses >= 3:
                        warnings.append(f"⚠️ {username} — {misses} дней без контента")

    # --- отправляем регулярный отчёт ---
    text = build_report(results)
    await send_message(text)

    # --- отправляем отчёт о нарушителях ---
    if warnings:
        warn_text = "🚨 Аккаунты с проблемами:\n\n" + "\n".join(warnings)
        await send_message(warn_text)


# ---------------------- Daily Scheduler ----------------------

async def scheduler():
    print("[scheduler] Worker started. Waiting for daily report...")

    tz = pytz.timezone(TIMEZONE)
    TARGET_HOUR = 21
    TARGET_MINUTE = 0

    while True:
        now = datetime.now(tz)
        target = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE,
                             second=0, microsecond=0)

        if now > target:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()

        print(f"[scheduler] Next run at {target}. Waiting {int(wait_seconds)} sec")

        await asyncio.sleep(wait_seconds)

        try:
            await run_report()
        except Exception as e:
            await send_message(f"⚠️ Ошибка генерации отчёта: {e}")

        await asyncio.sleep(60)


# ---------------------- Main run ----------------------

if __name__ == "__main__":
    asyncio.get_event_loop().create_task(telegram_poll())
    asyncio.get_event_loop().run_until_complete(scheduler())
