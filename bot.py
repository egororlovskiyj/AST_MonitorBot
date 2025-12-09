# bot.py
import json
import asyncio
from datetime import datetime, timedelta

import aiohttp
import pytz

from config import BOT_TOKEN, CHAT_ID
from monitor import monitor_user
from report import build_report, build_inactive_alert
from db import init_db, save_result, get_prev_followers, get_inactive_users

from datetime import datetime, timedelta

from config import REPORT_TZ_OFFSET, REPORT_HOUR


# ---------- Telegram helper ----------

async def send_message(text: str):
    if not text:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, data={"chat_id": CHAT_ID, "text": text})


# ---------- Основной отчёт ----------

async def run_report():
    """
    1) Читает accounts.json
    2) По каждому аккаунту вызывает monitor_user / check_account
    3) Сохраняет результат в БД (с фолловерами, баном, ошибкой)
    4) Шлёт отчёт
    5) Шлёт алерт по 3 дням без контента
    """
    await init_db()

    with open("accounts.json", "r", encoding="utf-8") as f:
        accounts = json.load(f)   # {"Finland": ["user1", "user2"], ...}

    results: dict[str, list[dict]] = {}

    for country, names in accounts.items():
        country_list = []
        results[country] = country_list

        for username in names:
            (
                username,
                has_story,
                has_reels,
                has_photo,
                followers,
                banned,
                error,
            ) = await monitor_user(username)

            prev_followers = await get_prev_followers(username)
            followers_diff = None
            if followers is not None and prev_followers is not None:
                followers_diff = followers - prev_followers

            await save_result(
                username,
                has_story,
                has_reels,
                has_photo,
                followers,
                banned,
                error,
            )

            country_list.append(
                {
                    "username": username,
                    "story": has_story,
                    "reels": has_reels,
                    "photo": has_photo,
                    "followers": followers,
                    "followers_diff": followers_diff,
                    "banned": banned,
                    "error": error,
                }
            )

            # маленькая пауза, чтобы не ловить 429
            await asyncio.sleep(0.2)

    text = build_report(results)
    await send_message(text)

    # алерт по неактивным
    inactive = await get_inactive_users(days=3)
    alert = build_inactive_alert(inactive, days=3)
    if alert:
        await send_message(alert)


# ---------- Планировщик 21:00 ----------

async def scheduler():
    TARGET_HOUR = 21
    TARGET_MINUTE = 0

    while True:
        now = datetime.now(TZ)
        target = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        print(f"[scheduler] Next report at: {target}")
        await asyncio.sleep(wait_seconds)

        try:
            await run_report()
        except Exception as e:
            print("[scheduler] ERROR in run_report:", e)

        # защита от повторного мгновенного запуска
        await asyncio.sleep(60)


# ---------- Telegram listener для команд ----------

_last_manual_run_at: datetime | None = None


async def telegram_listener():
    global _last_manual_run_at
    print("[telegram] Listener started...")
    offset = None

    while True:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {"timeout": 25}
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

        if "result" not in data:
            await asyncio.sleep(1)
            continue

        for upd in data["result"]:
            offset = upd["update_id"] + 1

            msg = upd.get("message") or upd.get("channel_post")
            if not msg:
                continue

            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")

            if chat_id != CHAT_ID or not text:
                continue

            lower = text.lower().strip()
            if lower in ("отчет", "отчёт", "/report", "report"):
                # анти-спам: не чаще раза в минуту
                now = datetime.now(TZ)
                if _last_manual_run_at and (now - _last_manual_run_at).total_seconds() < 60:
                    print("[telegram] manual report ignored (cooldown)")
                    continue

                _last_manual_run_at = now
                await send_message("Готовлю отчёт ⏳...")

                try:
                    await run_report()
                except Exception as e:
                    print("[telegram] ERROR manual run_report:", e)
                    await send_message("Ошибка при формировании отчёта 😔")

        await asyncio.sleep(1)


# ---------- MAIN ----------

async def main():
    await asyncio.gather(
        scheduler(),
        telegram_listener(),
    )


if __name__ == "__main__":
    asyncio.run(main())

