from __future__ import annotations

import threading
import time
from datetime import timedelta
from typing import Callable

from planner.schemas import utc_now


class SafeScheduler:
    """Replaceable in-process scheduler facade for safe automation jobs."""

    def __init__(self) -> None:
        now = utc_now()
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._started = False
        self._interval_jobs: dict[str, dict[str, object]] = {}
        self.jobs: dict[str, dict[str, object]] = {
            "tracking": {"interval_minutes": 60, "last_run_at": None, "next_run_at": now + timedelta(minutes=60), "last_status": "pending"},
            "intelligence": {"interval_minutes": 240, "last_run_at": None, "next_run_at": now + timedelta(minutes=240), "last_status": "pending"},
            "inventory": {"interval_minutes": 180, "last_run_at": None, "next_run_at": now + timedelta(minutes=180), "last_status": "pending"},
        }

    def status(self) -> dict[str, object]:
        with self._lock:
            interval_jobs = {
                job_name: {
                    "interval_seconds": payload["interval_seconds"],
                    "last_run_at": payload["last_run_at"],
                    "next_run_at": payload["next_run_at"],
                    "last_status": payload["last_status"],
                }
                for job_name, payload in self._interval_jobs.items()
            }
            return {"enabled": True, "mode": "in-process", "jobs": self.jobs, "datasource_ingestion": interval_jobs}

    def run_now(self, job_name: str, runner: Callable[[], object]) -> object:
        started_at = utc_now()
        result = runner()
        interval = int(self.jobs[job_name]["interval_minutes"])
        self.jobs[job_name].update(
            {
                "last_run_at": started_at,
                "next_run_at": utc_now() + timedelta(minutes=interval),
                "last_status": "completed",
            }
        )
        return result

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
        thread = threading.Thread(target=self._run_loop, name="purpleclaw-scheduler", daemon=True)
        thread.start()

    def register_interval_job(self, job_name: str, interval_seconds: int, runner: Callable[[], object]) -> None:
        with self._lock:
            now = utc_now()
            self._interval_jobs[job_name] = {
                "interval_seconds": interval_seconds,
                "runner": runner,
                "last_run_at": None,
                "next_run_at": now + timedelta(seconds=interval_seconds),
                "last_status": "scheduled",
            }

    def remove_interval_job(self, job_name: str) -> None:
        with self._lock:
            self._interval_jobs.pop(job_name, None)

    def trigger_interval_job_now(self, job_name: str) -> None:
        with self._lock:
            job = self._interval_jobs.get(job_name)
            if job is None:
                return
            job["next_run_at"] = utc_now()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            due_jobs: list[tuple[str, dict[str, object]]] = []
            now = utc_now()
            with self._lock:
                for job_name, payload in self._interval_jobs.items():
                    next_run_at = payload.get("next_run_at")
                    if next_run_at is not None and next_run_at <= now:
                        due_jobs.append((job_name, payload))
            for job_name, payload in due_jobs:
                try:
                    payload["runner"]()
                    status = "completed"
                except Exception:  # noqa: BLE001
                    status = "failed"
                with self._lock:
                    interval = int(payload["interval_seconds"])
                    payload["last_run_at"] = now
                    payload["next_run_at"] = utc_now() + timedelta(seconds=interval)
                    payload["last_status"] = status
            time.sleep(1)


scheduler = SafeScheduler()
