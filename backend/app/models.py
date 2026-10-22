from datetime import date, datetime
from enum import Enum

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VideoStatus(str, Enum):
    active = "active"
    idle = "idle"
    completed = "completed"


class TagMode(str, Enum):
    instant = "instant"
    range = "range"
    antagonistic = "antagonistic"


class TagSource(str, Enum):
    human = "human"
    system = "system"


class DownloadStatus(str, Enum):
    pending = "pending"
    downloading = "downloading"
    completed = "completed"
    failed = "failed"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    codec_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    container_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bit_rate: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    game_format: Mapped[str | None] = mapped_column(String(30), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    match_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    competition: Mapped[str | None] = mapped_column(String(150), nullable=True)
    home_team: Mapped[str | None] = mapped_column(String(120), nullable=True)
    away_team: Mapped[str | None] = mapped_column(String(120), nullable=True)
    match_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    details_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[VideoStatus] = mapped_column(SAEnum(VideoStatus), default=VideoStatus.active, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    events: Mapped[list["TagEvent"]] = relationship(back_populates="video", cascade="all, delete-orphan")


class TagDefinition(Base):
    __tablename__ = "tag_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="#2563eb")
    mode: Mapped[TagMode] = mapped_column(SAEnum(TagMode), default=TagMode.range, nullable=False)
    source: Mapped[TagSource] = mapped_column(SAEnum(TagSource), default=TagSource.human, nullable=False)
    group_key: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    shortcut_key: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    events: Mapped[list["TagEvent"]] = relationship(back_populates="tag")


class TagEvent(Base):
    __tablename__ = "tag_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), nullable=False, index=True)
    tag_definition_id: Mapped[int] = mapped_column(ForeignKey("tag_definitions.id"), nullable=False, index=True)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    start_frame: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[TagSource] = mapped_column(SAEnum(TagSource), default=TagSource.human, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    video: Mapped[Video] = relationship(back_populates="events")
    tag: Mapped[TagDefinition] = relationship(back_populates="events")


class DownloadHistory(Base):
    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quality: Mapped[str] = mapped_column(String(20), nullable=False)
    download_format: Mapped[str] = mapped_column(String(20), nullable=False)
    output_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[DownloadStatus] = mapped_column(SAEnum(DownloadStatus), default=DownloadStatus.pending, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
