from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from logging import LogRecord
from typing import Any

REQUEST_ID_HEADER = "X-Request-ID"
SERVICE_NAME = "cloudops-sre-platform-api"

_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
_default_log_record_factory = logging.getLogRecordFactory()
_standard_record_attrs = set(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(request_id: str) -> contextvars.Token[str | None]:
    return _request_id.set(request_id)


def reset_request_id(token: contextvars.Token[str | None]) -> None:
    _request_id.reset(token)


class RequestContextFilter(logging.Filter):
    def __init__(self, app_env: str) -> None:
        super().__init__()
        self.app_env = app_env

    def filter(self, record: LogRecord) -> bool:
        record.request_id = get_request_id()
        record.service = SERVICE_NAME
        record.environment = self.app_env
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "service": getattr(record, "service", SERVICE_NAME),
            "environment": getattr(record, "environment", None),
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }

        for key, value in record.__dict__.items():
            if key in _standard_record_attrs or key in payload or key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging(log_level: str, log_format: str, app_env: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)

    def record_factory(*args: Any, **kwargs: Any) -> LogRecord:
        record = _default_log_record_factory(*args, **kwargs)
        record.request_id = get_request_id()
        return record

    logging.setLogRecordFactory(record_factory)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestContextFilter(app_env=app_env))
    if log_format.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(service)s] "
                "[request_id=%(request_id)s] %(name)s: %(message)s"
            )
        )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(level)

    logging.captureWarnings(True)
