"""Structured JSON logging with PII redaction. Raw document text must never reach logs."""
from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime

from flask import g, has_request_context

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_LONG_DIGITS = re.compile(r"\b\d{6,}\b")


def redact(text: str) -> str:
    return _LONG_DIGITS.sub("[number]", _EMAIL.sub("[email]", text))


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": redact(record.getMessage()),
        }
        if has_request_context():
            payload["correlation_id"] = getattr(g, "correlation_id", None)
        extra = getattr(record, "ctx", None)
        if isinstance(extra, dict):
            payload["ctx"] = {k: redact(str(v)) for k, v in extra.items()}
        if record.exc_info:
            payload["exc"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    for noisy in ("werkzeug", "pdfminer", "PIL", "pypdf"):
        logging.getLogger(noisy).setLevel("WARNING" if noisy == "werkzeug" else "ERROR")
