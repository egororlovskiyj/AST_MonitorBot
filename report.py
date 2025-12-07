# report.py

from typing import Dict, List, Any


def _line_for_user(info: dict) -> str:
    """
    info:
      username, story, reels, photo, followers, diff, banned, error
    """
    username = info["username"]
    has_story = info["story"]
    has_reels = info["reels"]
    has_photo = info["photo"]
    followers = info.get("followers")
    diff = info.get("followers_diff")
    banned = info.get("banned")
    error = info.get("error")

    if banned:
        base = f"{username} — 🚫 нет доступа (возможно бан/приват)"
    elif error:
        base = f"{username} — ⚠️ ошибка: {error}"
    else:
        if not (has_story or has_reels or has_photo):
            base = f"{username} — ❌ no content"
        else:
            parts = []
            parts.append("✅ story" if has_story else "✖ story")
            parts.append("✅ reels" if has_reels else "✖ reels")
            parts.append("✅ photo" if has_photo else "✖ photo")
            base = f"{username} — " + " | ".join(parts)

    # Фолловеры
    if followers is not None:
        if diff is None or diff == 0:
            base += f" | 👥 {followers}"
        else:
            sign = "📈" if diff > 0 else "📉"
            base += f" | 👥 {followers} ({'+' if diff>0 else ''}{diff}) {sign}"

    return base


def build_report(results: Dict[str, List[dict]]) -> str:
    """
    results: { "Finland": [ {...}, {...} ], "Sweden": [...] }
    """
    lines = []
    lines.append("📊 Daily IG Report — 21:00 (GMT+2)\n")

    for country, items in results.items():
        lines.append(f"🇫🇮 {country}:")  # можешь потом заменить флаг под страну
        if not items:
            lines.append("  нет аккаунтов")
            continue

        for info in items:
            lines.append(_line_for_user(info))
        lines.append("")  # пустая строка между странами

    return "\n".join(lines).strip()


def build_inactive_alert(usernames: list[str], days: int = 3) -> str | None:
    if not usernames:
        return None
    lines = []
    lines.append(f"⚠️ {days} дня подряд без контента:")
    for u in usernames:
        lines.append(f"• {u}")
    return "\n".join(lines)
