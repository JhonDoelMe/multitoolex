# bot_app/downloader.py
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Optional

import yt_dlp


# ------------------------------------------------------------
# yt-dlp utility
# ------------------------------------------------------------
async def run_ytdlp(url: str, out_filename: str) -> Optional[Path]:
    """
    Асинхронно запускает yt-dlp для скачивания видео.
    Возвращает путь к готовому файлу или None, если не удалось.
    """
    tmpdir = Path(tempfile.gettempdir()) / "multitoolex_downloads"
    tmpdir.mkdir(parents=True, exist_ok=True)
    output_path = tmpdir / f"{out_filename}.%(ext)s"

    ydl_opts = {
        "format": "mp4/bestvideo+bestaudio/best",
        "outtmpl": str(output_path),
        "quiet": True,
        "noprogress": True,
        "merge_output_format": "mp4",
        "retries": 3,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "continuedl": True,
        "ignoreerrors": True,
    }

    def _download_sync() -> Optional[Path]:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    return None
                filename = ydl.prepare_filename(info)
                return Path(filename)
        except Exception:
            return None

    file_path = await asyncio.to_thread(_download_sync)
    if file_path and file_path.exists():
        return file_path
    return None


# ------------------------------------------------------------
# move_file_to_final
# ------------------------------------------------------------
def move_file_to_final(file_path: Path, dest_dir: Path) -> Optional[Path]:
    """
    Перемещает скачанный файл из временной папки в итоговую директорию.
    Возвращает новый путь.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        new_path = dest_dir / file_path.name
        shutil.move(str(file_path), str(new_path))
        return new_path
    except Exception:
        return None
