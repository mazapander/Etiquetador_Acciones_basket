from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Etiquetador"
    database_url: str = "sqlite:///./etiquetador.db"
    video_storage_dir: Path = Path("storage/videos")
    video_library_dir: Path = Path("../videos")
    clip_exports_dir: Path = Path("storage/clip_exports")
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    ffmpeg_path: Path = Path(r"C:\Users\afer\Desktop\ANDER\ffmpeg-2026-03-12\bin\ffmpeg.exe")
    ffprobe_path: Path = Path(r"C:\Users\afer\Desktop\ANDER\ffmpeg-2026-03-12\bin\ffprobe.exe")

    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
