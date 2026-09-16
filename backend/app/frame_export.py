import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.clip_export import ClipSegment


@dataclass(frozen=True)
class FrameRecord:
    segment_index: int
    sample_index: int
    source_time_seconds: float
    source_frame: int | None
    source_event_id: int | None
    file_path: Path


def estimate_segment_frames(segment: ClipSegment, sample_fps: float) -> int:
    if sample_fps <= 0:
        raise ValueError("sample_fps must be greater than 0")
    return max(0, math.ceil(segment.duration_seconds * sample_fps - 1e-9))


def format_timecode(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


def extract_segment_frames(
    source_path: Path,
    output_dir: Path,
    ffmpeg_path: Path,
    segment: ClipSegment,
    *,
    sample_fps: float,
    source_fps: float | None,
    image_format: str = "jpg",
    jpeg_quality: int = 2,
) -> list[FrameRecord]:
    if sample_fps <= 0:
        raise ValueError("sample_fps must be greater than 0")
    if image_format not in {"jpg", "png"}:
        raise ValueError("image_format must be 'jpg' or 'png'")
    if not source_path.exists():
        raise FileNotFoundError(f"Source video not found: {source_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    pattern = output_dir / f"segment_{segment.index:04d}_%06d.{image_format}"
    duration = segment.duration_seconds
    if duration <= 0:
        return []

    command = [
        str(ffmpeg_path),
        "-y",
        "-ss",
        f"{segment.start_seconds:.6f}",
        "-i",
        str(source_path),
        "-t",
        f"{duration:.6f}",
        "-vf",
        f"fps={sample_fps}",
        "-an",
    ]
    if image_format == "jpg":
        command.extend(["-q:v", str(jpeg_quality)])
    command.append(str(pattern))

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg frame extraction failed: {result.stderr.strip()}")

    files = sorted(output_dir.glob(f"segment_{segment.index:04d}_*.{image_format}"))
    records: list[FrameRecord] = []
    interval = 1.0 / sample_fps
    for sample_index, file_path in enumerate(files, start=1):
        source_time = segment.start_seconds + (sample_index - 1) * interval
        source_time = min(source_time, max(segment.start_seconds, segment.end_seconds - 1e-6))
        source_time = round(source_time, 6)
        source_frame = int(round(source_time * source_fps)) if source_fps else None
        records.append(
            FrameRecord(
                segment_index=segment.index,
                sample_index=sample_index,
                source_time_seconds=source_time,
                source_frame=source_frame,
                source_event_id=segment.source_event_id,
                file_path=file_path,
            )
        )
    return records


def write_jsonl(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path
