from pathlib import Path
import json
import subprocess

import pytest

from app.config import get_settings


def test_final_coruna_vs_estudiantes_mp4_is_mpegts_container():
    settings = get_settings()
    video_path = Path(__file__).resolve().parents[2] / "videos" / "FinalCorunavsEstudiantes.mp4"

    if not video_path.exists():
        pytest.skip(f"Test video not found: {video_path}")
    if not settings.ffprobe_path.exists():
        pytest.skip(f"ffprobe not found: {settings.ffprobe_path}")

    result = subprocess.run(
        [
            str(settings.ffprobe_path),
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    video_stream = next(stream for stream in payload["streams"] if stream["codec_type"] == "video")
    audio_stream = next(stream for stream in payload["streams"] if stream["codec_type"] == "audio")

    assert payload["format"]["format_name"] == "mpegts"
    assert float(payload["format"]["duration"]) == pytest.approx(10313.340856)
    assert video_stream["codec_name"] == "h264"
    assert audio_stream["codec_name"] == "aac"
