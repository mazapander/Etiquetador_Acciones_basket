from pathlib import Path
import time

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


def make_client(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    library_dir = tmp_path / "library"
    library_dir.mkdir()
    exports_dir = tmp_path / "exports"
    exports_dir.mkdir()
    monkeypatch.setattr("app.main.settings.video_storage_dir", storage_dir)
    monkeypatch.setattr("app.main.settings.video_library_dir", library_dir)
    monkeypatch.setattr("app.main.settings.clip_exports_dir", exports_dir)
    monkeypatch.setattr("app.main.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.main.probe_video_metadata", lambda path, ffprobe_path: {
        "duration_seconds": 12.5, "fps": 25.0, "width": 1920, "height": 1080,
        "format_name": "mp4", "codec_name": "h264", "bit_rate": 4_000_000, "size_bytes": path.stat().st_size,
    })
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_tag_lifecycle(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    response = client.post("/api/tags", json={"name": "Gol", "color": "#16a34a", "mode": "range", "shortcut_key": "g"})
    assert response.status_code == 201
    tag_id = response.json()["id"]
    assert response.json()["source"] == "human"
    assert response.json()["shortcut_key"] == "g"

    assert len(client.get("/api/tags").json()) == 1
    delete_response = client.delete(f"/api/tags/{tag_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["is_active"] is False
    assert client.get("/api/tags").json() == []

    all_tags = client.get("/api/tags?include_inactive=true").json()
    assert len(all_tags) == 1
    assert all_tags[0]["id"] == tag_id
    reactivated = client.patch(f"/api/tags/{tag_id}", json={"is_active": True})
    assert reactivated.status_code == 200
    assert reactivated.json()["is_active"] is True
    assert len(client.get("/api/tags").json()) == 1


def test_antagonistic_pair_activation_updates_both_tags(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    created = client.post("/api/antagonistic-pairs", json={
        "first_name": "Ataque", "second_name": "Defensa",
        "first_color": "#2563eb", "second_color": "#16a34a",
    })
    assert created.status_code == 201
    group_key = created.json()["group_key"]

    disabled = client.patch(f"/api/antagonistic-pairs/{group_key}", json={"is_active": False})
    assert disabled.status_code == 200
    assert all(not tag["is_active"] for tag in disabled.json()["tags"])
    assert client.get("/api/tags").json() == []

    enabled = client.patch(f"/api/antagonistic-pairs/{group_key}", json={"is_active": True})
    assert enabled.status_code == 200
    assert all(tag["is_active"] for tag in enabled.json()["tags"])
    assert len(client.get("/api/tags").json()) == 2


def test_reactivating_tag_reassigns_reused_color(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    first = client.post("/api/tags", json={"name": "Gol", "color": "#16a34a"}).json()
    assert client.delete(f"/api/tags/{first['id']}").status_code == 200
    second = client.post("/api/tags", json={"name": "Tiro", "color": "#16a34a"}).json()

    response = client.patch(f"/api/tags/{first['id']}", json={"is_active": True})
    assert response.status_code == 200
    assert response.json()["color"] != second["color"]
    assert len(client.get("/api/tags").json()) == 2


def test_duplicate_color_returns_suggested_color(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.post("/api/tags", json={"name": "Gol", "color": "#16a34a", "mode": "range"}).status_code == 201
    response = client.post("/api/tags", json={"name": "Tiro", "color": "#16a34a", "mode": "range"})
    assert response.status_code == 409
    assert response.json()["detail"]["message"] == "Tag color already in use"
    assert response.json()["detail"]["suggested_color"] != "#16a34a"


def test_upload_edit_and_complete_video(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    video_file = tmp_path / "match.mp4"
    video_file.write_bytes(b"fake")

    with video_file.open("rb") as fh:
        response = client.post("/api/videos", files={"file": ("match.mp4", fh, "video/mp4")}, data={"display_name": "Partido 1"})
    assert response.status_code == 201
    video = response.json()
    assert video["display_name"] == "Partido 1"
    assert video["duration_seconds"] == 12.5
    assert video["fps"] == 25.0
    assert video["width"] == 1920
    assert video["height"] == 1080
    assert video["codec_name"] == "h264"
    assert video["container_name"] == "mp4"
    assert video["bit_rate"] == 4_000_000
    assert video["details_completed"] is False
    incomplete = client.patch(f"/api/videos/{video['id']}", json={"details_completed": True})
    assert incomplete.status_code == 422

    details = client.patch(f"/api/videos/{video['id']}", json={
        "game_format": "5x5", "category": "Senior femenino", "match_name": "Equipo A - Equipo B",
        "home_team": "Equipo A", "away_team": "Equipo B", "competition": "Liga",
        "match_date": "2026-10-22", "details_completed": True,
    })
    assert details.status_code == 200
    assert details.json()["game_format"] == "5x5"
    assert details.json()["match_date"] == "2026-10-22"
    assert details.json()["details_completed"] is True

    patch = client.patch(f"/api/videos/{video['id']}", json={"display_name": "Final A", "status": "completed"})
    assert patch.status_code == 200
    assert patch.json()["display_name"] == "Final A"
    assert patch.json()["status"] == "completed"


def test_download_registers_video_and_probes_it(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    library = tmp_path / "library"

    def fake_download(request, progress_callback):
        (library / "downloaded.mp4").write_bytes(b"video")
        return str(library)

    monkeypatch.setattr("app.main.download_video", fake_download)
    response = client.post("/api/download/start", json={"url": "https://example.com/match", "quality": "best", "download_format": "mp4"})
    assert response.status_code == 200
    task_id = response.json()["task_id"]
    for _ in range(100):
        progress = client.get(f"/api/download/progress/{task_id}").json()
        if progress["status"] != "downloading":
            break
        time.sleep(0.01)
    assert progress["status"] == "completed", progress.get("error")
    assert progress["video_id"] is not None
    videos = client.get("/api/videos").json()
    imported = next(item for item in videos if item["id"] == progress["video_id"])
    assert imported["original_filename"] == "downloaded.mp4"
    assert imported["fps"] == 25.0
    assert imported["details_completed"] is False


def test_library_file_is_reanalyzed_after_copy_finishes(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    file_path = tmp_path / "library" / "copied.mp4"
    file_path.write_bytes(b"first")
    first = client.get("/api/videos").json()[0]
    assert first["size_bytes"] == 5

    file_path.write_bytes(b"finished-video")
    second = client.get("/api/videos").json()[0]
    assert second["id"] == first["id"]
    assert second["size_bytes"] == len(b"finished-video")


def test_uploading_new_video_sets_previous_to_idle(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    with first.open("rb") as fh:
        first_response = client.post("/api/videos", files={"file": ("first.mp4", fh, "video/mp4")})
    assert first_response.status_code == 201
    first_video = first_response.json()
    with second.open("rb") as fh:
        response = client.post("/api/videos", files={"file": ("second.mp4", fh, "video/mp4")})
    assert response.status_code == 201
    assert client.get("/api/current-video").json()["original_filename"] == "second.mp4"
    videos = client.get("/api/videos").json()
    previous = next(item for item in videos if item["id"] == first_video["id"])
    assert previous["status"] == "idle"


def test_marking_current_video_completed_then_uploading_new_one_keeps_completed(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    with first.open("rb") as fh:
        first_video = client.post("/api/videos", files={"file": ("first.mp4", fh, "video/mp4")}).json()
    completed = client.patch(f"/api/videos/{first_video['id']}", json={"status": "completed"})
    assert completed.status_code == 200

    with second.open("rb") as fh:
        response = client.post("/api/videos", files={"file": ("second.mp4", fh, "video/mp4")})
    assert response.status_code == 201
    videos = client.get("/api/videos").json()
    previous = next(item for item in videos if item["id"] == first_video["id"])
    assert previous["status"] == "completed"


def test_list_videos_imports_library_files(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    library_video = tmp_path / "library" / "review.mp4"
    library_video.write_bytes(b"review")

    response = client.get("/api/videos")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["original_filename"] == "review.mp4"
    assert payload[0]["status"] == "idle"
    assert payload[0]["file_exists"] is True
    assert payload[0]["width"] == 1920
    assert payload[0]["height"] == 1080


def test_event_lifecycle_and_range_validation(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    video_file = tmp_path / "match.mp4"
    video_file.write_bytes(b"fake")

    tag = client.post("/api/tags", json={"name": "Tiro", "color": "#dc2626", "mode": "range"}).json()
    with video_file.open("rb") as fh:
        video = client.post("/api/videos", files={"file": ("match.mp4", fh, "video/mp4")}).json()

    create = client.post(
        f"/api/videos/{video['id']}/events",
        json={"tag_definition_id": tag["id"], "start_seconds": 5.0, "note": "inicio"},
    )
    assert create.status_code == 201
    event = create.json()
    assert event["end_seconds"] is None
    assert event["start_frame"] == 125
    assert event["source"] == "human"

    invalid = client.patch(f"/api/events/{event['id']}", json={"end_seconds": 4.0})
    assert invalid.status_code == 422

    update = client.patch(f"/api/events/{event['id']}", json={"end_seconds": 8.0, "note": "fin"})
    assert update.status_code == 200
    assert update.json()["end_seconds"] == 8.0

    delete = client.delete(f"/api/events/{event['id']}")
    assert delete.status_code == 204
    assert client.get(f"/api/videos/{video['id']}/events").json() == []


def test_antagonistic_tags_close_previous_open_event(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    video_file = tmp_path / "match.mp4"
    video_file.write_bytes(b"fake")

    pair = client.post(
        "/api/antagonistic-pairs",
        json={"first_name": "Jugando", "second_name": "No jugando", "first_color": "#16a34a", "second_color": "#dc2626", "shortcut_key": "j"},
    ).json()
    playing, paused = pair["tags"]
    with video_file.open("rb") as fh:
        video = client.post("/api/videos", files={"file": ("match.mp4", fh, "video/mp4")}).json()

    first = client.post(
        f"/api/videos/{video['id']}/events",
        json={"tag_definition_id": playing["id"], "start_seconds": 3.0},
    )
    assert first.status_code == 201
    second = client.post(
        f"/api/videos/{video['id']}/events",
        json={"tag_definition_id": paused["id"], "start_seconds": 9.0},
    )
    assert second.status_code == 201

    events = client.get(f"/api/videos/{video['id']}/events").json()
    assert len(events) == 2
    assert events[0]["tag_definition_id"] == playing["id"]
    assert events[0]["end_seconds"] == 9.0
    assert events[1]["tag_definition_id"] == paused["id"]
    assert events[1]["end_seconds"] is None


def test_antagonistic_tags_from_different_groups_can_coexist(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    video_file = tmp_path / "match.mp4"
    video_file.write_bytes(b"fake")

    playing = client.post(
        "/api/antagonistic-pairs",
        json={"first_name": "Jugando", "second_name": "No jugando", "first_color": "#16a34a", "second_color": "#dc2626"},
    ).json()["tags"][0]
    attack = client.post(
        "/api/antagonistic-pairs",
        json={"first_name": "Ataque", "second_name": "Defensa", "first_color": "#2563eb", "second_color": "#d97706"},
    ).json()["tags"][0]
    with video_file.open("rb") as fh:
        video = client.post("/api/videos", files={"file": ("match.mp4", fh, "video/mp4")}).json()

    first = client.post(
        f"/api/videos/{video['id']}/events",
        json={"tag_definition_id": playing["id"], "start_seconds": 3.0},
    )
    second = client.post(
        f"/api/videos/{video['id']}/events",
        json={"tag_definition_id": attack["id"], "start_seconds": 4.0},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    events = client.get(f"/api/videos/{video['id']}/events").json()
    assert len(events) == 2
    assert events[0]["end_seconds"] is None
    assert events[1]["end_seconds"] is None


def test_antagonistic_tag_requires_group_key(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    response = client.post("/api/tags", json={"name": "Jugando", "color": "#16a34a", "mode": "antagonistic"})
    assert response.status_code == 422


def test_create_antagonistic_pair_creates_two_tags_with_shared_shortcut(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    response = client.post(
        "/api/antagonistic-pairs",
        json={"first_name": "Jugando", "second_name": "No jugando", "first_color": "#16a34a", "second_color": "#dc2626", "shortcut_key": "p"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["shortcut_key"] == "p"
    assert len(payload["tags"]) == 2
    assert payload["tags"][0]["group_key"] == payload["group_key"]
    assert payload["tags"][1]["group_key"] == payload["group_key"]
    assert payload["tags"][0]["shortcut_key"] == "p"
    assert payload["tags"][1]["shortcut_key"] == "p"
    assert payload["tags"][0]["color"] != payload["tags"][1]["color"]


def test_update_antagonistic_pair_updates_both_tags(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    pair = client.post(
        "/api/antagonistic-pairs",
        json={"first_name": "Jugando", "second_name": "No jugando", "first_color": "#16a34a", "second_color": "#dc2626", "shortcut_key": "p"},
    ).json()
    response = client.patch(
        f"/api/antagonistic-pairs/{pair['group_key']}",
        json={"first_name": "En juego", "second_name": "Parado", "first_color": "#2563eb", "second_color": "#d97706", "shortcut_key": "o"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tags"][0]["name"] == "En juego"
    assert payload["tags"][1]["name"] == "Parado"
    assert payload["tags"][0]["color"] == "#2563eb"
    assert payload["tags"][1]["color"] == "#d97706"
    assert payload["tags"][1]["shortcut_key"] == "o"


def test_clip_plan_builds_segments_for_range_tag(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    video_file = tmp_path / "match.mp4"
    video_file.write_bytes(b"fake")

    tag = client.post("/api/tags", json={"name": "Tiro", "color": "#dc2626", "mode": "range"}).json()
    with video_file.open("rb") as fh:
        video = client.post("/api/videos", files={"file": ("match.mp4", fh, "video/mp4")}).json()

    client.post(f"/api/videos/{video['id']}/events", json={"tag_definition_id": tag["id"], "start_seconds": 5.0, "end_seconds": 7.0, "start_frame": 125})
    client.post(f"/api/videos/{video['id']}/events", json={"tag_definition_id": tag["id"], "start_seconds": 9.0, "end_seconds": 12.0, "start_frame": 225})

    response = client.post(
        f"/api/videos/{video['id']}/clip-plan",
        json={"tag_definition_id": tag["id"], "export_mode": "segments", "pre_roll_seconds": 0.5, "post_roll_seconds": 0.25},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["segment_count"] == 2
    assert payload["segments"][0]["start_seconds"] == 4.5
    assert payload["segments"][0]["end_seconds"] == 7.25


def test_clip_export_excludes_antagonistic_segments_and_writes_manifest(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    video_file = tmp_path / "match.mp4"
    video_file.write_bytes(b"fake")
    export_calls: list[str] = []

    def fake_export_segment(source_path, output_path, ffmpeg_path, segment):
        output_path.write_bytes(b"clip")
        export_calls.append(output_path.name)

    monkeypatch.setattr("app.main.export_segment", fake_export_segment)
    monkeypatch.setattr("app.main.concatenate_segments", lambda *args, **kwargs: None)

    pair = client.post(
        "/api/antagonistic-pairs",
        json={"first_name": "Jugando", "second_name": "No jugado", "first_color": "#16a34a", "second_color": "#dc2626"},
    ).json()
    excluded_tag = pair["tags"][1]

    with video_file.open("rb") as fh:
        video = client.post("/api/videos", files={"file": ("match.mp4", fh, "video/mp4")}).json()

    client.post(f"/api/videos/{video['id']}/events", json={"tag_definition_id": excluded_tag["id"], "start_seconds": 2.0, "end_seconds": 4.0})
    client.post(f"/api/videos/{video['id']}/events", json={"tag_definition_id": excluded_tag["id"], "start_seconds": 6.0, "end_seconds": 8.0})

    response = client.post(
        f"/api/videos/{video['id']}/clip-export",
        json={"tag_definition_id": excluded_tag["id"], "export_mode": "exclude", "output_label": "jugable"},
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]
    for _ in range(100):
        progress = client.get(f"/api/videos/{video['id']}/clip-export/{task_id}").json()
        if progress["status"] != "running":
            break
        time.sleep(0.01)
    assert progress["status"] == "completed", progress["error"]
    payload = progress["result"]
    assert payload["segment_count"] == 3
    assert len(export_calls) == 3
    assert Path(payload["manifest_path"]).exists()
