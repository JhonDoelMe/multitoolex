import os
import asyncio
import shlex
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
YT_DLP = os.getenv("YT_DLP_PATH", "yt-dlp")
TMP_DIR = Path(os.getenv("TMP_DIR", "/tmp/video_downloader"))
TMP_DIR.mkdir(parents=True, exist_ok=True)

async def run_ytdlp(url: str, out_filename: str, extra_args=None, timeout=300):
    out = str(TMP_DIR / out_filename)
    cmd = [
        YT_DLP,
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", out,
        url
    ]
    if extra_args:
        cmd.extend(extra_args)
    # Запуск через subprocess в окремому процесі
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        raise
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {stderr.decode()}")
    # yt-dlp формує файл згідно з шаблоном; знаходимо найновіший mp4 у TMP_DIR що починається з out_filename
    candidates = list(TMP_DIR.glob(f"{out_filename}*"))
    if not candidates:
        # fallback: знайти останній створений mp4
        mp4s = sorted(TMP_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        return mp4s[0] if mp4s else None
    # повертаємо перший кандидат
    return candidates[0]
