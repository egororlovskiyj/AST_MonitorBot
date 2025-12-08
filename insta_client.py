# insta_client.py
import os
import asyncio
from typing import Any, Dict

import aiohttp

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "instagram-scraper-stable-api.p.rapidapi.com")

BASE_URL = f"https://{RAPIDAPI_HOST}"


if not RAPIDAPI_KEY:
    raise RuntimeError("RAPIDAPI_KEY is not set in Railway variables")


def _make_username_url(username: str) -> str:
    """
    Превращаем ник в полный URL профиля, как требует Scraper.
    Можно передавать и готовый URL — тогда он просто вернётся.
    """
    username = username.strip()
    if "instagram.com" in username:
        return username

    username = username.strip("@").strip("/")
    return f"https://www.instagram.com/{username}/"


async def _post(
    session: aiohttp.ClientSession,
    path: str,
    payload: Dict[str, str],
) -> Dict[str, Any]:
    """
    Общий helper для POST-запросов к RapidAPI.
    Возвращает:
    { "ok": True, "data": {...} } или { "ok": False, "error": "rate_limited", "detail": "..." }
    """
    url = f"{BASE_URL}/{path}"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }

    last_error = "unknown_error"

    # Пара попыток на случай таймаута / временных глюков
    for attempt in range(3):
        try:
            async with session.post(url, data=payload, headers=headers, timeout=40) as resp:
                status = resp.status
                text = await resp.text()

                if status == 429:
                    return {"ok": False, "error": "rate_limited", "detail": text}
                if status >= 400:
                    return {"ok": False, "error": f"http_{status}", "detail": text}

                # если всё ок — парсим JSON
                try:
                    data = await resp.json()
                except Exception:
                    return {"ok": False, "error": "bad_json", "detail": text}

                return {"ok": True, "data": data}

        except asyncio.TimeoutError:
            last_error = "timeout"
        except Exception as e:  # типа сетевые ошибки
            last_error = str(e)

        # небольшая пауза перед повторной попыткой
        await asyncio.sleep(2)

    return {"ok": False, "error": last_error, "detail": None}


def _append_error(current: str | None, part: str) -> str:
    if not current:
        return part
    return current + "; " + part


async def fetch_user_activity(username: str) -> Dict[str, Any]:
    """
    Возвращает агрегированный статус по пользователю:

    {
        "has_story": bool,
        "has_reels": bool,
        "has_photo": bool,
        "followers": int | None,
        "banned": bool,
        "error": str | None,
    }
    """

    result: Dict[str, Any] = {
        "has_story": False,
        "has_reels": False,
        "has_photo": False,
        "followers": None,
        "banned": False,
        "error": None,
    }

    url = _make_username_url(username)

    async with aiohttp.ClientSession() as session:
        # ---------- POSTS ----------
        posts_resp = await _post(
            session,
            "get_ig_user_posts.php",
            {"username_or_url": url, "amount": "12"},
        )
        if not posts_resp["ok"]:
            detail = (posts_resp.get("detail") or "").lower()
            if "forbidden" in detail or "unauthorized" in detail or "private" in detail:
                result["banned"] = True
            result["error"] = _append_error(result["error"], f"posts:{posts_resp['error']}")
        else:
            data = posts_resp["data"]
            posts = data.get("posts") or data.get("data") or []
            result["has_photo"] = bool(posts)

        # ---------- REELS ----------
        reels_resp = await _post(
            session,
            "get_ig_user_reels.php",
            {"username_or_url": url, "amount": "12"},
        )
        if not reels_resp["ok"]:
            detail = (reels_resp.get("detail") or "").lower()
            if "forbidden" in detail or "unauthorized" in detail or "private" in detail:
                result["banned"] = True
            result["error"] = _append_error(result["error"], f"reels:{reels_resp['error']}")
        else:
            data = reels_resp["data"]
            reels = data.get("reels") or data.get("data") or []
            result["has_reels"] = bool(reels)

        # ---------- STORIES ----------
        stories_resp = await _post(
            session,
            "get_ig_user_stories.php",
            {"username_or_url": url},
        )
        if not stories_resp["ok"]:
            detail = (stories_resp.get("detail") or "").lower()
            if "forbidden" in detail or "unauthorized" in detail or "private" in detail:
                result["banned"] = True
            result["error"] = _append_error(result["error"], f"stories:{stories_resp['error']}")
        else:
            data = stories_resp["data"]
            stories = data.get("stories") or data.get("data") or []
            result["has_story"] = bool(stories)

        # ---------- FOLLOWERS (Account Data V2) ----------
        profile_resp = await _post(
            session,
            "get_ig_account_data_v2.php",
            {"username_or_url": url},
        )
        if profile_resp["ok"]:
            data = profile_resp["data"]
            followers = None

            if isinstance(data, dict):
                if isinstance(data.get("followers"), int):
                    followers = data["followers"]
                elif isinstance(data.get("edge_followed_by"), dict):
                    followers = data["edge_followed_by"].get("count")

            result["followers"] = followers
        else:
            result["error"] = _append_error(result["error"], f"followers:{profile_resp['error']}")

    return result
