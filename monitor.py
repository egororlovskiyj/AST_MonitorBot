import asyncio
from instagram_checker import check_account
from db import save_result, get_prev_followers


async def monitor_user(username: str):
    data = await check_account(username)

    await save_result(
        username=username,
        has_story=data["has_story"],
        has_reels=data["has_reels"],
        has_photo=data["has_photo"],
        followers=data["followers"],
        banned=data["banned"],
        error=data["error"],
    )

    return data
