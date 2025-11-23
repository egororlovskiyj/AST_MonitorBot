import asyncio
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from proxy_config import PROXY

IG_USERNAME = "error_dixon"
IG_PASSWORD = "1226"

# глобальный клиент чтобы не логиниться на каждый запрос
cl = Client()


async def login():
    if not cl.user_id:
        try:
            print("Logging into Instagram...")
            cl.set_proxy(PROXY)
            cl.login(IG_USERNAME, IG_PASSWORD)
            print("Login success!")
        except ChallengeRequired:
            print("ChallengeRequired — Instagram blocked login")
        except LoginRequired:
            print("LoginRequired — bad login")
        except Exception as e:
            print("Login error:", e)


async def check_account(username: str):
    try:
        await login()
        cl.set_proxy(PROXY)

        user_id = cl.user_id_from_username(username)
        feed = cl.user_medias(user_id, 20)

        has_story = bool(cl.user_stories(user_id))

        reels_today = False
        posts_today = False

        from datetime import datetime
        today = datetime.utcnow().date()

        for m in feed:
            ts = m.taken_at.date()
            if ts == today:
                if m.media_type == 2:
                    reels_today = True
                else:
                    posts_today = True

        return username, has_story, reels_today, posts_today

    except Exception as e:
        print(f"Error checking {username}: {e}")
        return username, False, False, False

