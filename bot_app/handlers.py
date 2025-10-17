import os
import asyncio
from aiogram.types import Message
from aiogram import F
from .bot import dp, bot
from .keyboard import main_menu, back_menu
from .utils import extract_urls
from .worker import enqueue_download
from .db import AsyncSessionLocal
from .models import User
from sqlalchemy.future import select

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = q.scalars().first()
        if not user:
            user = User(telegram_id=message.from_user.id)
            session.add(user)
            await session.commit()
    await message.answer("Вітаю. Обери дію:", reply_markup=main_menu())

@dp.message(F.text == "Скачати відео")
async def show_download_prompt(message: Message):
    await message.answer("Надішли посилання або переслав повідомлення з відео", reply_markup=back_menu())

@dp.message(F.text == "Назад")
async def cmd_back(message: Message):
    await message.answer("Головне меню", reply_markup=main_menu())

@dp.message()
async def handle_text(message: Message):
    urls = extract_urls(message.text)
    if not urls:
        await message.answer("Не знайшов посилання. Надішліть посилання або переслане повідомлення.")
        return
    # беремо перше посилання (можна змінити логіку)
    url = urls[0]
    # створюємо задачу в черзі
    job_id = await enqueue_download(user_tg_id=message.from_user.id, url=url)
    await message.answer(f"Прийнято в обробку. Job ID: {job_id}")
