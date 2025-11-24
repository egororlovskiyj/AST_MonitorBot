import asyncio
import aiohttp
from datetime import datetime, timedelta

BASE_URL = "https://www.instagram.com/{username}/?__a=1&__d=dis"


async def fetch_json(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers={
                "User-Agent": "Mozilla/5.0"
            }) as resp:
                return await resp.json()
        except:
            return None


async def check_account(username: str):
    url = BASE_URL.format(username=username)

    data = await fetch_json(url)

    if not data:
        print(f"[ERROR] Cannot load {username}")
        return username, False, False, False

    try:
        user = data["graphql"]["user"]
    except:
        print(f"[ERROR] JSON changed for {username}")
        return username, False, False, False

    # stories
    has_story = user.get("has_public_story", False)

    # posts
    today = datetime.utcnow().date()
    reels_today = False
    posts_today = False

    edges = user["edge_owner_to_timeline_media"]["edges"]

    for e in edges:
        node = e["node"]
        ts = datetime.fromtimestamp(node["taken_at_timestamp"]).date()

        if ts == today:
            if node["is_video"]:
                reels_today = True
            else:
                posts_today = True

    return username, has_story, reels_today, posts_today
