import aiohttp
import datetime

async def fetch_json(username):
    url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as r:
            if r.status != 200:
                return None
            return await r.json()

async def check_account(username):
    data = await fetch_json(username)
    if not data:
        return (username, False, False, False)

    now = datetime.datetime.utcnow().date()

    # Stories (public endpoint alternative)
    # Мы проверяем stories через reel tabs (если сториз есть — data содержит story highlights)
    has_story = "story" in str(data).lower()

    # Posts + Reels
    reels_today = False
    posts_today = False

    try:
        edges = data["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]
        for item in edges:
            ts = datetime.datetime.fromtimestamp(item["node"]["taken_at_timestamp"]).date()
            if ts == now:
                if item["node"]["is_video"]:
                    reels_today = True
                else:
                    posts_today = True
    except:
        pass

    return (username, has_story, reels_today, posts_today)
