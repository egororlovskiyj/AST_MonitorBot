import aiohttp
from datetime import datetime

# Проверяем сторис, рилс и посты через публичные веб-endpoints Instagram

async def fetch_json(session, url):
    try:
        async with session.get(url, timeout=15) as resp:
            return await resp.json()
    except:
        return None


async def check_account(username: str):
    base = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"

    async with aiohttp.ClientSession(
        headers={
            "User-Agent": "Mozilla/5.0",
            "X-IG-App-ID": "936619743392459",
        }
    ) as session:

        data = await fetch_json(session, base)
        if not data or "data" not in data:
            print(f"[ERROR] Cannot load {username}")
            return username, False, False, False

        user = data["data"]["user"]

        # STORY
        has_story = user.get("has_public_story", False)

        # MEDIA
        media = user["edge_owner_to_timeline_media"]["edges"]
        reels_today = False
        posts_today = False

        today = datetime.utcnow().date()

        for item in media:
            node = item["node"]
            taken = datetime.fromtimestamp(node["taken_at_timestamp"]).date()

            if taken == today:
                if node["is_video"]:
                    reels_today = True
                else:
                    posts_today = True

        return username, has_story, reels_today, posts_today

