# report.py
from typing import Dict, List

from instagram_checker import CheckResult


def _format_line(res: CheckResult) -> str:
    if res.banned:
        return f"{res.username} — 🚫 нет доступа (возможно бан/приват)"

    # если рейтлимит / любая ошибка
    errors = []
    if res.error_posts:
        errors.append(f"posts:{res.error_posts}")
    if res.error_reels:
        errors.append(f"reels:{res.error_reels}")
    if res.error_stories:
        errors.append(f"stories:{res.error_stories}")

    if errors:
        return f"{res.username} — ⚠️ ошибка: " + "; ".join(errors)

    # нормальное состояние
    parts = []
    if res.has_photo:
        parts.append("посты ✅")
    else:
        parts.append("посты — нет")

    if res.has_reels:
        parts.append("reels ✅")
    else:
        parts.append("reels — нет")

    if res.has_story:
        parts.append("сториз ✅")
    else:
        parts.append("сториз — нет")

    return f"{res.username} — " + ", ".join(parts)


def build_daily_report(results_by_country: Dict[str, List[CheckResult]]) -> str:
    """
    Собираем финальный текст отчёта.
    results_by_country = { "Finland": [CheckResult, ...], "Denmark": [...] }
    """
    lines: list[str] = []
    lines.append("📊 Daily IG Report")

    # можно добавить время, если хочешь – сейчас бот у тебя сам его пишет.

    for country, items in results_by_country.items():
        if country.lower().startswith("fin"):
            flag = "🇫🇮"
        elif country.lower().startswith("den"):
            flag = "🇩🇰"
        else:
            flag = "🌍"

        lines.append("")
        lines.append(f"{flag} {country}:")
        for res in items:
            lines.append(_format_line(res))

    return "\n".join(lines)
