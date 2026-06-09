from datetime import datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.clip_export import (
    ClipSegment,
    build_exclusion_segments,
    build_tag_segments,
    concatenate_segments,
    export_segment,
    slugify,
    write_manifest,
)
from app.config import get_settings
from app.database import Base, engine, get_db
from app.models import TagDefinition, TagEvent, TagMode, Video, VideoStatus
from app.schemas import (
    AntagonisticPairCreate,
    AntagonisticPairRead,
    AntagonisticPairUpdate,
    ClipExportPlanRead,
    ClipExportRequest,
    ClipExportResultRead,
    ClipSegmentRead,
    TagDefinitionCreate,
    TagDefinitionRead,
    TagDefinitionUpdate,
    TagEventCreate,
    TagEventRead,
    TagEventUpdate,
    VideoLibraryItemRead,
    VideoRead,
    VideoUpdate,
)
from app.video_probe import probe_video_metadata

settings = get_settings()

clip_export_tasks: dict[int, dict] = {}
DEFAULT_TAG_COLORS = [
    "#2563eb",
    "#16a34a",
    "#dc2626",
    "#d97706",
    "#7c3aed",
    "#0891b2",
    "#db2777",
    "#65a30d",
    "#ea580c",
    "#0f766e",
]
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    settings.video_storage_dir.mkdir(parents=True, exist_ok=True)
    settings.video_library_dir.mkdir(parents=True, exist_ok=True)
    settings.clip_exports_dir.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def get_active_video(db: Session) -> Video | None:
    return db.scalar(select(Video).where(Video.status == VideoStatus.active).order_by(Video.created_at.desc()))


def set_active_video(db: Session, target_video: Video) -> Video:
    active_video = get_active_video(db)
    if active_video is not None and active_video.id != target_video.id:
        active_video.status = VideoStatus.idle
    target_video.status = VideoStatus.active
    target_video.completed_at = None
    db.commit()
    db.refresh(target_video)
    return target_video


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


def calculate_labeled_percent(db: Session, video: Video) -> float:
    if not video.duration_seconds or video.duration_seconds <= 0:
        return 0
    events = db.scalars(select(TagEvent).where(TagEvent.video_id == video.id).order_by(TagEvent.start_seconds)).all()
    intervals: list[tuple[float, float]] = []
    for event in events:
        if event.end_seconds is None or event.end_seconds <= event.start_seconds:
            continue
        intervals.append((event.start_seconds, min(event.end_seconds, video.duration_seconds)))
    if not intervals:
        return 0
    merged: list[list[float]] = []
    for start, end in intervals:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
            continue
        merged[-1][1] = max(merged[-1][1], end)
    labeled_seconds = sum(end - start for start, end in merged)
    return round(min(100.0, max(0.0, (labeled_seconds / video.duration_seconds) * 100)), 1)


