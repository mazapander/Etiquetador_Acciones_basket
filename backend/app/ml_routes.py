import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api/ml", tags=["ml"])


def _json_loads(value: str | None, fallback: Any):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def ensure_ml_tables(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ml_model_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name VARCHAR(120) NOT NULL,
                model_version VARCHAR(80),
                task VARCHAR(80) NOT NULL,
                description TEXT,
                train_video_ids_json TEXT,
                test_video_ids_json TEXT,
                params_json TEXT,
                metrics_json TEXT,
                created_at DATETIME NOT NULL
            )
            """
        )
    )
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_ml_model_runs_model_name ON ml_model_runs(model_name)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_ml_model_runs_task ON ml_model_runs(task)"))
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS ml_model_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                video_id INTEGER NOT NULL,
                window_start FLOAT NOT NULL,
                window_end FLOAT NOT NULL,
                predicted_label VARCHAR(120) NOT NULL,
                true_label VARCHAR(120),
                confidence FLOAT,
                metadata_json TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(run_id) REFERENCES ml_model_runs(id),
                FOREIGN KEY(video_id) REFERENCES videos(id)
            )
            """
        )
    )
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_ml_predictions_run_video ON ml_model_predictions(run_id, video_id)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_ml_predictions_video_time ON ml_model_predictions(video_id, window_start)"))
    db.commit()


def serialize_run(row) -> dict[str, Any]:
    return {
        "id": row.id,
        "model_name": row.model_name,
        "model_version": row.model_version,
        "task": row.task,
        "description": row.description,
        "train_video_ids": _json_loads(row.train_video_ids_json, []),
        "test_video_ids": _json_loads(row.test_video_ids_json, []),
        "params": _json_loads(row.params_json, {}),
        "metrics": _json_loads(row.metrics_json, {}),
        "created_at": row.created_at,
    }


def serialize_video(row) -> dict[str, Any]:
    return {
        "id": row.id,
        "display_name": row.display_name,
        "original_filename": row.original_filename,
        "duration_seconds": row.duration_seconds,
        "fps": row.fps,
    }


def serialize_prediction(row) -> dict[str, Any]:
    is_correct = row.true_label is not None and row.predicted_label == row.true_label
    error_type = None
    if row.true_label is not None and not is_correct:
        if row.predicted_label == "playing" and row.true_label != "playing":
            error_type = "false_positive"
        elif row.predicted_label != "playing" and row.true_label == "playing":
            error_type = "false_negative"
        else:
            error_type = "wrong_label"
    return {
        "id": row.id,
        "run_id": row.run_id,
        "video_id": row.video_id,
        "window_start": row.window_start,
        "window_end": row.window_end,
        "predicted_label": row.predicted_label,
        "true_label": row.true_label,
        "confidence": row.confidence,
        "metadata": _json_loads(row.metadata_json, {}),
        "is_correct": is_correct,
        "error_type": error_type,
        "created_at": row.created_at,
    }


@router.get("/runs")
def list_model_runs(db: Session = Depends(get_db)):
    ensure_ml_tables(db)
    rows = db.execute(
        text(
            """
            SELECT id, model_name, model_version, task, description,
                   train_video_ids_json, test_video_ids_json, params_json, metrics_json, created_at
            FROM ml_model_runs
            ORDER BY created_at DESC, id DESC
            """
        )
    ).fetchall()
    return [serialize_run(row) for row in rows]


