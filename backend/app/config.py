from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Etiquetador"

    # Data layer
    # Local/dev default remains SQLite. Production should set a PostgreSQL URL, for example:
    # postgresql+psycopg://etiquetador_user:password@postgres-main:5432/etiquetador
    database_url: str = "sqlite:///./etiquetador.db"
    db_pool_pre_ping: bool = True

    # Storage
    # In Docker production these paths should be mounted to a persistent host directory.
    video_storage_dir: Path = Path("storage/videos")
    video_library_dir: Path = Path("../videos")
    clip_exports_dir: Path = Path("storage/clip_exports")

    # Frontend/API access
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Production auth through Supabase JWTs. Keep disabled locally until Supabase is configured.
    auth_enabled: bool = False
    supabase_url: str | None = None
    supabase_jwks_url: str | None = None
    supabase_jwt_audience: str | None = None
    admin_emails: list[str] = []

    # Media tools
    ffmpeg_path: Path = Path(r"C:\Users\afer\Desktop\ANDER\ffmpeg-2026-03-12\bin\ffmpeg.exe")
    ffprobe_path: Path = Path(r"C:\Users\afer\Desktop\ANDER\ffmpeg-2026-03-12\bin\ffprobe.exe")

    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
