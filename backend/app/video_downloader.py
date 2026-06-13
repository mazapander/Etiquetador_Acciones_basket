from pathlib import Path
from typing import Literal

import imageio_ffmpeg
import yt_dlp
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()

VideoQuality = Literal["best", "1080p", "720p", "480p", "360p", "audio_only"]
DownloadFormat = Literal["mp4", "mkv", "webm", "mp3", "wav"]


class VideoInfo(BaseModel):
    url: str
    title: str | None
    thumbnail: str | None
    duration: float | None
    description: str | None
    webpage_url: str | None
    playlist_title: str | None
    channel: str | None
    formats: list[dict]


class DownloadRequest(BaseModel):
    url: str
    quality: VideoQuality = "best"
    download_format: DownloadFormat = "mp4"
    output_name: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    video_title: str | None = None
    video_channel: str | None = None
    include_audio: bool = False


class DownloadProgress(BaseModel):
    status: Literal["downloading", "processing", "completed", "failed"] = "downloading"
    percent: float = 0
    speed: str | None = None
    eta: str | None = None
    stage: str = "Starting..."
    error: str | None = None
    output_path: str | None = None


def fetch_video_info(url: str) -> VideoInfo:
    ydl_opts = {
        "dumpjson": True,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info(url, download=False)
        if data is None:
            raise RuntimeError(f"yt-dlp failed to extract info from {url}")
        formats = data.get("formats", [])

        return VideoInfo(
            url=url,
            title=data.get("title"),
            thumbnail=data.get("thumbnail"),
            duration=data.get("duration"),
            description=data.get("description"),
            webpage_url=data.get("webpage_url"),
            playlist_title=data.get("playlist_title"),
            channel=data.get("channel") or data.get("uploader"),
            formats=formats,
        )


def build_ytdlp_format_string(quality: VideoQuality, download_format: DownloadFormat, include_audio: bool = False) -> str | None:
    if quality == "audio_only" or download_format in ("mp3", "wav"):
        return "bestaudio/best"

    merge_suffix = "+bestaudio/best" if include_audio else "/best"

    if quality == "best":
        return "bestvideo+bestaudio/best" if include_audio else "best"
    if quality == "1080p":
        return f"bestvideo[height<=1080]{merge_suffix}"
    if quality == "720p":
        return f"bestvideo[height<=720]{merge_suffix}"
    if quality == "480p":
        return f"bestvideo[height<=480]{merge_suffix}"
    if quality == "360p":
        return f"bestvideo[height<=360]{merge_suffix}"

    return "best"


def download_video(request: DownloadRequest, progress_callback=None) -> str:
    output_dir = settings.video_library_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    ext_map = {"mp4": "mp4", "mkv": "mkv", "webm": "webm", "mp3": "mp3", "wav": "wav"}
    auto_ext = ext_map.get(request.download_format, "mp4")

    if request.output_name:
        filename = request.output_name.strip()
        if filename:
            is_template = "%(title)s" in filename or "%(ext)s" in filename
            last_dot = filename.rfind(".")
            has_extension = last_dot > 0 and len(filename) - last_dot <= 5
            if not is_template and not has_extension:
                filename = filename + "." + auto_ext
    else:
        filename = "%(title)s.%(ext)s"

    output_template = str(output_dir / filename)
    format_string = build_ytdlp_format_string(request.quality, request.download_format, request.include_audio)

    ydl_opts: dict = {
        "outtmpl": output_template,
        "quiet": False,
        "no_warnings": False,
        "format": format_string,
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
    }

    if request.quality == "audio_only" or request.download_format in ("mp3", "wav"):
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": request.download_format if request.download_format in ("mp3", "wav") else "mp3",
        }]

    if request.start_time is not None and request.end_time is not None:
        ydl_opts["download_ranges"] = lambda info, ydl: [(request.start_time, request.end_time)]

    if progress_callback:
        last_progress = {"percent": 0}

        def progress_hook(progress: dict):
            if progress["status"] == "downloading":
                total = progress.get("total_bytes", 0) or progress.get("downloaded_bytes", 0) or 1
                downloaded = progress.get("downloaded_bytes", 0)
                percent = (downloaded / total) * 100 if total > 0 else 0
                if percent > last_progress["percent"]:
                    last_progress["percent"] = percent
                    progress_callback(DownloadProgress(
                        status="downloading",
                        percent=percent,
                        stage=f"Downloading... {progress.get('_speed_str', 'N/A')} - ETA: {progress.get('_eta_str', 'N/A')}",
                        speed=progress.get("_speed_str"),
                        eta=progress.get("_eta_str"),
                    ))
            elif progress["status"] == "finished":
                progress_callback(DownloadProgress(status="processing", percent=100, stage="Processing..."))

        ydl_opts["progress_hooks"] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])
    except Exception as exc:
        error_msg = str(exc)
        if progress_callback:
            progress_callback(DownloadProgress(status="failed", error=error_msg))
        raise RuntimeError(f"yt-dlp failed: {error_msg}")

    return str(output_dir)
