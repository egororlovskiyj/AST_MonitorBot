# monitor.py
import asyncio
import json
from pathlib import Path
from typing import Dict, List

from aiogram import Bot

from config import BOT_TOKEN, CHAT_ID
from db import init_db
from insta_client import InstagramClient
from instagram_checker import check_account, CheckResult
from report import build_daily_report


ACCOUNTS_FILE = Path(__file__).parent / "accounts.json"


def load_accounts() -> Dict[str, List[str]]:
    with ACCOUNTS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: list(v) for k, v in data.items()}


async def run_check_for_all() -> Dict[str, List[CheckResult]]:
    await init_db()
    accounts = load_accounts()

    client = InstagramClient()
    results_by_country: Dict[str, List[CheckResult]] = {}

    try:
        for country, users in accounts.items():
            country_results: List[CheckResult] = []
            for username in users:
                username = username.strip()
                if not username:
                    continue

                res = await check_account(client, username)
                country_results.append(res)

                # лёгкая пауза между аккаунтами
                await asyncio.sleep(0.5)

            results_by_country[country] = country_results
    finally:
        await client.aclose()

    return results_by_country


async def run_report() -> str:
    """
    Только собирает данные и возвращает текст отчёта.
    Её удобно вызывать и из расписания, и из команды бота.
    """
    results = await run_check_for_all()
    text = build_daily_report(results)
    return text


async def send_report_via_bot():
    """
    Автоматическая отправка в канал/чат (для scheduler’а).
    """
    text = await run_report()
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    try:
        await bot.send_message(CHAT_ID, text)
    finally:
        await bot.session.close()
