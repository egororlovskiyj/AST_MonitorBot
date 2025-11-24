import os
import asyncio
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired

# Берём данные из Railway ENV
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
IG_PROXY = os.getenv("IG_PROXY")

cl = Client()


def login():
    cl.set_proxy(IG_PROXY)

    try:
        cl.load_settings("session.json")
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings("session.json")
        print("Login OK (session loaded)")
    except Exception:
        print("No session → logging normally")
        cl.set_proxy(IG_PROXY)
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings("session.json")
        print("New session saved")


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

    except Exception as e:
        print("Error:", e)
        return username, False, False, False

