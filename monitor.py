# monitor.py
from instagram_checker import check_account_content

async def check_account(username):
    """
    Возвращает кортеж:
    (username, story_bool, reels_bool, post_bool)
    Формат совместим с твоим bot.py и report.py
    """

    data = await check_account_content(username)

    if data["error"]:
        # если ошибка — считаем что контента нет
        return (username, False, False, False)

    return (
        username,
        data["story"],
        data["reels"],
        data["post"]
    )

