import json
import threading
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.clip_export import ClipSegment, build_exclusion_segments, build_tag_segments, slugify
from app.config import get_settings
from app.database import get_db
from app.frame_export import estimate_segment_frames, extract_segment_frames, format_timecode, write_jsonl
from app.models import TagDefinition, TagEvent, TagMode, Video

router = APIRouter(prefix="/api/datasets", tags=["datasets"])
settings = get_settings()
frame_export_tasks: dict[str, dict[str, Any]] = {}


class FrameExportRequest(BaseModel):
    tag_definition_id: int
    export_mode: Literal["segments", "exclude"] = "segments"
    sample_fps: float = Field(default=1.0, gt=0, le=60)
    pre_roll_seconds: float = Field(default=0, ge=0)
    post_roll_seconds: float = Field(default=0, ge=0)
    output_label: str | None = Field(default=None, min_length=1, max_length=120)
    image_format: Literal["jpg", "png"] = "jpg"
    jpeg_quality: int = Field(default=2, ge=1, le=31)
    split: Literal["pool", "train", "val", "test"] = "pool"
    game_metadata: dict[str, Any] = Field(default_factory=dict)


def resolve_video_path(video: Video) -> Path:
    direct_path = Path(video.storage_path)
    if direct_path.exists():
        return direct_path
    library_candidate = settings.video_library_dir / video.original_filename
    if library_candidate.exists():
        return library_candidate
    storage_candidate = settings.video_storage_dir / video.stored_filename
    if storage_candidate.exists():
        return storage_candidate
    return direct_path


def build_segments(video: Video, tag: TagDefinition, events: list[TagEvent], payload: FrameExportRequest) -> list[ClipSegment]:
    if payload.export_mode == "exclude":
        return build_exclusion_segments(video, tag, events)
    return build_tag_segments(
        video,
        tag,
        events,
        pre_roll_seconds=payload.pre_roll_seconds,
        post_roll_seconds=payload.post_roll_seconds,
    )


def snapshot_events(events: list[TagEvent]) -> list[dict[str, Any]]:
    return [
        {
            "id": event.id,
            "tag_definition_id": event.tag_definition_id,
            "tag_name": event.tag.name,
            "tag_mode": event.tag.mode.value,
            "start_seconds": event.start_seconds,
            "end_seconds": event.end_seconds,
        }
        for event in events
    ]


def labels_at_time(event_rows: list[dict[str, Any]], source_time: float, source_event_id: int | None) -> tuple[list[str], list[str]]:
    labels: set[str] = set()
    active_range_tags: set[str] = set()

    for event in event_rows:
        if event["id"] == source_event_id:
            labels.add(event["tag_name"])
        if event["tag_mode"] == TagMode.instant.value or event["end_seconds"] is None:
            continue
        if event["start_seconds"] <= source_time <= event["end_seconds"]:
            labels.add(event["tag_name"])
            active_range_tags.add(event["tag_name"])

    return sorted(labels), sorted(active_range_tags)


def serialize_segment(segment: ClipSegment) -> dict[str, Any]:
    return {
        "index": segment.index,
        "start_seconds": segment.start_seconds,
        "end_seconds": segment.end_seconds,
        "duration_seconds": segment.duration_seconds,
        "label": segment.label,
        "source_event_id": segment.source_event_id,
        "start_frame": segment.start_frame,
        "end_frame": segment.end_frame,
    }


