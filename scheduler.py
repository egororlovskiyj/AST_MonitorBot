import asyncio
from datetime import datetime, timedelta

from config import REPORT_HOUR, REPORT_TZ_OFFSET
from monitor import run_monitor_cycle
from report import send_report_via_bot


async def scheduler_loop():
    print("[scheduler] started")

    while True:
        try:
            # локальное время Финляндии
            now = datetime.utcnow() + timedelta(hours=REPORT_TZ_OFFSET)

            # запускаем проверку инстаграмов
            await run_monitor_cycle()

            # отправляем отчет ровно в заданный час
            if now.hour == REPORT_HOUR:
                print("[scheduler] Sending daily report...")
                await send_report_via_bot()

        except Exception as e:
            print("[scheduler] ERROR:", e)

        # ждем 1 час
        await asyncio.sleep(3600)
