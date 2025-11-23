from datetime import datetime
from config import TIMEZONE
import pytz

def build_report(results):
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz).strftime("%H:%M")
    out = f"📊 Daily IG Report — {now} (GMT+2)\n\n"

    for country, accounts in results.items():
        flag = {
            "Finland": "🇫🇮",
            "Denmark": "🇩🇰",
            "Norway": "🇳🇴",
            "Sweden": "🇸🇪"
        }.get(country, "")

        out += f"{flag} {country}:\n"

        for row in accounts:
            user, story, reels, post = row
            if story or reels or post:
                out += f"{user} — "
                if story: out += "✔️ stories "
                if reels: out += "| ✔️ reels "
                if post: out += "| ✔️ photo "
                out += "\n"
            else:
                out += f"{user} — ❌ no content\n"

        out += "\n"

    return out
