from pathlib import Path

from app.clip_export import ClipSegment
from app.frame_export import estimate_segment_frames, format_timecode, write_jsonl
from app.main import app


def test_dataset_routes_are_registered():
    paths = {route.path for route in app.routes}
    assert "/api/datasets/videos/{video_id}/frame-plan" in paths
    assert "/api/datasets/videos/{video_id}/frame-export" in paths
    assert "/api/datasets/frame-export/{task_id}" in paths


def test_estimate_segment_frames():
    segment = ClipSegment(
        index=1,
        start_seconds=10.25,
        end_seconds=13.25,
        label="playing",
        source_event_id=7,
        start_frame=307,
        end_frame=397,
    )
    assert estimate_segment_frames(segment, 1.0) == 3
    assert estimate_segment_frames(segment, 5.0) == 15


def test_format_timecode():
    assert format_timecode(0) == "00:00:00.000"
    assert format_timecode(65.432) == "00:01:05.432"
    assert format_timecode(3661.125) == "01:01:01.125"


def test_write_jsonl(tmp_path: Path):
    target = tmp_path / "frames.jsonl"
    write_jsonl(target, [{"frame_id": "a", "label": "tiro"}, {"frame_id": "b", "label": "playing"}])
    assert target.read_text(encoding="utf-8").splitlines() == [
        '{"frame_id": "a", "label": "tiro"}',
        '{"frame_id": "b", "label": "playing"}',
    ]
