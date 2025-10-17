# bot_app/worker.py
import os
import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.future import select

from .db import AsyncSessionLocal
from .models import Download, DownloadStatus, User
from .downloader import run_ytdlp, move_file_to_final


# ------------------------------------------------------------
# Параметры очереди
# ------------------------------------------------------------
MAX_CONCURRENT = int(os.getenv("WORKER_CONCURRENCY", "2"))
FINAL_DIR = Path(os.getenv("DOWNLOADS_DIR", "./data/downloads")).resolve()

_queue: asyncio.Queue["Job"] = asyncio.Queue()
_semaphore = asyncio.Semaphore(MAX_CONCURRENT)


@dataclass
class Job:
    download_id: int


# ------------------------------------------------------------
# Паблик-функция: постановка задачи в очередь
# ------------------------------------------------------------
async def enqueue_download(user_tg_id: int, url: str) -> int:
    """
    Создаёт запись Download со статусом pending и ставит задачу в очередь.
    Возвращает ID загрузки.
    """
    async with AsyncSessionLocal() as session:
        # убеждаемся, что пользователь существует
        q = await session.execute(select(User).where(User.telegram_id == user_tg_id))
        user = q.scalar_one_or_none()
        if user is None:
            user = User(telegram_id=user_tg_id)
            session.add(user)
            await session.flush()

        d = Download(user_id=user.id, url=url, status=DownloadStatus.pending)
        session.add(d)
        await session.commit()

        await _queue.put(Job(download_id=d.id))
        return d.id


# ------------------------------------------------------------
# Внутренний воркер
# ------------------------------------------------------------
async def _worker():
    while True:
        job = await _queue.get()
        try:
            async with _semaphore:
                await _process_job(job)
        finally:
            _queue.task_done()


async def _process_job(job: Job) -> None:
    async with AsyncSessionLocal() as session:
        d: Optional[Download] = await session.get(Download, job.download_id)
        if d is None:
            return

        # помечаем как processing
        d.status = DownloadStatus.processing
        await session.commit()

        try:
            # 1) Скачиваем во временную директорию (yt-dlp)
            tmp_file = await run_ytdlp(d.url, out_filename=str(d.id))
            if not tmp_file or not tmp_file.exists():
                raise RuntimeError("failed to download")

            # 2) Переносим в постоянное хранилище
            final_path = move_file_to_final(tmp_file, FINAL_DIR)
            if not final_path or not final_path.exists():
                raise RuntimeError("failed to move file to final dir")

            # 3) Обновляем запись
            d.file_path = str(final_path)
            d.file_size = final_path.stat().st_size
            d.status = DownloadStatus.done
            d.finished_at = datetime.utcnow()
            await session.commit()

        except Exception as e:
            d.error = str(e)
            d.status = DownloadStatus.failed
            d.finished_at = datetime.utcnow()
            await session.commit()


# ------------------------------------------------------------
# Публичный цикл воркеров
# ------------------------------------------------------------
async def worker_loop():
    """
    Запускает N конкурентных воркеров.
    Бесконечный цикл; завершение через отмену task (task.cancel()).
    """
    workers = [asyncio.create_task(_worker(), name=f"worker-{i}") for i in range(MAX_CONCURRENT)]
    try:
        await asyncio.gather(*workers)
    finally:
        for w in workers:
            if not w.cancelled():
                w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
