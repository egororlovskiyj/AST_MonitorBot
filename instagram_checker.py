# instagram_checker.py

from insta_client import get_insta_client

insta = get_insta_client()


async def check_account_content(username: str):
    """Возвращает dict с флагами: сториз, рилсы, посты."""

    try:
        user_id = insta.user_id_from_username(username)

        # Сториз
        stories = insta.user_stories(user_id)
        has_story = len(stories) > 0

        # Рилсы
        reels = insta.user_clips(user_id)
        has_reels = len(reels) > 0

        # Последний пост (1 шт.)
        posts = insta.user_medias(user_id, amount=1)
        has_post = len(posts) > 0

        return {
            "story": has_story,
            "reels": has_reels,
            "post": has_post,
            "error": None
        }

    except Exception as e:
        return {
            "story": False,
            "reels": False,
            "post": False,
            "error": str(e)
        }
