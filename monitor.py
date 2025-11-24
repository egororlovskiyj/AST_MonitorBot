import aiohttp
import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

async def fetch_user_data(username):
    url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as r:
            if r.status != 200:
                return None
            return await r.json()

async def check_account(username):
    try:
        data = await fetch_user_data(username)
        if not data:
            return username, False, False, False

        today = datetime.datetime.utcnow().date()

        # Проверка сториз через публичные данные
        has_story = "story" in str(data).lower()

        reels_today = False
        posts_today = False

        edges = data["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]

        for item in edges:
            node = item["node"]
            ts = datetime.datetime.fromtimestamp(node["taken_at_timestamp"]).date()

            if ts == today:
                if node["is_video"]:
                    reels_today = True
                else:
                    posts_today = True

        return username, has_story, reels_today, posts_today

    except Exception as e:
        print("Error:", e)
        return username, False, False, False



