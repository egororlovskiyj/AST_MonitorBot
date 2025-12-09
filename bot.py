import asyncio
from aiogram import Bot, Dispatcher, types
from scheduler import scheduler_loop
from config import BOT_TOKEN, CHAT_ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


async def send_report_via_bot(text: str):
    await bot.send_message(CHAT_ID, text)


async def on_startup(_):
    asyncio.create_task(scheduler_loop())


def main():
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


if __name__ == "__main__":
    main()

