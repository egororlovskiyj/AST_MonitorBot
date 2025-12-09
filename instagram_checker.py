# instagram_checker.py
from dataclasses import dataclass
from typing import Optional

from insta_client import InstagramClient
from db import save_result


@dataclass
class CheckResult:
    username: str
    has_story: bool
    has_reels: bool
    has_photo: bool
    followers: Optional[int]
    banned: bool
    error_posts: Optional[str]
    error_reels: Optional[str]
    error_stories: Optional[str]

    @property
    def any_error(self) -> bool:
        return bool(self.error_posts or self.error_reels or self.error_stories)


async def check_account(client: InstagramClient, username: str) -> CheckResult:
    """
    Делаем 3 запроса: посты, рилсы, сториз.
    Аккуратно ловим ошибки, чтобы не падал весь отчёт.
    """
    has_photo = has_reels = has_story = False
    err_posts = err_reels = err_stories = None
    banned = False

    # POSTs
    try:
        has_photo, err_posts = await client.get_posts(username)
        if err_posts and "forbidden" in err_posts:
            banned = True
    except Exception as e:
        err_posts = f"exception:{e}"

    # REELS
    try:
        has_reels, err_reels = await client.get_reels(username)
        if err_reels and "forbidden" in err_reels:
            banned = True
    except Exception as e:
        err_reels = f"exception:{e}"

    # STORIES
    try:
        has_story, err_stories = await client.get_stories(username)
        if err_stories and "forbidden" in err_stories:
            banned = True
    except Exception as e:
        err_stories = f"exception:{e}"

    followers = None  # пока так, при желании можно докрутить

    # единый error для БД – собираем всё в строку
    parts = []
    if err_posts:
        parts.append(f"posts:{err_posts}")
    if err_reels:
        parts.append(f"reels:{err_reels}")
    if err_stories:
        parts.append(f"stories:{err_stories}")
    error_str = "; ".join(parts) if parts else None

    await save_result(
        username=username,
        has_story=has_story,
        has_reels=has_reels,
        has_photo=has_photo,
        followers=followers,
        banned=banned,
        error=error_str,
    )

    return CheckResult(
        username=username,
        has_story=has_story,
        has_reels=has_reels,
        has_photo=has_photo,
        followers=followers,
        banned=banned,
        error_posts=err_posts,
        error_reels=err_reels,
        error_stories=err_stories,
    )
