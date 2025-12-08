from insta_client import check_user

async def check_account(username: str) -> dict:
    """
    Старое имя функции сохранено для совместимости с bot.py / monitor.py
    """
    return await check_user(username)