@router.get("/runs/{run_id}")
def get_model_run(run_id: int, db: Session = Depends(get_db)):
    ensure_ml_tables(db)
    row = db.execute(
        text(
            """
            SELECT id, model_name, model_version, task, description,
                   train_video_ids_json, test_video_ids_json, params_json, metrics_json, created_at
            FROM ml_model_runs
            WHERE id = :run_id
            """
        ),
        {"run_id": run_id},
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model run not found")
    return serialize_run(row)


@router.get("/runs/{run_id}/videos")
def list_run_videos(run_id: int, db: Session = Depends(get_db)):
    ensure_ml_tables(db)
    run = get_model_run(run_id, db)
    rows = db.execute(
        text(
            """
            SELECT DISTINCT v.id, v.display_name, v.original_filename, v.duration_seconds, v.fps
            FROM videos v
            JOIN ml_model_predictions p ON p.video_id = v.id
            WHERE p.run_id = :run_id
            ORDER BY v.display_name
            """
        ),
        {"run_id": run_id},
    ).fetchall()
    return {"run": run, "videos": [serialize_video(row) for row in rows]}


@router.get("/runs/{run_id}/videos/{video_id}")
def get_run_video_results(run_id: int, video_id: int, db: Session = Depends(get_db)):
    ensure_ml_tables(db)
    run = get_model_run(run_id, db)
    video_row = db.execute(
        text(
            """
            SELECT id, display_name, original_filename, duration_seconds, fps
            FROM videos
            WHERE id = :video_id
            """
        ),
        {"video_id": video_id},
    ).fetchone()
    if video_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    prediction_rows = db.execute(
        text(
            """
            SELECT id, run_id, video_id, window_start, window_end, predicted_label,
                   true_label, confidence, metadata_json, created_at
            FROM ml_model_predictions
            WHERE run_id = :run_id AND video_id = :video_id
            ORDER BY window_start, id
            """
        ),
        {"run_id": run_id, "video_id": video_id},
    ).fetchall()
    predictions = [serialize_prediction(row) for row in prediction_rows]
    total = len(predictions)
    correct = sum(1 for item in predictions if item["is_correct"])
    incorrect = sum(1 for item in predictions if item["true_label"] is not None and not item["is_correct"])
    confidences = [item["confidence"] for item in predictions if item["confidence"] is not None]
    avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else None
    labels = sorted({item["true_label"] for item in predictions if item["true_label"] is not None} | {item["predicted_label"] for item in predictions})
    confusion = []
    for true_label in labels:
        for predicted_label in labels:
            count = sum(1 for item in predictions if item["true_label"] == true_label and item["predicted_label"] == predicted_label)
            if count:
                confusion.append({"true_label": true_label, "predicted_label": predicted_label, "count": count})
    return {
        "run": run,
        "video": serialize_video(video_row),
        "summary": {
            "total_windows": total,
            "correct": correct,
            "incorrect": incorrect,
            "accuracy": round(correct / total, 4) if total else None,
            "avg_confidence": avg_confidence,
        },
        "predictions": predictions,
        "errors": [item for item in predictions if item["error_type"] is not None],
        "confusion": confusion,
    }


@router.post("/runs")
def create_model_run(payload: dict[str, Any], db: Session = Depends(get_db)):
    ensure_ml_tables(db)
    required = ["model_name", "task"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Missing fields: {', '.join(missing)}")
    now = datetime.utcnow().isoformat()
    result = db.execute(
        text(
            """
            INSERT INTO ml_model_runs (
                model_name, model_version, task, description,
                train_video_ids_json, test_video_ids_json, params_json, metrics_json, created_at
            )
            VALUES (
                :model_name, :model_version, :task, :description,
                :train_video_ids_json, :test_video_ids_json, :params_json, :metrics_json, :created_at
            )
            """
        ),
        {
            "model_name": payload["model_name"],
            "model_version": payload.get("model_version"),
            "task": payload["task"],
            "description": payload.get("description"),
            "train_video_ids_json": json.dumps(payload.get("train_video_ids", [])),
            "test_video_ids_json": json.dumps(payload.get("test_video_ids", [])),
            "params_json": json.dumps(payload.get("params", {})),
            "metrics_json": json.dumps(payload.get("metrics", {})),
            "created_at": now,
        },
    )
    db.commit()
    run_id = result.lastrowid
    return get_model_run(run_id, db)


@router.post("/runs/{run_id}/predictions")
def create_model_predictions(run_id: int, payload: dict[str, Any], db: Session = Depends(get_db)):
    ensure_ml_tables(db)
    get_model_run(run_id, db)
    predictions = payload.get("predictions", [])
    if not isinstance(predictions, list):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="predictions must be a list")
    now = datetime.utcnow().isoformat()
    for item in predictions:
        db.execute(
            text(
                """
                INSERT INTO ml_model_predictions (
                    run_id, video_id, window_start, window_end, predicted_label,
                    true_label, confidence, metadata_json, created_at
                )
                VALUES (
                    :run_id, :video_id, :window_start, :window_end, :predicted_label,
                    :true_label, :confidence, :metadata_json, :created_at
                )
                """
            ),
            {
                "run_id": run_id,
                "video_id": item["video_id"],
                "window_start": item["window_start"],
                "window_end": item["window_end"],
                "predicted_label": item["predicted_label"],
                "true_label": item.get("true_label"),
                "confidence": item.get("confidence"),
                "metadata_json": json.dumps(item.get("metadata", {})),
                "created_at": now,
            },
        )
    db.commit()
    return {"inserted": len(predictions)}
