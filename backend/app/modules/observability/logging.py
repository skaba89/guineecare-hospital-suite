"""Structured JSON logging — drop-in replacement for the default formatter.

Use:
    from app.modules.observability.logging import configure_logging
    configure_logging(environment="production")  # JSON in prod, pretty in dev

This avoids extra dependencies (no structlog, no python-json-logger). Standard
library `logging` is enough and reduces the surface area for supply chain risk.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Render log records as one-line JSON objects."""

    # Reserved attributes on LogRecord that we don't want to copy into extras
    _RESERVED = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime", "taskName",
    }

    def __init__(self, service: str = "guineecare", environment: str = "production"):
        super().__init__()
        self.service = service
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        # Timestamp in ISO-8601 with timezone (UTC)
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()

        payload: dict = {
            "ts": ts,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service,
            "environment": self.environment,
            "file": f"{record.pathname}:{record.lineno}",
        }

        # Carry over non-reserved extras (request_id, user_id, etc.)
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                # Skip non-serializable values gracefully
                try:
                    json.dumps(value)
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = repr(value)

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


class PrettyFormatter(logging.Formatter):
    """Human-readable formatter for dev — colors optional."""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%H:%M:%S")
        msg = record.getMessage()
        prefix = f"{ts} {record.levelname:7s} {record.name:30s}"
        out = f"{prefix} | {msg}"
        if record.exc_info:
            out += "\n" + self.formatException(record.exc_info)
        return out


def configure_logging(environment: str | None = None) -> None:
    """Configure root logger with JSON or pretty formatter based on environment.

    ENVIRONMENT values "production" and "staging" get JSON.
    Everything else (local, dev, test, unset) gets pretty.
    """
    env = (environment or os.environ.get("ENVIRONMENT", "local")).lower()
    is_json = env in {"production", "staging"}

    root = logging.getLogger()
    # Remove any existing handlers (uvicorn installs its own)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if is_json:
        handler.setFormatter(JsonFormatter(environment=env))
    else:
        handler.setFormatter(PrettyFormatter())

    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # Quiet down noisy libs
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
