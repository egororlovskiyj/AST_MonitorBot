import os
import aiohttp
import asyncio
from datetime import datetime, timezone

RAPID_KEY = os.getenv("RAPIDAPI_KEY")
RAPID_HOST = os.getenv("RAPIDAPI_HOST")

HEADERS = {
    "x-rapidapi-key": RAPID_KEY,
    "x-rapidapi-host": RAPID_HOST,
    "content-type": "application/json"
}


async def call_api(endpoint, payload=None):
    url = f"https://{RAPID_HOST}/{endpoint}"
    await asyncio.sleep(0.4)  # анти-429 throttle

    async with aiohttp.ClientSession() as s:
        try:
            async with s.post(url, json=payload or {}, headers=HEADERS) as r:
                if r.status != 200:
                    print(f"[API ERROR] {endpoint} HTTP {r.status}")
                    return None
                return await r.json()
        except Exception as e:
            print("API exception:", e)
            return None


async def get_user_info(username):
    return await call_api("get_user_info", {"username": username})


async def get_user_posts(username):
    return await call_api("user_posts.php", {"username": username})


async def get_user_stories(username):
    return await call_api("user_stories.php", {"username": username})


async def check_account(username):
    # info → followers + ban status
    info = await get_user_info(username)
    if not info:
        return username, False, False, False, "blocked", None

    followers = info.get("follower_count", 0)
    is_private = info.get("is_private", False)
    is_blocked = info.get("is_blocked", False)
    status = "OK"

    if is_blocked or is_private:
        status = "restricted"

    # stories
    stories_json = await get_user_stories(username)
    has_story = bool(stories_json and stories_json.get("stories"))

    # posts / reels
    posts_json = await get_user_posts(username)
    reels_today = False
    photo_today = False

    today = datetime.now(timezone.utc).date()

    if posts_json and "items" in posts_json:
        for item in posts_json["items"]:
            ts = item.get("taken_at")
            if not ts:
                continue

            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
            if dt != today:
                continue

            if item.get("media_type") == 2:
                reels_today = True
            else:
                photo_today = True

    return username, has_story, reels_today, photo_today, status, followers

