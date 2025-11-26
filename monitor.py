import aiohttp
from datetime import datetime
from config import RAPIDAPI_KEY, RAPIDAPI_HOST

# Базовый URL RapidAPI
BASE_URL = "https://instagram-scraper-stable-api.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST,
}


async def fetch(endpoint: str, payload: dict):
    """
    Универсальный запрос к Instagram Scraper Stable API.
    endpoint: например "/posts" или "/stories".
    """
    url = BASE_URL + endpoint

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=HEADERS) as resp:
                if resp.status != 200:
                    print(f"[ERROR] {endpoint} — HTTP {resp.status}")
                    return None
                return await resp.json()
        except Exception as e:
            print(f"[ERROR] Exception in {endpoint}: {e}")
            return None


async def check_account(username: str):
    """
    Возвращает:
    (username, has_story, reels_today, photo_today)
    """

    # ----------- 1) STORIES -----------
    stories_json = await fetch("/stories", {"username": username})
    has_story = False

    if stories_json:
        items = (
            stories_json.get("data")
            or stories_json.get("items")
            or []
        )
        has_story = len(items) > 0

    # ----------- 2) POSTS / REELS -----------
    posts_json = await fetch("/posts", {"username": username, "count": 20})

    reels_today = False
    photo_today = False

    if posts_json:
        items = posts_json.get("data") or posts_json.get("items") or []
        today = datetime.utcnow().date()

        for item in items:
            ts = (
                item.get("taken_at")
                or item.get("timestamp")
                or item.get("taken_at_timestamp")
            )

            if not ts:
                continue

            # Обрабатываем Unix timestamp или ISO-строку
            try:
                if isinstance(ts, (int, float)):
                    dt = datetime.utcfromtimestamp(ts)
                else:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                continue

            if dt.date() != today:
                continue

            # Определяем тип медиа
            is_video = bool(item.get("is_video"))
            media_type = str(item.get("media_type") or "").lower()

            # reels = видео
            if "reel" in media_type or is_video:
                reels_today = True
            else:
                photo_today = True

    return username, has_story, reels_today, photo_today


# Поддержка старого интерфейса monitor_user()
async def monitor_user(username):
    return await check_account(username)
