import asyncio
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from proxy_config import PROXY

IG_USERNAME = "nordic_smm_egor"
IG_PASSWORD = "ASTalent25!"

cl = Client()


def login():
    try:
        cl.set_proxy(PROXY)
        cl.load_settings("session.json")   # ← пробуем загрузить прошлую сессию
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings("session.json")   # ← сохраняем новую сессию
        print("Login OK (session loaded)")
    except Exception:
        print("Session not found → logging normally")
        cl.set_proxy(PROXY)
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings("session.json")
        print("Login saved")


async def check_account(username: str):
    try:
        login()

        user_id = cl.user_id_from_username(username)
        feed = cl.user_medias(user_id, 30)

        stories = cl.user_stories(user_id)
        has_story = bool(stories)

        from datetime import datetime
        today = datetime.utcnow().date()

        reels_today = False
        posts_today = False

        for m in feed:
            ts = m.taken_at.date()
            if ts == today:
                if m.media_type == 2:
                    reels_today = True
                else:
                    posts_today = True

        return username, has_story, reels_today, posts_today

    except Exception as e:
        print("Error:", e)
        return username, False, False, False
