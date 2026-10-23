"""Uniform API errors: {"error": {"code", "message", "correlation_id", "details"}}."""
from __future__ import annotations

import logging
from typing import Any

from flask import Flask, g, jsonify
from werkzeug.exceptions import HTTPException

log = logging.getLogger("veriscope.errors")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}


def bad_request(message: str, **details: Any) -> ApiError:
    return ApiError(400, "INVALID_REQUEST", message, details)


def not_found(entity: str) -> ApiError:
    return ApiError(404, "NOT_FOUND", f"{entity} was not found.")


def forbidden(message: str = "Your role does not allow this action.") -> ApiError:
    return ApiError(403, "FORBIDDEN", message)


def conflict(message: str, **details: Any) -> ApiError:
    return ApiError(409, "INVALID_STATE", message, details)


def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "correlation_id": getattr(g, "correlation_id", None),
            "details": details or {},
        }
    }


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def _api(e: ApiError):  # type: ignore[no-untyped-def]
        return jsonify(error_body(e.code, e.message, e.details)), e.status

    @app.errorhandler(HTTPException)
    def _http(e: HTTPException):  # type: ignore[no-untyped-def]
        codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 413: "FILE_TOO_LARGE", 429: "RATE_LIMITED"}
        status = e.code or 500
        code = codes.get(status, "HTTP_ERROR")
        if status == 413:
            msg = "The uploaded file is larger than the allowed limit."
        elif status == 404:
            msg = "That address does not exist."
        else:
            msg = e.description or "The request failed."
        return jsonify(error_body(code, msg)), status

    @app.errorhandler(Exception)
    def _unhandled(e: Exception):  # type: ignore[no-untyped-def]
        log.exception("unhandled_error")
        return (
            jsonify(error_body("INTERNAL_ERROR", "The server hit an unexpected error. Quote the correlation ID when reporting it.")),
            500,
        )
