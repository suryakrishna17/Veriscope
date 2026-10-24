"""JWT auth, password hashing, role guards, rate limiting and security headers."""
from __future__ import annotations

import fnmatch
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, TypeVar

import jwt
from flask import Flask, Response, current_app, g, request
from werkzeug.security import check_password_hash, generate_password_hash

from .errors import ApiError

F = TypeVar("F", bound=Callable[..., Any])
ROLES = ("applicant", "reviewer", "admin")


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="scrypt")


def verify_password(hashed: str, password: str) -> bool:
    return check_password_hash(hashed, password)


def issue_token(user: dict[str, Any], secret: str, ttl_minutes: int) -> str:
    now = datetime.now(UTC)
    claims = {"sub": user["id"], "role": user["role"], "iat": now, "exp": now + timedelta(minutes=ttl_minutes)}
    return jwt.encode(claims, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as e:
        raise ApiError(401, "TOKEN_EXPIRED", "Your session has expired. Sign in again.") from e
    except jwt.PyJWTError as e:
        raise ApiError(401, "UNAUTHENTICATED", "Sign in to continue.") from e


def current_user() -> dict[str, Any]:
    user = getattr(g, "user", None)
    if user is None:
        raise ApiError(401, "UNAUTHENTICATED", "Sign in to continue.")
    return user  # type: ignore[no-any-return]


def require_auth(*roles: str) -> Callable[[F], F]:
    def deco(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                raise ApiError(401, "UNAUTHENTICATED", "Sign in to continue.")
            svc = current_app.extensions["veriscope"]
            claims = decode_token(header[7:], svc.settings.secret_key)
            user = svc.db.one("SELECT id, email, name, role FROM users WHERE id = ?", (claims["sub"],))
            if user is None:
                raise ApiError(401, "UNAUTHENTICATED", "Sign in to continue.")
            if roles and user["role"] not in roles:
                raise ApiError(403, "FORBIDDEN", "Your role does not allow this action.")
            g.user = user
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return deco


class RateLimiter:
    """In-process sliding-window limiter. Swap for Redis when running several instances.

    Note: state is per-process only — multi-worker deployments need an external store.
    _MAX_KEYS bounds memory by evicting the oldest entry when the dict is full.
    """

    _MAX_KEYS = 10_000

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_s: int) -> None:
        now = time.monotonic()
        with self._lock:
            # Evict the oldest entry when the dict would exceed _MAX_KEYS.
            if key not in self._hits and len(self._hits) >= self._MAX_KEYS:
                oldest = next(iter(self._hits))
                del self._hits[oldest]
            q = self._hits[key]
            while q and now - q[0] > window_s:
                q.popleft()
            if len(q) >= limit:
                raise ApiError(429, "RATE_LIMITED", "Too many requests. Wait a minute and try again.")
            q.append(now)


def rate_limit(bucket: str, limit: int, window_s: int = 60) -> Callable[[F], F]:
    def deco(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            svc = current_app.extensions["veriscope"]
            if svc.settings.app_env != "test":
                svc.rate_limiter.check(f"{bucket}:{request.remote_addr}", limit, window_s)
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return deco


def install_security_headers(app: Flask, cors_origins: tuple[str, ...]) -> None:
    def _is_allowed(origin: str | None) -> bool:
        if not origin:
            return False
        return "*" in cors_origins or any(fnmatch.fnmatch(origin, pat) for pat in cors_origins)

    @app.before_request
    def _preflight() -> Response | None:
        if request.method == "OPTIONS":
            resp = Response(status=204)
            origin = request.headers.get("Origin")
            if _is_allowed(origin):
                resp.headers["Access-Control-Allow-Origin"] = origin
                resp.headers["Vary"] = "Origin"
                resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Request-ID"
                resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
                resp.headers["Access-Control-Max-Age"] = "86400"
            return resp
        return None

    @app.after_request
    def _headers(resp: Response) -> Response:
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; frame-ancestors 'none'",
        )
        origin = request.headers.get("Origin")
        if _is_allowed(origin):
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
            resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Request-ID"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
        cid = g.get("correlation_id")
        if cid:
            resp.headers["X-Request-ID"] = cid
        return resp
