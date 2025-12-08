import os
import httpx


RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "instagram-scraper-stable-api.p.rapidapi.com")

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
    "Content-Type": "application/x-www-form-urlencoded"
}

BASE_URL = f"https://{RAPIDAPI_HOST}"


async def _post(session: httpx.AsyncClient, endpoint: str, data: dict) -> dict:
    try:
        r = await session.post(f"{BASE_URL}/{endpoint}", headers=HEADERS, data=data, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


async def check_user(username: str) -> dict:
    """
    Универсальная проверка профиля: сторис, рилсы, посты, фолловеры, бан.
    """
    async with httpx.AsyncClient() as session:
        out = {
            "username": username,
            "has_story": False,
            "has_reels": False,
            "has_photo": False,
            "followers": None,
            "banned": False,
            "error": None,
        }

        # --- POSTS ---
        posts = await _post(session, "get_ig_user_posts.php", {"username_or_url": username, "amount": 1})
        if "error" in posts:
            out["error"] = f"posts:{posts['error']}"
        elif posts.get("posts") is None:
            out["banned"] = True
        elif posts.get("posts"):
            out["has_photo"] = True

        # --- REELS ---
        reels = await _post(session, "get_ig_user_reels.php", {"username_or_url": username, "amount": 1})
        if "error" in reels:
            out["error"] = f"{out['error']}; reels:{reels['error']}" if out["error"] else f"reels:{reels['error']}"
        elif reels.get("reels"):
            out["has_reels"] = True

        # --- STORIES ---
        stories = await _post(session, "get_ig_user_highlight_stories.php", {"username_or_url": username})
        if "error" in stories:
            out["error"] = f"{out['error']}; stories:{stories['error']}" if out["error"] else f"stories:{stories['error']}"
        elif stories.get("stories"):
            out["has_story"] = True

        # --- FOLLOWERS ---
        about = await _post(session, "get_ig_user_about.php", {"username_or_url": username})
        if "error" in about:
            out["error"] = f"{out['error']}; about:{about['error']}" if out["error"] else f"about:{about['error']}"
        else:
            out["followers"] = about.get("user", {}).get("follower_count")

        return out
