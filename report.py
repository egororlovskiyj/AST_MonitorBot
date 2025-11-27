def build_report(results):
    lines = []
    lines.append("📊 Daily IG Report")

    for country, users in results.items():
        lines.append("")
        lines.append(f"🌍 {country}:")
        for u in users:
            username, story, reels, photo, status, diff = u

            parts = []
            if reels: parts.append("🎥 reels")
            if photo: parts.append("📸 post")
            if story: parts.append("🟢 story")
            if not (story or reels or photo): parts.append("❌ no content")

            if diff is not None:
                if diff > 0:
                    parts.append(f"📈 +{diff}")
                elif diff < 0:
                    parts.append(f"📉 {diff}")

            if status != "OK":
                parts.append(f"⚠️ {status}")

            lines.append(f"{username} — " + " | ".join(parts))

    return "\n".join(lines)


def build_inactive_alert(users, days=3):
    if not users:
        return ""
    text = f"⚠️ {days} days without content:\n"
    for u in users:
        text += f"• {u}\n"
    return text

