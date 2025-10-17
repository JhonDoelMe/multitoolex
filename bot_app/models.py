# bot_app/models.py
from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    String,
    Text,
    Integer,
    DateTime,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .db import Base


# ------------------------------------------------------------
# Enums
# ------------------------------------------------------------
class DownloadStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"


# ------------------------------------------------------------
# Models
# ------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # relationships
    downloads: Mapped[List["Download"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id}>"


class Download(Base):
    __tablename__ = "downloads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[DownloadStatus] = mapped_column(
        Enum(DownloadStatus, name="download_status"),
        default=DownloadStatus.pending,
        nullable=False,
        index=True,
    )

    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # relationships
    user: Mapped["User"] = relationship(back_populates="downloads", lazy="joined")

    def __repr__(self) -> str:
        return f"<Download id={self.id} status={self.status} url={self.url[:30]}...>"
