# bot_app/db.py
import os
import pathlib
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker, declarative_base

# ------------------------------------------------------------
# Base metadata (импортируется в bot_app/models.py)
# ------------------------------------------------------------
Base = declarative_base()

# ------------------------------------------------------------
# Конфигурация подключения
# Приоритет:
#   1) DATABASE_URL (например, postgres+psycopg://user:pass@host/dbname)
#   2) SQLITE_PATH  (например, ./data/local.db) -> собираем sqlite+aiosqlite:///
#   3) По умолчанию ./data/local.db
# ------------------------------------------------------------
def _build_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # если это sqlite без async-драйвера — подменим на aiosqlite
        if db_url.startswith("sqlite:///") or db_url.startswith("sqlite://"):
            # Нормализуем на async-драйвер
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
        return db_url

    # fallback: локальный sqlite
    sqlite_path = os.getenv("SQLITE_PATH", "./data/local.db")
    sqlite_path = str(pathlib.Path(sqlite_path).resolve())
    # гарантируем наличие директории
    pathlib.Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{sqlite_path}"


DATABASE_URL = _build_database_url()

# ------------------------------------------------------------
# Async engine / session factory
# ------------------------------------------------------------
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "0") == "1",
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal: sessionmaker = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# ------------------------------------------------------------
# Инициализация схемы
# ------------------------------------------------------------
async def init_db() -> None:
    """
    Создаёт таблицы при первом запуске.
    Важно: импортируем models, чтобы все маппинги были зарегистрированы в Base.metadata.
    """
    # Ленивая регистрация моделей
    from . import models  # noqa: F401  # регистрирует таблицы в Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ------------------------------------------------------------
# Контекстная выдача сессии (например, для FastAPI Depends)
# ------------------------------------------------------------
async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


# ------------------------------------------------------------
# Служебное: корректное закрытие пула
# ------------------------------------------------------------
async def dispose_engine() -> None:
    await engine.dispose()
