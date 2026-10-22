import subprocess

import pytest

from app.clip_export import ClipSegment, concatenate_segments, export_segment
from app.config import get_settings


def test_ffmpeg_can_export_and_concatenate(tmp_path):
    settings = get_settings()
    if not settings.ffmpeg_path.is_file() or not settings.ffprobe_path.is_file():
        pytest.skip("FFmpeg/FFprobe not installed")

    source = tmp_path / "source.mp4"
    subprocess.run(
        [str(settings.ffmpeg_path), "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=320x180:r=25:d=3",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(source)],
        check=True,
    )

    paths = []
    for index, start, end in ((1, 0.0, 1.0), (2, 1.0, 2.0)):
        path = tmp_path / f"clip-{index}.mp4"
        export_segment(source, path, settings.ffmpeg_path, ClipSegment(index, start, end, "test", None, None, None))
        paths.append(path)

    joined = tmp_path / "joined.mp4"
    concatenate_segments(paths, joined, settings.ffmpeg_path, tmp_path)
    assert joined.is_file() and joined.stat().st_size > 0
    duration = subprocess.run(
        [str(settings.ffprobe_path), "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(joined)],
        check=True, capture_output=True, text=True,
    )
    assert float(duration.stdout) > 1.5
