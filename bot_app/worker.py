import os
import asyncio
from dotenv import load_dotenv
from .db import AsyncSessionLocal
from .models import Download, DownloadStatus, User
from .downloader import run_ytdlp, TMP_DIR
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime

load_dotenv()
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))

# Проста in-memory черга + семафор (локально)
_queue = asyncio.Queue()
_semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def enqueue_download(user_tg_id: int, url: str) -> int:
    # створити запис у БД та поставити в чергу
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(User).where(User.telegram_id == user_tg_id))
        user = q.scalars().first()
        if not user:
            user = User(telegram_id=user_tg_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        d = Download(user_id=user.id, url=url, status=DownloadStatus.pending)
        session.add(d)
        await session.commit()
        await session.refresh(d)
        await _queue.put(d.id)
        return d.id

async def worker_loop():
    while True:
        download_id = await _queue.get()
        asyncio.create_task(process_job(download_id))

async def process_job(download_id: int):
    async with _semaphore:
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(Download).where(Download.id == download_id))
            d = q.scalars().first()
            if not d:
                return
            try:
                await session.execute(update(Download).where(Download.id == download_id).values(status=DownloadStatus.processing))
                await session.commit()
                # скачування
                out_basename = f"dl_{download_id}_%(title)s.%(ext)s"
                file_path = await run_ytdlp(d.url, out_basename)
                if not file_path:
                    raise RuntimeError("no output file")
                # зберегти шлях і статус
                d.file_path = str(file_path)
                d.file_size = file_path.stat().st_size
                d.status = DownloadStatus.done
                d.finished_at = datetime.utcnow()
                session.add(d)
                await session.commit()
                # тут треба нотифікувати користувача: для простоти — запис у БД, бот може періодично перевіряти finished jobs
            except Exception as e:
                d.error = str(e)
                d.status = DownloadStatus.failed
                session.add(d)
                await session.commit()
