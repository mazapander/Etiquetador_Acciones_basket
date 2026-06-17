from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.auth import SupabaseAuthMiddleware
from app.database import SessionLocal
from app.models import AppUser, AuditEvent


def get_current_user_from_request(request: Request) -> AppUser | None:
    return getattr(request.state, "current_user", None)


def require_admin(request: Request) -> AppUser:
    user = get_current_user_from_request(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if user.role not in {"admin", "owner"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


def register_production_features(app: FastAPI) -> None:
    app.add_middleware(SupabaseAuthMiddleware)

    @app.get("/api/auth/me")
    def read_me(request: Request) -> dict:
        user = get_current_user_from_request(request)
        if user is None:
            return {"auth_enabled": False, "user": None}
        return {
            "auth_enabled": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role,
                "is_active": user.is_active,
            },
        }

    @app.get("/api/admin/audit-events")
    def list_audit_events(
        request: Request,
        limit: int = Query(default=100, ge=1, le=500),
        video_id: int | None = Query(default=None),
        user_id: int | None = Query(default=None),
        event_type: str | None = Query(default=None),
    ) -> list[dict]:
        require_admin(request)
        db = SessionLocal()
        try:
            statement = select(AuditEvent).options(selectinload(AuditEvent.user)).order_by(AuditEvent.created_at.desc()).limit(limit)
            if video_id is not None:
                statement = statement.where(AuditEvent.video_id == video_id)
            if user_id is not None:
                statement = statement.where(AuditEvent.user_id == user_id)
            if event_type:
                statement = statement.where(AuditEvent.event_type == event_type)
            events = db.scalars(statement).all()
            return [
                {
                    "id": event.id,
                    "user_id": event.user_id,
                    "user_email": event.user.email if event.user else None,
                    "video_id": event.video_id,
                    "annotation_id": event.annotation_id,
                    "event_type": event.event_type,
                    "event_payload": event.event_payload,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                }
                for event in events
            ]
        finally:
            db.close()
