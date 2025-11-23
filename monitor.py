import aiohttp
import datetime

PROXY = {
    "http": "socks5://originalharmony271109:eWvTse@5y7uqt2ob5.cn.fxdx.in:15469",
    "https": "socks5://originalharmony271109:eWvTse@5y7uqt2ob5.cn.fxdx.in:15469"
}

async def fetch_json(username):
    url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"

    connector = aiohttp.ProxyConnector.from_url(PROXY["https"])

    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }) as r:
            if r.status != 200:
                return None
            try:
                return await r.json()
            except:
                return None


async def check_account(username):
    data = await fetch_json(username)
    if not data:
        return (username, False, False, False)

    now = datetime.datetime.utcnow().date()

    has_story = False
    reels_today = False
    posts_today = False

    try:
        edges = data["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]
        for item in edges:
            ts = datetime.datetime.fromtimestamp(
                item["node"]["taken_at_timestamp"]
            ).date()

            if ts == now:
                if item["node"]["is_video"]:
                    reels_today = True
                else:
                    posts_today = True
    except:
        pass

    # Если json содержит раздел stories → считаем что были stories
    if "story" in str(data).lower():
        has_story = True

    return (username, has_story, reels_today, posts_today)
