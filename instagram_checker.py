# instagram_checker.py
import asyncio
import json
from pathlib import Path
from typing import Dict, List

from insta_client import fetch_user_activity
from db import save_result


ACCOUNTS_FILE = Path(__file__).with_name("accounts.json")


async def check_all_accounts():
    # читаем список моделей по странам
    with ACCOUNTS_FILE.open("r", encoding="utf-8") as f:
        accounts_by_country: Dict[str, List[str]] = json.load(f)

    # идём строго по очереди, без gather, чтобы не ловить rate_limit
    for country, usernames in accounts_by_country.items():
        for username in usernames:
            # получаем статус по юзеру
            data = await fetch_user_activity(username)

            await save_result(
                username=username,
                has_story=data["has_story"],
                has_reels=data["has_reels"],
                has_photo=data["has_photo"],
                followers=data["followers"],
                banned=data["banned"],
                error=data["error"],
            )

            # небольшая пауза между запросами,
            # чтобы точно не упираться в лимиты RapidAPI
            await asyncio.sleep(1.0)


if __name__ == "__main__":
    asyncio.run(check_all_accounts())