def sync_library_videos(db: Session) -> None:
    known_paths = {Path(video.storage_path).resolve(): video for video in db.scalars(select(Video)).all()}
    for path in sorted(settings.video_library_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        resolved = path.resolve()
        if resolved in known_paths:
            continue
        metadata = probe_video_metadata(resolved, settings.ffprobe_path)
        db.add(
            Video(
                original_filename=path.name,
                stored_filename=f"{uuid5(NAMESPACE_URL, str(resolved)).hex}{path.suffix.lower()}",
                display_name=path.stem,
                storage_path=str(resolved),
                duration_seconds=metadata["duration_seconds"],
                fps=metadata["fps"],
                width=metadata["width"],
                height=metadata["height"],
                status=VideoStatus.idle,
            )
        )
    db.commit()


def serialize_video_item(db: Session, video: Video) -> VideoLibraryItemRead:
    event_count = db.query(TagEvent).where(TagEvent.video_id == video.id).count()
    payload = VideoRead.model_validate(video).model_dump()
    payload["file_exists"] = resolve_video_path(video).exists()
    payload["event_count"] = event_count
    payload["labeled_percent"] = calculate_labeled_percent(db, video)
    return VideoLibraryItemRead.model_validate(payload)


def ensure_tag_exists(db: Session, tag_definition_id: int) -> TagDefinition:
    tag = db.get(TagDefinition, tag_definition_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return tag


def ensure_video_exists(db: Session, video_id: int) -> Video:
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


def normalize_shortcut_key(shortcut_key: str | None) -> str | None:
    return shortcut_key.strip().lower() if shortcut_key else None


def build_clip_plan(video: Video, tag: TagDefinition, events: list[TagEvent], payload: ClipExportRequest) -> ClipExportPlanRead:
    if payload.export_mode == "exclude":
        segments = build_exclusion_segments(video, tag, events)
    else:
        segments = build_tag_segments(
            video,
            tag,
            events,
            pre_roll_seconds=payload.pre_roll_seconds,
            post_roll_seconds=payload.post_roll_seconds,
        )
    output_label = payload.output_label or tag.name
    return ClipExportPlanRead(
        video_id=video.id,
        tag_definition_id=tag.id,
        export_mode=payload.export_mode,
        output_label=output_label,
        segment_count=len(segments),
        segments=[
            ClipSegmentRead(
                index=segment.index,
                start_seconds=segment.start_seconds,
                end_seconds=segment.end_seconds,
                duration_seconds=segment.duration_seconds,
                label=segment.label,
                source_event_id=segment.source_event_id,
                start_frame=segment.start_frame,
                end_frame=segment.end_frame,
            )
            for segment in segments
        ],
    )


def suggest_color(db: Session, excluded_tag_ids: set[int] | None = None, group_key: str | None = None) -> str:
    excluded_tag_ids = excluded_tag_ids or set()
    active_tags = db.scalars(select(TagDefinition).where(TagDefinition.is_active.is_(True))).all()
    used_colors = {
        tag.color.lower()
        for tag in active_tags
        if tag.id not in excluded_tag_ids and not (group_key and tag.group_key == group_key and tag.mode == TagMode.antagonistic)
    }
    for color in DEFAULT_TAG_COLORS:
        if color.lower() not in used_colors:
            return color
    return DEFAULT_TAG_COLORS[0]


def assert_color_available(
    db: Session,
    color: str,
    *,
    excluded_tag_ids: set[int] | None = None,
    group_key: str | None = None,
) -> None:
    statement = select(TagDefinition).where(TagDefinition.is_active.is_(True), TagDefinition.color == color)
    conflicting_tags = db.scalars(statement).all()
    for conflicting_tag in conflicting_tags:
        if excluded_tag_ids and conflicting_tag.id in excluded_tag_ids:
            continue
        if group_key and conflicting_tag.group_key == group_key and conflicting_tag.mode == TagMode.antagonistic:
            continue
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Tag color already in use", "suggested_color": suggest_color(db, excluded_tag_ids, group_key)},
        )


def close_open_antagonistic_events(
    db: Session,
    video_id: int,
    selected_tag_id: int,
    selected_group_key: str | None,
    end_seconds: float,
) -> list[int]:
    if not selected_group_key:
        return []
    statement = (
        select(TagEvent)
        .join(TagDefinition, TagDefinition.id == TagEvent.tag_definition_id)
        .where(
            TagEvent.video_id == video_id,
            TagEvent.end_seconds.is_(None),
            TagDefinition.mode == TagMode.antagonistic,
            TagDefinition.group_key == selected_group_key,
            TagEvent.tag_definition_id != selected_tag_id,
        )
    )
    open_events = db.scalars(statement).all()
    for event in open_events:
        event.end_seconds = max(end_seconds, event.start_seconds)
    return [event.id for event in open_events]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/current-video", response_model=VideoRead | None)
def read_current_video(db: Session = Depends(get_db)):
    return get_active_video(db)


@app.get("/api/videos", response_model=list[VideoLibraryItemRead])
def list_videos(db: Session = Depends(get_db)):
    sync_library_videos(db)
    videos = db.scalars(select(Video).order_by(Video.updated_at.desc(), Video.created_at.desc())).all()
    return [serialize_video_item(db, video) for video in videos]


@app.post("/api/videos/sync", status_code=status.HTTP_204_NO_CONTENT)
def sync_videos(db: Session = Depends(get_db)):
    sync_library_videos(db)


@app.post("/api/videos", response_model=VideoRead, status_code=status.HTTP_201_CREATED)
def upload_video(
    file: UploadFile = File(...),
    display_name: str | None = Form(default=None),
    finish_current: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    active_video = get_active_video(db)
    if active_video is not None:
        active_video.status = VideoStatus.completed if finish_current else VideoStatus.idle
        active_video.completed_at = datetime.utcnow() if finish_current else None

    suffix = Path(file.filename or "video").suffix
    stored_filename = f"{uuid4().hex}{suffix}"
    storage_path = settings.video_storage_dir / stored_filename
    settings.video_storage_dir.mkdir(parents=True, exist_ok=True)

    with storage_path.open("wb") as destination:
        while chunk := file.file.read(1024 * 1024):
            destination.write(chunk)
    metadata = probe_video_metadata(storage_path, settings.ffprobe_path)

    video = Video(
        original_filename=file.filename or stored_filename,
        stored_filename=stored_filename,
        display_name=display_name or Path(file.filename or stored_filename).stem,
        storage_path=str(storage_path),
        duration_seconds=metadata["duration_seconds"],
        fps=metadata["fps"],
        width=metadata["width"],
        height=metadata["height"],
        status=VideoStatus.active,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@app.patch("/api/videos/{video_id}", response_model=VideoRead)
def update_video(video_id: int, payload: VideoUpdate, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    if payload.display_name is not None:
        video.display_name = payload.display_name
    if payload.status is not None:
        if payload.status == VideoStatus.active:
            return set_active_video(db, video)
        video.status = payload.status
        video.completed_at = datetime.utcnow() if payload.status == VideoStatus.completed else None
        if payload.status == VideoStatus.idle:
            video.completed_at = None
    db.commit()
    db.refresh(video)
    return video


@app.get("/api/videos/{video_id}/stream")
def stream_video(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    path = resolve_video_path(video)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found")
    return FileResponse(path)


@app.get("/api/tags", response_model=list[TagDefinitionRead])
def list_tags(include_inactive: bool = False, db: Session = Depends(get_db)):
    statement = select(TagDefinition).order_by(TagDefinition.sort_order, TagDefinition.name)
    if not include_inactive:
        statement = statement.where(TagDefinition.is_active.is_(True))
    return db.scalars(statement).all()


@app.post("/api/tags", response_model=TagDefinitionRead, status_code=status.HTTP_201_CREATED)
def create_tag(payload: TagDefinitionCreate, db: Session = Depends(get_db)):
    values = payload.model_dump()
    values["shortcut_key"] = normalize_shortcut_key(values.get("shortcut_key"))
    assert_color_available(db, values["color"])
    tag = TagDefinition(**values)
    db.add(tag)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag name already exists") from exc
    db.refresh(tag)
    return tag


@app.post("/api/antagonistic-pairs", response_model=AntagonisticPairRead, status_code=status.HTTP_201_CREATED)
def create_antagonistic_pair(payload: AntagonisticPairCreate, db: Session = Depends(get_db)):
    group_key = uuid4().hex
    shortcut_key = normalize_shortcut_key(payload.shortcut_key)
    assert_color_available(db, payload.first_color, group_key=group_key)
    assert_color_available(db, payload.second_color, group_key=group_key)
    first_tag = TagDefinition(
        name=payload.first_name,
        color=payload.first_color,
        mode=TagMode.antagonistic,
        group_key=group_key,
        shortcut_key=shortcut_key,
        sort_order=payload.sort_order,
    )
    second_tag = TagDefinition(
        name=payload.second_name,
        color=payload.second_color,
        mode=TagMode.antagonistic,
        group_key=group_key,
        shortcut_key=shortcut_key,
        sort_order=payload.sort_order,
    )
    db.add_all([first_tag, second_tag])
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag name already exists") from exc
    db.refresh(first_tag)
    db.refresh(second_tag)
    return AntagonisticPairRead(group_key=group_key, shortcut_key=shortcut_key, tags=[first_tag, second_tag])


@app.patch("/api/antagonistic-pairs/{group_key}", response_model=AntagonisticPairRead)
def update_antagonistic_pair(group_key: str, payload: AntagonisticPairUpdate, db: Session = Depends(get_db)):
    tags = db.scalars(
        select(TagDefinition).where(TagDefinition.group_key == group_key, TagDefinition.mode == TagMode.antagonistic).order_by(TagDefinition.id)
    ).all()
    if len(tags) != 2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Antagonistic pair not found")
    if payload.first_color is not None:
        assert_color_available(db, payload.first_color, excluded_tag_ids={tags[0].id}, group_key=group_key)
        tags[0].color = payload.first_color
    if payload.second_color is not None:
        assert_color_available(db, payload.second_color, excluded_tag_ids={tags[1].id}, group_key=group_key)
        tags[1].color = payload.second_color
    if tags[0].color.lower() == tags[1].color.lower():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Antagonistic pair colors must be different")
    if payload.shortcut_key is not None:
        normalized_shortcut = normalize_shortcut_key(payload.shortcut_key)
        for tag in tags:
            tag.shortcut_key = normalized_shortcut
    if payload.first_name is not None:
        tags[0].name = payload.first_name
    if payload.second_name is not None:
        tags[1].name = payload.second_name
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag name already exists") from exc
    for tag in tags:
        db.refresh(tag)
    return AntagonisticPairRead(group_key=group_key, shortcut_key=tags[0].shortcut_key, tags=tags)


@app.patch("/api/tags/{tag_id}", response_model=TagDefinitionRead)
def update_tag(tag_id: int, payload: TagDefinitionUpdate, db: Session = Depends(get_db)):
    tag = db.get(TagDefinition, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "shortcut_key":
            value = normalize_shortcut_key(value)
        setattr(tag, key, value)
    if payload.color is not None:
        assert_color_available(db, tag.color, excluded_tag_ids={tag.id}, group_key=tag.group_key)
    if tag.mode == TagMode.antagonistic and not tag.group_key:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="group_key is required for antagonistic tags")
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag name already exists") from exc
    db.refresh(tag)
    return tag


@app.delete("/api/tags/{tag_id}", response_model=TagDefinitionRead)
def deactivate_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.get(TagDefinition, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    tag.is_active = False
    db.commit()
    db.refresh(tag)
    return tag


@app.get("/api/videos/{video_id}/events", response_model=list[TagEventRead])
def list_events(video_id: int, db: Session = Depends(get_db)):
    statement = (
        select(TagEvent)
        .options(selectinload(TagEvent.tag))
        .where(TagEvent.video_id == video_id)
        .order_by(TagEvent.start_seconds, TagEvent.created_at)
    )
    return db.scalars(statement).all()


@app.post("/api/videos/{video_id}/clip-plan", response_model=ClipExportPlanRead)
def preview_clip_plan(video_id: int, payload: ClipExportRequest, db: Session = Depends(get_db)):
    video = ensure_video_exists(db, video_id)
    tag = ensure_tag_exists(db, payload.tag_definition_id)
    events = db.scalars(select(TagEvent).where(TagEvent.video_id == video_id).order_by(TagEvent.start_seconds)).all()
    return build_clip_plan(video, tag, events, payload)


@app.post("/api/videos/{video_id}/clip-export")
def export_clips(video_id: int, payload: ClipExportRequest, db: Session = Depends(get_db)):
    video = ensure_video_exists(db, video_id)
    tag = ensure_tag_exists(db, payload.tag_definition_id)
    source_path = resolve_video_path(video)
    if not source_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found")

    events = db.scalars(select(TagEvent).where(TagEvent.video_id == video_id).order_by(TagEvent.start_seconds)).all()
    plan = build_clip_plan(video, tag, events, payload)
    if plan.segment_count == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No exportable segments found for this tag")

    task_id = video_id * 10000 + len(clip_export_tasks)
    clip_export_tasks[task_id] = {
        "status": "running",
        "current": 0,
        "total": plan.segment_count,
        "stage": "Preparando...",
        "result": None,
        "error": None,
    }

    def run_export():
        try:
            export_root = settings.clip_exports_dir / slugify(video.display_name) / f"{slugify(plan.output_label)}-{payload.export_mode}"
            export_root.mkdir(parents=True, exist_ok=True)

            output_files: list[str] = []
            segment_paths: list[Path] = []
            for i, segment in enumerate(plan.segments):
                clip_export_tasks[task_id]["stage"] = f"Exportando clip {i + 1}/{plan.segment_count}"
                clip_export_tasks[task_id]["current"] = i + 1
                filename = f"{segment.index:03d}_{slugify(segment.label)}_{segment.start_seconds:.3f}_{segment.end_seconds:.3f}.mp4"
                output_path = export_root / filename
                export_segment(
                    source_path,
                    output_path,
                    settings.ffmpeg_path,
                    ClipSegment(
                        index=segment.index,
                        start_seconds=segment.start_seconds,
                        end_seconds=segment.end_seconds,
                        label=segment.label,
                        source_event_id=segment.source_event_id,
                        start_frame=segment.start_frame,
                        end_frame=segment.end_frame,
                    ),
                )
                output_files.append(str(output_path))
                segment_paths.append(output_path)

            if payload.export_mode == "concatenate" and segment_paths:
                clip_export_tasks[task_id]["stage"] = "Concatenando clips..."
                clip_export_tasks[task_id]["current"] = plan.segment_count
                concat_output = export_root / f"{slugify(plan.output_label)}_concat.mp4"
                concatenate_segments(segment_paths, concat_output, settings.ffmpeg_path, export_root)
                output_files.append(str(concat_output))
                if not payload.keep_segments:
                    for segment_path in segment_paths:
                        segment_path.unlink(missing_ok=True)

            manifest_path = write_manifest(
                export_root,
                {
                    "video_id": plan.video_id,
                    "video_name": video.display_name,
                    "tag_definition_id": plan.tag_definition_id,
                    "tag_name": tag.name,
                    "export_mode": plan.export_mode,
                    "output_label": plan.output_label,
                    "segment_count": plan.segment_count,
                    "segments": [segment.model_dump() for segment in plan.segments],
                    "output_files": output_files,
                },
            )

            result = ClipExportResultRead(
                **plan.model_dump(),
                export_dir=str(export_root),
                manifest_path=str(manifest_path),
                output_files=output_files,
            )
            clip_export_tasks[task_id]["status"] = "completed"
            clip_export_tasks[task_id]["stage"] = "Completado"
            clip_export_tasks[task_id]["result"] = result.model_dump()
        except Exception as exc:
            clip_export_tasks[task_id]["status"] = "failed"
            clip_export_tasks[task_id]["error"] = str(exc)

    import threading
    thread = threading.Thread(target=run_export)
    thread.start()

    return {"task_id": task_id, "status": "started"}


@app.get("/api/videos/{video_id}/clip-export/{task_id}")
def get_clip_export_progress(video_id: int, task_id: int):
    if task_id not in clip_export_tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return clip_export_tasks[task_id]


@app.post("/api/videos/{video_id}/events", response_model=TagEventRead, status_code=status.HTTP_201_CREATED)
def create_event(video_id: int, payload: TagEventCreate, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    tag = ensure_tag_exists(db, payload.tag_definition_id)
    values = payload.model_dump()
    if values.get("start_frame") is None and video.fps is not None:
        values["start_frame"] = int(round(values["start_seconds"] * video.fps))
    if tag.mode == TagMode.antagonistic:
        close_open_antagonistic_events(db, video_id, tag.id, tag.group_key, values["start_seconds"])
    event = TagEvent(video_id=video_id, **values)
    db.add(event)
    db.commit()
    db.refresh(event)
    return db.scalar(select(TagEvent).options(selectinload(TagEvent.tag)).where(TagEvent.id == event.id))


@app.patch("/api/events/{event_id}", response_model=TagEventRead)
def update_event(event_id: int, payload: TagEventUpdate, db: Session = Depends(get_db)):
    event = db.get(TagEvent, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    values = payload.model_dump(exclude_unset=True)
    if "tag_definition_id" in values:
        ensure_tag_exists(db, values["tag_definition_id"])
    start_seconds = values.get("start_seconds", event.start_seconds)
    end_seconds = values.get("end_seconds", event.end_seconds)
    if end_seconds is not None and end_seconds < start_seconds:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_seconds must be >= start_seconds")
    for key, value in values.items():
        setattr(event, key, value)
    db.commit()
    return db.scalar(select(TagEvent).options(selectinload(TagEvent.tag)).where(TagEvent.id == event.id))


@app.delete("/api/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(TagEvent, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    db.delete(event)
    db.commit()


@app.delete("/api/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    db.delete(video)
    db.commit()
