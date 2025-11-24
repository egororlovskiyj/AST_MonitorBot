# monitor.py
from datetime import datetime
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from proxy_config import PROXY

IG_USERNAME = "error_dixon"
IG_PASSWORD = "1226"

cl = Client()


def login():
    """Выполняем единоразовый вход в Instagram"""
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


def check_account(username: str):
    """
    Синхронная проверка аккаунта.
    Возвращает: (username, has_story, reels_today, posts_today)
    """
    try:
        login()
        cl.set_proxy(PROXY)

        user_id = cl.user_id_from_username(username)

        # --- stories ---
        has_story = bool(cl.user_stories(user_id))

        # --- posts + reels ---
        feed = cl.user_medias(user_id, 30)

        reels_today = False
        posts_today = False

        today = datetime.utcnow().date()

        for m in feed:
            if m.taken_at.date() == today:
                if m.media_type == 2:
                    reels_today = True
                else:
                    posts_today = True

        return username, has_story, reels_today, posts_today

    except Exception as e:
        print(f"[ERROR] {username}: {e}")
        return username, False, False, False

