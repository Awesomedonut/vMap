"""Thread-safe in-memory tracking of world-generation jobs."""

from __future__ import annotations

import threading
import uuid
from typing import Any


class JobTracker:
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self) -> dict[str, Any]:
        job = {"id": uuid.uuid4().hex[:12], "status": "running", "stage": "queued",
               "progress": 0.0, "slug": None, "error": None}
        with self._lock:
            self._jobs[job["id"]] = job
        return dict(job)

    def update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            self._jobs[job_id].update(fields)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None
