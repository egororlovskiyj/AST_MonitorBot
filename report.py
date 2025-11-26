def build_report(results: dict) -> str:
    """
    results = {
        "Finland": [
            (username, has_story, reels, photo),
            ...
        ],
        ...
    }
    """
    lines = []
    lines.append("📊 Daily IG Report — 21:00 (GMT+2)")

    flag_by_country = {
        "Finland": "🇫🇮",
        "Sweden": "🇸🇪",
        "Norway": "🇳🇴",
        "Denmark": "🇩🇰",
        "Iceland": "🇮🇸",
    }

    for country, items in results.items():
        flag = flag_by_country.get(country, "🌍")
        lines.append("")
        lines.append(f"{flag} {country}:")

        for username, has_story, reels, photo in items:
            parts = []

            # логика крестиков / галочек как у тебя в отчёте
            if reels:
                parts.append("✅ reels")
            if photo:
                parts.append("✅ photo")

            if not reels and not photo:
                parts.append("❌ no content")

            line = f"{username} — " + " | ".join(parts)
            lines.append(line)

    return "\n".join(lines)


def build_inactive_alert(usernames, days: int = 3) -> str:
    if not usernames:
        return ""

    lines = ["⚠️ Внимание! Без контента последние "
             f"{days} дня:"]
    for u in usernames:
        lines.append(f"• {u}")
    return "\n".join(lines)

