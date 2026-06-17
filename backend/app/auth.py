from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import jwt
from fastapi import Request, status
from fastapi.responses import JSONResponse
from jwt import PyJWKClient
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.database import SessionLocal
from app.models import AppUser, AuditEvent

settings = get_settings()
_jwks_client: PyJWKClient | None = None

VIDEO_ID_RE = re.compile(r"^/api/videos/(?P<video_id>\d+)(?:/|$)")
ANNOTATION_ID_RE = re.compile(r"^/api/events/(?P<annotation_id>\d+)(?:/|$)")


class AuthError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _jwks_url() -> str:
    if settings.supabase_jwks_url:
        return settings.supabase_jwks_url
    if not settings.supabase_url:
        raise AuthError("Supabase URL is not configured", status.HTTP_500_INTERNAL_SERVER_ERROR)
    return f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(_jwks_url())
    return _jwks_client


def extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    # Fallback for browser media requests where Authorization headers are hard to attach.
    # Prefer the service worker approach in frontend/public/auth-stream-sw.js.
    query_token = request.query_params.get("access_token")
    return query_token.strip() if query_token else None


def verify_supabase_token(token: str) -> dict[str, Any]:
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        decode_kwargs: dict[str, Any] = {
            "key": signing_key.key,
            "algorithms": ["ES256", "RS256"],
            "options": {"verify_aud": bool(settings.supabase_jwt_audience)},
        }
        if settings.supabase_jwt_audience:
            decode_kwargs["audience"] = settings.supabase_jwt_audience
        return jwt.decode(token, **decode_kwargs)
    except Exception as exc:  # noqa: BLE001 - auth failures should not leak internals
        raise AuthError("Invalid or expired auth token") from exc


def _is_admin_email(email: str | None) -> bool:
    if not email:
        return False
    return email.lower() in {admin_email.lower() for admin_email in settings.admin_emails}


def upsert_app_user(claims: dict[str, Any]) -> AppUser:
    supabase_user_id = claims.get("sub")
    email = claims.get("email") or claims.get("user_metadata", {}).get("email")
    if not supabase_user_id or not email:
        raise AuthError("Token does not contain a valid user identity")

    now = datetime.utcnow()
    db = SessionLocal()
    try:
        user = db.query(AppUser).filter(AppUser.supabase_user_id == str(supabase_user_id)).one_or_none()
        if user is None:
            user = AppUser(
                supabase_user_id=str(supabase_user_id),
                email=str(email).lower(),
                display_name=claims.get("user_metadata", {}).get("name"),
                role="admin" if _is_admin_email(str(email)) else "annotator",
                is_active=True,
                last_login_at=now,
            )
            db.add(user)
        else:
            user.email = str(email).lower()
            user.display_name = claims.get("user_metadata", {}).get("name") or user.display_name
            user.last_login_at = now
            if _is_admin_email(str(email)) and user.role != "admin":
                user.role = "admin"
        db.commit()
        db.refresh(user)
        db.expunge(user)
        return user
    finally:
        db.close()


def get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else None


def event_type_for_request(method: str, path: str) -> str:
    if re.match(r"^/api/videos/\d+/stream$", path):
        return "video_stream_requested"
    if method == "POST" and path == "/api/videos":
        return "video_uploaded"
    if method == "POST" and path == "/api/videos/sync":
        return "video_library_synced"
    if method == "PATCH" and re.match(r"^/api/videos/\d+$", path):
        return "video_updated"
    if method == "DELETE" and re.match(r"^/api/videos/\d+$", path):
        return "video_deleted"
    if method == "GET" and re.match(r"^/api/videos/\d+/events$", path):
        return "video_events_listed"
    if method == "POST" and re.match(r"^/api/videos/\d+/events$", path):
        return "annotation_created"
    if method == "PATCH" and re.match(r"^/api/events/\d+$", path):
        return "annotation_updated"
    if method == "DELETE" and re.match(r"^/api/events/\d+$", path):
        return "annotation_deleted"
    if method == "POST" and re.match(r"^/api/videos/\d+/clip-export$", path):
        return "clip_export_started"
    if method == "POST" and path == "/api/download/start":
        return "download_started"
    return "api_request"


def _extract_video_id(path: str) -> int | None:
    match = VIDEO_ID_RE.match(path)
    return int(match.group("video_id")) if match else None


def _extract_annotation_id(path: str) -> int | None:
    match = ANNOTATION_ID_RE.match(path)
    return int(match.group("annotation_id")) if match else None


def should_audit(method: str, path: str) -> bool:
    if not path.startswith("/api") or path == "/api/health":
        return False
    if path == "/api/auth/me":
        return False
    if method in {"POST", "PATCH", "DELETE"}:
        return True
    return bool(re.match(r"^/api/videos/\d+/(stream|events)$", path))


def create_audit_event(
    *,
    user_id: int | None,
    method: str,
    path: str,
    status_code: int,
    request: Request,
) -> None:
    if not should_audit(method, path):
        return
    db = SessionLocal()
    try:
        db.add(
            AuditEvent(
                user_id=user_id,
                video_id=_extract_video_id(path),
                annotation_id=_extract_annotation_id(path),
                event_type=event_type_for_request(method, path),
                event_payload={
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "query": {key: value for key, value in request.query_params.items() if key != "access_token"},
                },
                ip_address=get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
            )
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()
    finally:
        db.close()


class SupabaseAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()
        path = request.url.path

        if method == "OPTIONS" or not path.startswith("/api") or path == "/api/health":
            return await call_next(request)

        user: AppUser | None = None
        if settings.auth_enabled:
            token = extract_token(request)
            if not token:
                return JSONResponse({"detail": "Missing auth token"}, status_code=status.HTTP_401_UNAUTHORIZED)
            try:
                claims = verify_supabase_token(token)
                user = upsert_app_user(claims)
                if not user.is_active:
                    return JSONResponse({"detail": "User is disabled"}, status_code=status.HTTP_403_FORBIDDEN)
                request.state.current_user = user
            except AuthError as exc:
                return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        else:
            request.state.current_user = None

        response = await call_next(request)
        create_audit_event(
            user_id=user.id if user else None,
            method=method,
            path=path,
            status_code=response.status_code,
            request=request,
        )
        return response
