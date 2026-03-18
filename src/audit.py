"""
Structured audit logging for the pipeline.

Every significant pipeline event is written to:
  1. The standard Python logging system (console + file handler)
  2. An in-memory audit trail list attached to the ReviewPayload

This provides a complete, reproducible record of every decision made during
processing, suitable for compliance, debugging, and model evaluation.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path


def configure_logging(log_dir: str | Path = "logs", level: int = logging.INFO) -> None:
    """
    Set up root logger with:
      - StreamHandler (stdout) for interactive use
      - RotatingFileHandler for persistent audit records
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)

    if not root.handlers:
        # Console
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        root.addHandler(sh)

        # Rotating file (10 MB × 5 backups)
        fh = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        fh.setFormatter(fmt)
        root.addHandler(fh)


class AuditTrail:
    """Collects pipeline audit events as timestamped strings."""

    def __init__(self, note_id: str) -> None:
        self.note_id = note_id
        self._events: list[str] = []
        self._logger = logging.getLogger(f"audit.{note_id}")

    def record(self, event: str) -> None:
        ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = f"[{ts}] {event}"
        self._events.append(entry)
        self._logger.info(entry)

    def events(self) -> list[str]:
        return list(self._events)
