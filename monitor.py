from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ProxyBad, ChallengeRequired
import datetime
import os

PROXY_URL = os.getenv("IG_PROXY")  # socks5://user:pass@host:port
IG_LOGIN = os.getenv("IG_LOGIN")
IG_PASSWORD = os.getenv("IG_PASSWORD")


def login_client():
    cl = Client()
    if PROXY_URL:
        cl.set_proxy(PROXY_URL)

    cl.login(IG_LOGIN, IG_PASSWORD)
    return cl


def check_account(username):
    cl = login_client()

    user_id = cl.user_id_from_username(username)
    now = datetime.date.today()

    # --- Stories ---
    has_story = False
    try:
        stories = cl.user_stories(user_id)
        if stories:
            has_story = True
    except:
        pass

    # --- Posts/Reels ---
    posts_today = False
    reels_today = False

    try:
        medias = cl.user_medias(user_id, 10)
        for m in medias:
            ts = m.taken_at.date()
            if ts == now:
                if m.media_type == 2:  # video / reel
                    reels_today = True
                else:
                    posts_today = True
    except:
        pass

    return (username, has_story, reels_today, posts_today)

