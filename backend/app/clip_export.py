import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.models import TagDefinition, TagEvent, TagMode, Video

ExportMode = Literal["segments", "concatenate", "exclude"]


@dataclass
class ClipSegment:
    index: int
    start_seconds: float
    end_seconds: float
    label: str
    source_event_id: int | None
    start_frame: int | None
    end_frame: int | None

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end_seconds - self.start_seconds)


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "clip"


def merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda item: item[0])
    merged: list[list[float]] = [[ordered[0][0], ordered[0][1]]]
    for start, end in ordered[1:]:
        if start > merged[-1][1]:
            merged.append([start, end])
            continue
        merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def build_tag_segments(
    video: Video,
    tag: TagDefinition,
    events: list[TagEvent],
    *,
    pre_roll_seconds: float = 0.0,
    post_roll_seconds: float = 0.0,
) -> list[ClipSegment]:
    duration_limit = video.duration_seconds
    segments: list[ClipSegment] = []
    for index, event in enumerate(events, start=1):
        if event.tag_definition_id != tag.id:
            continue
        start_seconds = max(0.0, event.start_seconds - pre_roll_seconds)
        if tag.mode == TagMode.instant:
            end_seconds = event.start_seconds + post_roll_seconds
        else:
            if event.end_seconds is None:
                continue
            end_seconds = event.end_seconds + post_roll_seconds
        if duration_limit is not None:
            end_seconds = min(end_seconds, duration_limit)
        if end_seconds <= start_seconds:
            continue
        end_frame = int(round(end_seconds * video.fps)) if video.fps is not None else None
        segments.append(
            ClipSegment(
                index=index,
                start_seconds=round(start_seconds, 3),
                end_seconds=round(end_seconds, 3),
                label=tag.name,
                source_event_id=event.id,
                start_frame=event.start_frame,
                end_frame=end_frame,
            )
        )
    return segments


def build_exclusion_segments(video: Video, tag: TagDefinition, events: list[TagEvent]) -> list[ClipSegment]:
    if video.duration_seconds is None:
        raise ValueError("Video duration is required for exclusion exports")
    excluded = [
        (event.start_seconds, min(event.end_seconds, video.duration_seconds))
        for event in events
        if event.tag_definition_id == tag.id and event.end_seconds is not None and event.end_seconds > event.start_seconds
    ]
    merged = merge_intervals(excluded)
    keep_segments: list[ClipSegment] = []
    cursor = 0.0
    index = 1
    for start, end in merged:
        if start > cursor:
            keep_segments.append(
                ClipSegment(
                    index=index,
                    start_seconds=round(cursor, 3),
                    end_seconds=round(start, 3),
                    label=f"not-{tag.name}",
                    source_event_id=None,
                    start_frame=int(round(cursor * video.fps)) if video.fps is not None else None,
                    end_frame=int(round(start * video.fps)) if video.fps is not None else None,
                )
            )
            index += 1
        cursor = max(cursor, end)
    if cursor < video.duration_seconds:
        keep_segments.append(
            ClipSegment(
                index=index,
                start_seconds=round(cursor, 3),
                end_seconds=round(video.duration_seconds, 3),
                label=f"not-{tag.name}",
                source_event_id=None,
                start_frame=int(round(cursor * video.fps)) if video.fps is not None else None,
                end_frame=int(round(video.duration_seconds * video.fps)) if video.fps is not None else None,
            )
        )
    return [segment for segment in keep_segments if segment.duration_seconds > 0]


def export_segment(source_path: Path, output_path: Path, ffmpeg_path: Path, segment: ClipSegment) -> None:
    command = [
        str(ffmpeg_path),
        "-y",
        "-ss",
        str(segment.start_seconds),
        "-to",
        str(segment.end_seconds),
        "-i",
        str(source_path),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
import subprocess
from pathlib import Path


def _escape_concat_path(path: Path) -> str:
    """
    Escapa rutas para el concat demuxer de FFmpeg.
    Formato esperado:
    file '/absolute/path/video.mp4'
    """
    resolved = path.resolve().as_posix()
    escaped = resolved.replace("'", r"'\''")
    return f"file '{escaped}'"


def concatenate_segments(
    segment_paths: list[Path],
    output_path: Path,
    ffmpeg_path: Path,
    working_dir: Path
) -> None:
    if not segment_paths:
        raise ValueError("No segment paths provided")

    for path in segment_paths:
        if not path.exists():
            raise FileNotFoundError(f"Segment file not found: {path}")
        if path.stat().st_size == 0:
            raise ValueError(f"Segment file is empty: {path}")

    working_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    working_dir = working_dir.resolve()
    output_path = output_path.resolve()
    ffmpeg_path = ffmpeg_path.resolve()

    concat_file = (working_dir / "concat.txt").resolve()

    concat_content = "\n".join(
        _escape_concat_path(path)
        for path in segment_paths
    )

    concat_file.write_text(concat_content + "\n", encoding="utf-8")

    # 1) Intento rápido: concat sin recodificar
    command_copy = [
        str(ffmpeg_path),
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-fflags", "+genpts",
        "-i", concat_file.as_posix(),
        "-c", "copy",
        "-movflags", "+faststart",
        str(output_path),
    ]

    result = subprocess.run(
        command_copy,
        capture_output=True,
        text=True,
        cwd=str(working_dir)
    )

    if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
        return

    # 2) Fallback fiable: recodificar todo
    command_reencode = [
        str(ffmpeg_path),
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-fflags", "+genpts",
        "-i", str(concat_file),

        "-map", "0:v:0",
        "-map", "0:a?",

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "192k",

        "-movflags", "+faststart",
        str(output_path),
    ]

    result = subprocess.run(
        command_reencode,
        capture_output=True,
        text=True,
        cwd=str(working_dir)
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg concat failed.\n\n"
            f"Concat file:\n{concat_file}\n\n"
            f"Concat content:\n{concat_content}\n\n"
            f"Command copy stderr:\n{result.stderr}"
        )

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("FFmpeg finished but output file was not created or is empty")
def write_manifest(export_dir: Path, payload: dict) -> Path:
    manifest_path = export_dir / "manifest.json"
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest_path
