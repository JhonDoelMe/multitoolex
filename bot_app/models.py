from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from .db import Base
import enum

class DownloadStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Download(Base):
    __tablename__ = "downloads"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    url = Column(Text, nullable=False)
    status = Column(Enum(DownloadStatus), default=DownloadStatus.pending, nullable=False)
    file_path = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
