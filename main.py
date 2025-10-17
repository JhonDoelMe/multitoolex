import asyncio
from bot_app.bot import dp
from bot_app import handlers  # реєструє хендлери
from bot_app.worker import worker_loop
from aiogram import F
from aiogram import Bot
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start_worker():
    # запускаємо цикл обробки черги
    await worker_loop()

async def main():
    # start worker як бекграунд таск
    loop = asyncio.get_event_loop()
    loop.create_task(start_worker())
    # запускаємо long polling aiogram
    from aiogram import Bot, Dispatcher
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
