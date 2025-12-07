# instagram_checker.py
import asyncio
from datetime import datetime, timedelta

import aiohttp
import pytz

from config import (
    RAPIDAPI_KEY,
    RAPIDAPI_HOST,
    RAPIDAPI_BASE_URL,
    IG_USER_POSTS_PATH,
    IG_USER_REELS_PATH,
    IG_USER_STORIES_PATH,
    IG_USER_INFO_PATH,
    TIMEZONE,
    HOURS_WINDOW,
)

TZ = pytz.timezone(TIMEZONE)

COMMON_HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
    "Content-Type": "application/x-www-form-urlencoded",
}


class ApiError(Exception):
    """Общая ошибка API."""


async def _fetch_json(session: aiohttp.ClientSession, url: str, data: dict) -> dict:
    """POST на RapidAPI, возвращаем JSON или бросаем ApiError."""
    try:
        async with session.post(url, data=data, headers=COMMON_HEADERS) as resp:
            status = resp.status

            # Важные статусы
            if status in (401, 403):
                raise ApiError("forbidden_or_unauthorized")
            if status == 404:
                raise ApiError("not_found")
            if status == 429:
                raise ApiError("rate_limited")
            if status >= 500:
                raise ApiError(f"server_error_{status}")

            try:
                data = await resp.json()
            except Exception:
                text = await resp.text()
                raise ApiError(f"bad_json:{text[:200]}")

    except ApiError:
        raise
    except Exception as e:
        raise ApiError(f"network_error:{e}")

    # Если в теле ошибка
    if isinstance(data, dict) and "error" in data:
        # Например: {"error": "Username is required"}
        raise ApiError(str(data["error"]))

    return data


def _extract_ts_from_node(node: dict) -> datetime | None:
    """
    Пытаемся вытащить timestamp поста/рила/сторис.
    ТУТ МОЖНО ПОДКРУТИТЬ ПОД ТОЧНЫЙ JSON, КОТОРЫЙ ТЫ ВИДИШЬ.
    """
    ts = (
        node.get("taken_at")
        or node.get("created_at")
        or node.get("timestamp")
        or node.get("caption", {}).get("created_at")
    )

    if ts is None:
        return None

    if isinstance(ts, str) and ts.isdigit():
        ts = int(ts)

    try:
        return datetime.fromtimestamp(int(ts), tz=pytz.UTC).astimezone(TZ)
    except Exception:
        return None


def _is_recent(ts: datetime | None) -> bool:
    if not ts:
        return False
    now = datetime.now(TZ)
    return now - ts <= timedelta(hours=HOURS_WINDOW)


async def _get_posts(session: aiohttp.ClientSession, username: str) -> tuple[bool, str | None]:
    """Есть ли СЕГОДНЯ посты/фото у юзера."""
    url = RAPIDAPI_BASE_URL + IG_USER_POSTS_PATH
    form = {
        "username_or_url": f"https://www.instagram.com/{username}/",
        "amount": "12",
    }
    data = await _fetch_json(session, url, form)

    posts = data.get("posts") or data.get("items") or []
    recent = False
    for item in posts:
        # в твоём примере пост лежал в item["node"]
        node = item.get("node") if isinstance(item, dict) else None
        if not node:
            node = item
        ts = _extract_ts_from_node(node)
        if _is_recent(ts):
            recent = True
            break
    return recent, None


async def _get_reels(session: aiohttp.ClientSession, username: str) -> tuple[bool, str | None]:
    """Есть ли СЕГОДНЯ рилсы."""
    url = RAPIDAPI_BASE_URL + IG_USER_REELS_PATH
    form = {
        "username_or_url": f"https://www.instagram.com/{username}/",
        "amount": "12",
    }
    data = await _fetch_json(session, url, form)

    reels = data.get("reels") or data.get("items") or data.get("posts") or []
    recent = False
    for item in reels:
        node = item.get("node") if isinstance(item, dict) else item
        ts = _extract_ts_from_node(node)
        if _is_recent(ts):
            recent = True
            break
    return recent, None


async def _get_stories(session: aiohttp.ClientSession, username: str) -> tuple[bool, str | None]:
    """Есть ли СЕГОДНЯ сторис."""
    url = RAPIDAPI_BASE_URL + IG_USER_STORIES_PATH
    form = {
        "username_or_url": f"https://www.instagram.com/{username}/",
    }
    data = await _fetch_json(session, url, form)

    stories = data.get("stories") or data.get("items") or []
    recent = False
    for item in stories:
        node = item.get("node") if isinstance(item, dict) else item
        ts = _extract_ts_from_node(node)
        if _is_recent(ts):
            recent = True
            break
    return recent, None


async def _get_user_info(session: aiohttp.ClientSession, username: str) -> tuple[int | None, bool, str | None]:
    """
    Возвращаем (followers, banned, error).

    banned = True, если API отдаёт not_found/forbidden и т.п.
    """
    url = RAPIDAPI_BASE_URL + IG_USER_INFO_PATH
    form = {
        "username_or_url": f"https://www.instagram.com/{username}/",
    }

    try:
        data = await _fetch_json(session, url, form)
    except ApiError as e:
        msg = str(e)
        if "not_found" in msg or "forbidden" in msg or "private" in msg:
            return None, True, msg
        return None, False, msg

    # ТУТ нужно один раз посмотреть JSON профиля в playground
    # и записать реальное поле с количеством подписчиков
    followers = (
        data.get("user", {}).get("follower_count")
        or data.get("follower_count")
        or data.get("followers")
    )

    try:
        followers = int(followers) if followers is not None else None
    except Exception:
        followers = None

    return followers, False, None


async def check_account(username: str) -> tuple[str, bool, bool, bool, int | None, bool, str | None]:
    """
    Главная функция:
    возвращает (username, has_story, has_reels, has_photo, followers, banned, error)
    """
    async with aiohttp.ClientSession() as session:
        # сначала профиль — чтобы сразу поймать бан/404
        followers, banned, info_err = await _get_user_info(session, username)

        if banned:
            # если бан/404 — дальше не дёргаем посты
            return username, False, False, False, followers, True, info_err

        # параллельно, но без дикого спама — можно последовательно, так надёжнее
        errors = []

        try:
            has_photo, err = await _get_posts(session, username)
            if err:
                errors.append(f"posts:{err}")
        except ApiError as e:
            has_photo = False
            errors.append(f"posts:{e}")

        # маленькая пауза, чтобы не ловить 429
        await asyncio.sleep(0.3)

        try:
            has_reels, err = await _get_reels(session, username)
            if err:
                errors.append(f"reels:{err}")
        except ApiError as e:
            has_reels = False
            errors.append(f"reels:{e}")

        await asyncio.sleep(0.3)

        try:
            has_story, err = await _get_stories(session, username)
            if err:
                errors.append(f"stories:{err}")
        except ApiError as e:
            has_story = False
            errors.append(f"stories:{e}")

        error_text = "; ".join(errors) if errors else info_err

        return username, has_story, has_reels, has_photo, followers, banned, error_text


