import aiohttp
import datetime
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# прокси берём из Railway
PROXY = os.getenv("IG_PROXY")   # socks5://user:pass@host:port


async def fetch_json(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, proxy=PROXY) as r:
                if r.status != 200:
                    print("HTTP ERROR", r.status, url)
                    return None

                try:
                    return await r.json()
                except:
                    text = await r.text()
                    print("JSON decode error:", text[:150])
                    return None
    except Exception as e:
        print("Request error:", e)
        return None


async def check_account(username: str):
    url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
    data = await fetch_json(url)

    if not data:
        return username, False, False, False

    user = data.get("graphql", {}).get("user", {})
    feed = user.get("edge_owner_to_timeline_media", {}).get("edges", [])

    # stories
    stories_url = f"https://www.instagram.com/stories/{username}/?__a=1&__d=dis"
    stories_data = await fetch_json(stories_url)
    has_story = False

    if stories_data and "reel" in stories_data and stories_data["reel"].get("items"):
        has_story = True

    today = datetime.datetime.utcnow().date()

    reels_today = False
    posts_today = False

    for item in feed:
        node = item.get("node", {})
        ts = node.get("taken_at_timestamp")
        if not ts:
            continue

        post_date = datetime.datetime.utcfromtimestamp(ts).date()

        if post_date == today:
            if node.get("is_video", False):
                reels_today = True
            else:
                posts_today = True

    return username, has_story, reels_today, posts_today


