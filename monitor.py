import asyncio
from instagram_checker import check_account

# Этот файл просто вызывает новую функцию check_account
# и ничего лишнего не делает.

async def monitor_user(username):
    return await check_account(username)
