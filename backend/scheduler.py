from __future__ import annotations

from datetime import timedelta
from typing import Callable

from planner.schemas import utc_now


class SafeScheduler:
    """Replaceable in-process scheduler facade for safe automation jobs."""

    def __init__(self) -> None:
        now = utc_now()
        self.jobs: dict[str, dict[str, object]] = {
            "tracking": {"interval_minutes": 60, "last_run_at": None, "next_run_at": now + timedelta(minutes=60), "last_status": "pending"},
            "intelligence": {"interval_minutes": 240, "last_run_at": None, "next_run_at": now + timedelta(minutes=240), "last_status": "pending"},
            "inventory": {"interval_minutes": 180, "last_run_at": None, "next_run_at": now + timedelta(minutes=180), "last_status": "pending"},
        }

    def status(self) -> dict[str, object]:
        return {"enabled": True, "mode": "in-process", "jobs": self.jobs}

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


scheduler = SafeScheduler()
