# bot_app/bot.py
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# ------------------------------------------------------------
# Dispatcher setup
# ------------------------------------------------------------
# Тут не создаём Bot, чтобы избежать дубликатов экземпляров.
# Bot создаётся и управляется в main.py, а сюда просто импортируется dp.
# Это нужно, чтобы aiogram не открывал лишних HTTP-сессий.
dp = Dispatcher(storage=MemoryStorage())

# Импортируем хендлеры, чтобы они зарегистрировались при импорте
from . import handlers  # noqa: F401
