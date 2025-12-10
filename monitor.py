# monitor.py
import asyncio
from datetime import datetime, timedelta

from config import REPORT_TZ_OFFSET, REPORT_HOUR
from db import init_db
from report import send_report_via_bot
from instagram_checker import check_all_accounts


async def scheduler_loop():
    """
    Раз в минуту:
    - запускаем проверку аккаунтов (если ещё не ходили сегодня)
    - в нужный час шлём отчёт в телегу
    """
    await init_db()

    while True:
        try:
            # 1. Проверяем/обновляем активность инстаграм-аккаунтов
            await check_all_accounts()

            # 2. Проверяем, пора ли слать отчёт
            now = datetime.utcnow() + timedelta(hours=REPORT_TZ_OFFSET)
            if now.hour == REPORT_HOUR:
                await send_report_via_bot()

        except Exception as e:
            # чтобы любая ошибка не останавливала цикл на Railway
            print(f"[scheduler] ERROR in scheduler_loop: {e}")

        # спим минуту
        await asyncio.sleep(60)


def main():
    asyncio.run(scheduler_loop())


if __name__ == "__main__":
    main()
