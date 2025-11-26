import json
import asyncio
from datetime import datetime, timedelta

import aiohttp
import pytz

from config import BOT_TOKEN, CHAT_ID, TIMEZONE
from monitor import check_account
from report import build_report, build_inactive_alert
from db import init_db, save_result, get_inactive_users


# ------------- Telegram helper -------------

async def send_message(text: str):
    if not text:
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(
            url,
            data={"chat_id": CHAT_ID, "text": text},
        )


# ------------- Основной отчёт -------------

async def run_report():
    """
    1) Читает accounts.json
    2) Проверяет всех юзеров через Instagram Scraper Stable API
    3) Сохраняет результаты в БД
    4) Шлёт классический отчёт
    5) Шлёт отдельное уведомление, если кто-то 3 дня без контента
    """
    await init_db()

    with open("accounts.json", "r", encoding="utf-8") as f:
        accounts = json.load(f)

    results = {}

    # --- проверка всех аккаунтов ---
    for country, lst in accounts.items():
        results[country] = []

        for username in lst:
            username, has_story, reels, photo = await check_account(username)
            await save_result(username, has_story, reels, photo)
            results[country].append((username, has_story, reels, photo))

    # --- обычный отчёт ---
    text = build_report(results)
    await send_message(text)

    # --- алерт по 3 дням без контента ---
    inactive = await get_inactive_users(days=3)
    alert_text = build_inactive_alert(inactive, days=3)
    if alert_text:
        await send_message(alert_text)


# ------------- Планировщик на 21:00 -------------

async def scheduler():
    tz = pytz.timezone(TIMEZONE)
    TARGET_HOUR = 21
    TARGET_MINUTE = 0

    while True:
        now = datetime.now(tz)
        target = now.replace(
            hour=TARGET_HOUR,
            minute=TARGET_MINUTE,
            second=0,
            microsecond=0,
        )

        if now > target:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        print(f"[scheduler] Next report at: {target}")

        await asyncio.sleep(wait_seconds)

        try:
            await run_report()
        except Exception as e:
            print("ERROR while run_report:", e)

        # чтобы второй раз случайно сразу не запустилось
        await asyncio.sleep(60)


# ------------- Listener команд в Telegram -------------

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
        except Exception as e:
            print("[telegram] error:", e)
            await asyncio.sleep(5)
            continue

        if "result" in data:
            for upd in data["result"]:
                offset = upd["update_id"] + 1

                if "message" in upd:
                    msg = upd["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")

                    if chat_id == CHAT_ID and text:
                        lower = text.lower().strip()

                        if lower in ("отчет", "отчёт", "/report", "report"):
                            await send_message("Готовлю отчёт ⏳...")
                            try:
                                await run_report()
                            except Exception as e:
                                print("ERROR manual run_report:", e)
                                await send_message("Ошибка при формировании отчёта 😔")

        await asyncio.sleep(1)


# ------------- MAIN -------------

async def main():
    await asyncio.gather(
        scheduler(),
        telegram_listener()
    )


if __name__ == "__main__":
    asyncio.run(main())

