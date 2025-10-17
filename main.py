# main.py
import os
import asyncio
import logging
from contextlib import suppress

from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from bot_app.bot import dp  # экспортируем только Dispatcher
from bot_app.db import init_db
from bot_app.worker import worker_loop

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


async def _start_background_workers():
    """
    Запускает фоновые воркеры (очередь скачиваний и пр.).
    Возвращает список тасков, чтобы их можно было отменить при остановке.
    """
    tasks = []
    tasks.append(asyncio.create_task(worker_loop(), name="worker_loop"))
    return tasks


async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set in environment")

    # 1) Инициализируем БД (создаём таблицы, если нет)
    await init_db()

    # 2) Запускаем фоновые задачи
    bg_tasks = await _start_background_workers()

    # 3) Запускаем Telegram-бота (Aiogram >= 3.7: parse_mode через DefaultBotProperties)
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Корректная остановка фоновых задач
        for t in bg_tasks:
            t.cancel()
        for t in bg_tasks:
            with suppress(asyncio.CancelledError):
                await t
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Shutdown requested, exiting…")
