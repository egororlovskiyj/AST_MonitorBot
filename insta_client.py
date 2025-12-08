import asyncio
import aiohttp
from config import RAPIDAPI_KEY, RAPIDAPI_HOST

# Ограничиваем одновременные запросы
API_SEMAPHORE = asyncio.Semaphore(3)

# Таймаут между запросами
REQUEST_DELAY = 0.7

# URL конечной точки
API_URL = "https://instagram-scraper-api2.p.rapidapi.com/v1.1/posts"

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
}


async def make_request(session, payload):
    """Один запрос к API с лимитом, задержкой и повтором."""
    async with API_SEMAPHORE:
        await asyncio.sleep(REQUEST_DELAY)

        for attempt in range(3):  # ретраи
            try:
                async with session.post(API_URL, data=payload, headers=HEADERS, timeout=40) as resp:
                    data = await resp.json()

                    # API вернул ошибку
                    if "error" in data:
                        err = data["error"].lower()

                        if "rate_limited" in err or "forbidden" in err:
                            # ждём и повторяем
                            await asyncio.sleep(1.5)
                            continue

                        return None, err

                    return data, None

            except Exception as e:
                # повторяем в случае сетевой ошибки
                await asyncio.sleep(1.5)

        return None, "failed_after_retry"


async def fetch_user_data(username: str):
    """Возвращает (has_story, has_reels, has_photo, followers, banned, error)."""

    async with aiohttp.ClientSession() as session:
        # POSTS
        posts_payload = {
            "username_or_url": f"https://www.instagram.com/{username}/",
            "chunk_num": "1",
            "batch_size": "15"
        }

        posts_data, posts_err = await make_request(session, posts_payload)

        if posts_err and posts_err.startswith("forbidden"):
            return False, False, False, None, True, "forbidden_or_unauthorized"

        if posts_err:
            return False, False, False, None, False, f"posts:{posts_err}"

        if not posts_data or "items" not in posts_data:
            return False, False, False, None, False, "posts:no_items"

        has_photo = any(item.get("media_type") == 1 for item in posts_data["items"])
        has_reels = any(item.get("media_type") == 2 for item in posts_data["items"])
        followers = posts_data.get("user", {}).get("follower_count")

        # STORIES
        stories_payload = {
            "username_or_url": f"https://www.instagram.com/{username}/",
            "fetch_stories": "true"
        }

        stories_data, stories_err = await make_request(session, stories_payload)

        if stories_err and not stories_err.startswith("rate_limited"):
            return has_photo, has_reels, False, followers, False, f"stories:{stories_err}"

        has_story = False
        if stories_data and "items" in stories_data:
            has_story = len(stories_data["items"]) > 0

        return has_story, has_reels, has_photo, followers, False, None

