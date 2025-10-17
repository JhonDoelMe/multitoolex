# bot_app/handlers.py
import re
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from sqlalchemy.future import select

from .bot import dp
from .keyboard import main_menu, back_menu, confirm_download
from .models import User, Download
from .db import AsyncSessionLocal
from .worker import enqueue_download


# ------------------------------------------------------------
# /start
# ------------------------------------------------------------
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    """
    Приветствие нового пользователя и добавление в БД при первом входе.
    """
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = q.scalar_one_or_none()
        if user is None:
            session.add(User(telegram_id=message.from_user.id))
            await session.commit()

    await message.answer(
        "👋 Привіт! Надішли мені посилання на відео з YouTube, і я його скачаю 🎬",
        reply_markup=main_menu(),
    )


# ------------------------------------------------------------
# Обработка текста — если это ссылка на видео
# ------------------------------------------------------------
YOUTUBE_REGEX = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/")

@dp.message(F.text)
async def handle_url_or_command(message: Message):
    """
    Ловим любое сообщение: если это YouTube-ссылка — предлагаем подтвердить.
    """
    text = message.text.strip()
    if YOUTUBE_REGEX.search(text):
        await message.answer(
            f"🔗 Знайдено посилання:\n{text}\n\nПочати завантаження?",
            reply_markup=confirm_download(text),
        )
    else:
        await message.answer(
            "⚠️ Це не схоже на посилання YouTube.\nНадішліть коректну URL або натисніть кнопку нижче 👇",
            reply_markup=main_menu(),
        )


# ------------------------------------------------------------
# Callback: подтверждение загрузки
# ------------------------------------------------------------
@dp.callback_query(F.data.startswith("download:"))
async def cb_download(call: CallbackQuery):
    """
    Пользователь подтвердил загрузку видео.
    """
    url = call.data.split("download:", 1)[1]
    await call.message.edit_text(f"📥 Завантаження розпочато…\n{url}")

    job_id = await enqueue_download(call.from_user.id, url)
    await call.message.answer(
        f"✅ Додано в чергу (ID {job_id}).\nБот повідомить, коли відео буде готове.",
        reply_markup=main_menu(),
    )
    await call.answer()


# ------------------------------------------------------------
# Callback: отмена
# ------------------------------------------------------------
@dp.callback_query(F.data == "cancel")
async def cb_cancel(call: CallbackQuery):
    await call.message.edit_text("❌ Скасовано.", reply_markup=main_menu())
    await call.answer()


# ------------------------------------------------------------
# Назад
# ------------------------------------------------------------
@dp.message(F.text == "↩️ Назад")
async def cmd_back(message: Message):
    await message.answer("Головне меню", reply_markup=main_menu())


# ------------------------------------------------------------
# Инструкция
# ------------------------------------------------------------
@dp.message(F.text == "ℹ️ Інструкція")
async def cmd_help(message: Message):
    await message.answer(
        "📘 Як користуватись:\n"
        "1️⃣ Надішліть посилання на відео з YouTube\n"
        "2️⃣ Підтвердіть завантаження\n"
        "3️⃣ Дочекайтесь повідомлення про готовий файл\n\n"
        "Бот сам виконає все інше 💪",
        reply_markup=back_menu(),
    )


# ------------------------------------------------------------
# Выход
# ------------------------------------------------------------
@dp.message(F.text == "❌ Вийти")
async def cmd_exit(message: Message):
    await message.answer("До зустрічі 👋", reply_markup=back_menu())
    # Тут можна додати логіку для "виходу", якщо потрібно