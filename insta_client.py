# insta_client.py
import time
from typing import Any, Tuple, Optional

import httpx

from config import RAPIDAPI_KEY, RAPIDAPI_HOST

BASE_URL = "https://instagram-scraper-stable-api.p.rapidapi.com"

# мягкий лимит – одна пачка запросов раз в 1.2 секунды
REQUEST_DELAY = 1.2


class InstagramClient:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=20.0)
        self._last_request_ts = 0.0

    async def _sleep_if_needed(self):
        now = time.time()
        delta = now - self._last_request_ts
        if delta < REQUEST_DELAY:
            await asyncio.sleep(REQUEST_DELAY - delta)
        self._last_request_ts = time.time()

    async def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        import asyncio  # локальный импорт, чтобы не тянуть наверх

        await self._sleep_if_needed()

        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        url = f"{BASE_URL}{endpoint}"
        resp = await self._client.post(url, data=payload, headers=headers)

        # RapidAPI почти всегда даёт 200, даже при ошибках, так что:
        data = resp.json()
        return data

    # --------- helpers ---------

    @staticmethod
    def _check_recent(items: list[dict[str, Any]], hours: int = 24) -> bool:
        """
        Проверяем, есть ли среди items что-то свежее за N часов.
        Пытаемся угадать поле с таймштампом: timestamp / taken_at / taken_at_timestamp.
        Если ничего нет – считаем, что свежего нет.
        """
        if not items:
            return False

        now = int(time.time())
        max_age = hours * 3600

        for it in items:
            ts = (
                it.get("timestamp")
                or it.get("taken_at")
                or it.get("taken_at_timestamp")
                or it.get("taken_at_ts")
            )
            try:
                ts_int = int(ts)
            except (TypeError, ValueError):
                continue

            if 0 < now - ts_int <= max_age:
                return True

        return False

    # --------- API wrappers ---------

    async def get_posts(self, username: str) -> Tuple[bool, Optional[str]]:
        """
        Возвращает (есть_ли_свежие_посты_за_сутки, ошибка).
        Ошибка = None, если всё ок.
        """
        data = await self._post("/get_ig_user_posts.php", {"username_or_url": username})

        if "error" in data:
            return False, data["error"]

        posts = data.get("posts") or data.get("data") or []
        has_recent = self._check_recent(posts)
        return has_recent, None

    async def get_reels(self, username: str) -> Tuple[bool, Optional[str]]:
        data = await self._post("/get_ig_user_reels.php", {"username_or_url": username})

        if "error" in data:
            return False, data["error"]

        reels = data.get("reels") or data.get("data") or []
        has_recent = self._check_recent(reels)
        return has_recent, None

    async def get_stories(self, username: str) -> Tuple[bool, Optional[str]]:
        data = await self._post(
            "/get_ig_user_stories.php", {"username_or_url": username}
        )

        if "error" in data:
            return False, data["error"]

        # у сториз обычно поле stories / data / items
        stories = data.get("stories") or data.get("data") or data.get("items") or []
        has_recent = self._check_recent(stories, hours=24)
        return has_recent, None

    async def get_followers_count(self, username: str) -> Optional[int]:
        """
        Если в ответах на посты будет user->follower_count – можно будет сюда докрутить.
        Пока возвращаем None, чтобы не ломать логику.
        """
        return None

    async def aclose(self):
        await self._client.aclose()