@router.post("/videos/{video_id}/frame-plan")
def preview_frame_export(video_id: int, payload: FrameExportRequest, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    tag = db.get(TagDefinition, payload.tag_definition_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    events = db.scalars(
        select(TagEvent)
        .options(selectinload(TagEvent.tag))
        .where(TagEvent.video_id == video_id)
        .order_by(TagEvent.start_seconds)
    ).all()
    segments = build_segments(video, tag, events, payload)
    estimated_frame_count = sum(estimate_segment_frames(segment, payload.sample_fps) for segment in segments)

    return {
        "video_id": video.id,
        "video_name": video.display_name,
        "tag_definition_id": tag.id,
        "tag_name": tag.name,
        "export_mode": payload.export_mode,
        "sample_fps": payload.sample_fps,
        "split": payload.split,
        "segment_count": len(segments),
        "estimated_frame_count": estimated_frame_count,
        "segments": [serialize_segment(segment) for segment in segments],
    }


@router.post("/videos/{video_id}/frame-export")
def export_frames(video_id: int, payload: FrameExportRequest, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    tag = db.get(TagDefinition, payload.tag_definition_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    source_path = resolve_video_path(video)
    if not source_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found")

    events = db.scalars(
        select(TagEvent)
        .options(selectinload(TagEvent.tag))
        .where(TagEvent.video_id == video_id)
        .order_by(TagEvent.start_seconds)
    ).all()
    segments = build_segments(video, tag, events, payload)
    if not segments:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No exportable segments found for this tag")

    event_rows = snapshot_events(events)
    video_snapshot = {
        "id": video.id,
        "display_name": video.display_name,
        "original_filename": video.original_filename,
        "fps": video.fps,
        "width": video.width,
        "height": video.height,
        "duration_seconds": video.duration_seconds,
    }
    tag_snapshot = {"id": tag.id, "name": tag.name, "mode": tag.mode.value}
    output_label = payload.output_label or tag.name
    estimated_total = sum(estimate_segment_frames(segment, payload.sample_fps) for segment in segments)

    task_id = uuid4().hex
    frame_export_tasks[task_id] = {
        "status": "running",
        "current": 0,
        "total": estimated_total,
        "stage": "Preparando exportacion...",
        "result": None,
        "error": None,
    }

    def run_export() -> None:
        try:
            export_id = uuid4().hex[:8]
            export_root = (
                settings.clip_exports_dir
                / "_datasets"
                / slugify(video_snapshot["display_name"])
                / f"{slugify(output_label)}-{payload.split}-{export_id}"
            )
            frames_dir = export_root / "images"
            frames_dir.mkdir(parents=True, exist_ok=True)

            frame_rows: list[dict[str, Any]] = []
            for segment_number, segment in enumerate(segments, start=1):
                frame_export_tasks[task_id]["stage"] = f"Extrayendo segmento {segment_number}/{len(segments)}"
                records = extract_segment_frames(
                    source_path,
                    frames_dir,
                    settings.ffmpeg_path,
                    segment,
                    sample_fps=payload.sample_fps,
                    source_fps=video_snapshot["fps"],
                    image_format=payload.image_format,
                    jpeg_quality=payload.jpeg_quality,
                )
                for record in records:
                    labels, active_range_tags = labels_at_time(event_rows, record.source_time_seconds, record.source_event_id)
                    frame_id = f"v{video_snapshot['id']}_s{record.segment_index:04d}_f{record.sample_index:06d}"
                    frame_rows.append(
                        {
                            "frame_id": frame_id,
                            "file": str(record.file_path.relative_to(export_root)),
                            "video_id": video_snapshot["id"],
                            "game_id": payload.game_metadata.get("game_id", f"video-{video_snapshot['id']}"),
                            "video_name": video_snapshot["display_name"],
                            "original_filename": video_snapshot["original_filename"],
                            "source_time_seconds": record.source_time_seconds,
                            "source_timecode": format_timecode(record.source_time_seconds),
                            "source_frame": record.source_frame,
                            "source_event_id": record.source_event_id,
                            "segment_index": record.segment_index,
                            "sample_index": record.sample_index,
                            "sample_fps": payload.sample_fps,
                            "split": payload.split,
                            "selected_tag": tag_snapshot["name"],
                            "labels": labels,
                            "active_range_tags": active_range_tags,
                            "game_metadata": payload.game_metadata,
                        }
                    )
                frame_export_tasks[task_id]["current"] = len(frame_rows)

            jsonl_path = write_jsonl(export_root / "frames.jsonl", frame_rows)
            manifest = {
                "dataset_export_version": 1,
                "video": video_snapshot,
                "selected_tag": tag_snapshot,
                "export": {
                    "output_label": output_label,
                    "export_mode": payload.export_mode,
                    "sample_fps": payload.sample_fps,
                    "pre_roll_seconds": payload.pre_roll_seconds,
                    "post_roll_seconds": payload.post_roll_seconds,
                    "image_format": payload.image_format,
                    "split": payload.split,
                    "game_metadata": payload.game_metadata,
                },
                "segment_count": len(segments),
                "frame_count": len(frame_rows),
                "segments": [serialize_segment(segment) for segment in segments],
                "frames_manifest": str(jsonl_path.name),
            }
            manifest_path = export_root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

            result = {
                "export_dir": str(export_root),
                "manifest_path": str(manifest_path),
                "frames_manifest_path": str(jsonl_path),
                "frame_count": len(frame_rows),
                "segment_count": len(segments),
                "split": payload.split,
                "sample_fps": payload.sample_fps,
            }
            frame_export_tasks[task_id]["status"] = "completed"
            frame_export_tasks[task_id]["current"] = len(frame_rows)
            frame_export_tasks[task_id]["total"] = len(frame_rows)
            frame_export_tasks[task_id]["stage"] = "Completado"
            frame_export_tasks[task_id]["result"] = result
        except Exception as exc:
            frame_export_tasks[task_id]["status"] = "failed"
            frame_export_tasks[task_id]["error"] = str(exc)
            frame_export_tasks[task_id]["stage"] = "Error"

    threading.Thread(target=run_export, daemon=True).start()
    return {"task_id": task_id, "status": "started", "estimated_frame_count": estimated_total}


@router.get("/frame-export/{task_id}")
def get_frame_export_progress(task_id: str):
    task = frame_export_tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task
