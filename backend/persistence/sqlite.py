from __future__ import annotations

import json
import shutil
import sqlite3
import threading
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from persistence.schema import ENTITY_TABLES, json_dumps


ModelT = TypeVar("ModelT", bound=BaseModel)
DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "purpleclaw.db"
BACKUP_RETENTION = 10


class SQLiteStore:
    """SQLite JSON-string store for default self-contained tracking persistence."""

    backend_name = "sqlite"

    def __init__(self, database_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.database_path = Path(database_path)
        self._connection: sqlite3.Connection | None = None
        self._lock = threading.RLock()

    @property
    def enabled(self) -> bool:
        return True

    def init_schema(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            connection = self._connect()
            for table_name in ENTITY_TABLES:
                connection.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id TEXT PRIMARY KEY,
                        environment_id TEXT NOT NULL,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                connection.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_environment ON {table_name} (environment_id)")
            connection.commit()

    def upsert_many(self, table_name: str, records: Iterable[BaseModel], id_field: str | None = None) -> None:
        key = id_field or ENTITY_TABLES[table_name]
        with self._lock:
            connection = self._connect()
            with connection:
                for record in records:
                    payload = record.model_dump(mode="json")
                    connection.execute(
                        f"""
                        INSERT INTO {table_name} (id, environment_id, data, created_at, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT(id) DO UPDATE SET
                            environment_id = excluded.environment_id,
                            data = excluded.data,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (
                            str(payload[key]),
                            str(payload.get("environment_id", "global")),
                            json_dumps(payload),
                        ),
                    )

    def replace_environment(self, table_name: str, environment_id: str, records: Iterable[BaseModel], id_field: str | None = None) -> None:
        key = id_field or ENTITY_TABLES[table_name]
        with self._lock:
            connection = self._connect()
            with connection:
                connection.execute(f"DELETE FROM {table_name} WHERE environment_id = ?", (environment_id,))
                for record in records:
                    payload = record.model_dump(mode="json")
                    connection.execute(
                        f"""
                        INSERT INTO {table_name} (id, environment_id, data, created_at, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (
                            str(payload[key]),
                            str(payload.get("environment_id", environment_id)),
                            json_dumps(payload),
                        ),
                    )

    def list_records(self, table_name: str, model: type[ModelT], environment_id: str | None = None) -> list[ModelT]:
        with self._lock:
            connection = self._connect()
            if environment_id:
                rows = connection.execute(f"SELECT data FROM {table_name} WHERE environment_id = ?", (environment_id,)).fetchall()
            else:
                rows = connection.execute(f"SELECT data FROM {table_name}").fetchall()
        return [model.model_validate(json.loads(row["data"])) for row in rows]

    def platform_health(self, scheduler_status: dict[str, object], environment_count: int) -> dict[str, object]:
        status = self.status()
        status.update(
            {
                "connection_status": self.connection_status(),
                "writable": self.writable(),
                "scheduler": scheduler_status,
                "environment_count": environment_count,
                "metrics": self.metrics(),
            }
        )
        return status

    def connection_status(self) -> str:
        try:
            with self._lock:
                self._connect().execute("SELECT 1").fetchone()
            return "connected"
        except sqlite3.Error:
            return "unavailable"

    def writable(self) -> bool:
        try:
            with self._lock:
                connection = self._connect()
                connection.execute("CREATE TABLE IF NOT EXISTS __healthcheck (id TEXT PRIMARY KEY)")
                connection.execute("INSERT OR REPLACE INTO __healthcheck (id) VALUES ('write')")
                connection.commit()
            return True
        except sqlite3.Error:
            return False

    def metrics(self) -> dict[str, object]:
        self.init_schema()
        with self._lock:
            connection = self._connect()
            counts = {
                table_name: int(connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()["count"])
                for table_name in ENTITY_TABLES
            }
        return {
            "database_size_bytes": self.database_path.stat().st_size if self.database_path.exists() else 0,
            "record_counts": counts,
        }

    def backup(self, retention: int = BACKUP_RETENTION) -> dict[str, object]:
        self.init_schema()
        backups_dir = self.database_path.parent / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        backup_path = backups_dir / f"purpleclaw_{timestamp}.db"
        with self._lock:
            source = self._connect()
            destination = sqlite3.connect(backup_path)
            try:
                source.backup(destination)
            finally:
                destination.close()
        removed = self.cleanup_backups(retention)
        return {
            "filename": backup_path.name,
            "path": str(backup_path),
            "size_bytes": backup_path.stat().st_size,
            "removed_old_backups": removed,
        }

    def list_backups(self) -> list[dict[str, object]]:
        backups_dir = self.database_path.parent / "backups"
        if not backups_dir.exists():
            return []
        backups = []
        for path in sorted(backups_dir.glob("purpleclaw_*.db"), key=lambda item: item.stat().st_mtime, reverse=True):
            backups.append(
                {
                    "filename": path.name,
                    "size_bytes": path.stat().st_size,
                    "created_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                }
            )
        return backups

    def restore(self, filename: str) -> dict[str, object]:
        backups_dir = self.database_path.parent / "backups"
        backup_path = backups_dir / Path(filename).name
        if backup_path.parent != backups_dir or not backup_path.name.startswith("purpleclaw_") or backup_path.suffix != ".db":
            raise ValueError("invalid backup filename")
        if not backup_path.exists():
            raise FileNotFoundError("backup file not found")

        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            restore_tmp = self.database_path.with_suffix(".db.restore")
            shutil.copy2(backup_path, restore_tmp)
            restore_tmp.replace(self.database_path)
            self.init_schema()
        return {
            "restored": True,
            "filename": backup_path.name,
            "database_path": str(self.database_path),
        }

    def cleanup_backups(self, retention: int = BACKUP_RETENTION) -> int:
        backups = self.list_backups()
        removed = 0
        for backup in backups[retention:]:
            path = self.database_path.parent / "backups" / str(backup["filename"])
            if path.exists():
                path.unlink()
                removed += 1
        return removed

    def cleanup_stale_telemetry(self, max_records: int = 5000) -> int:
        with self._lock:
            connection = self._connect()
            count = int(connection.execute("SELECT COUNT(*) AS count FROM telemetry_summaries").fetchone()["count"])
            if count <= max_records:
                return 0
            to_delete = count - max_records
            with connection:
                connection.execute(
                    """
                    DELETE FROM telemetry_summaries
                    WHERE id IN (
                        SELECT id FROM telemetry_summaries
                        ORDER BY updated_at ASC
                        LIMIT ?
                    )
                    """,
                    (to_delete,),
                )
            return to_delete

    def status(self) -> dict[str, object]:
        return {
            "backend": self.backend_name,
            "enabled": True,
            "configured": True,
            "driver_available": True,
            "database_path": str(self.database_path),
        }

    def _connect(self) -> sqlite3.Connection:
        if self._connection is None:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(self.database_path, check_same_thread=False, timeout=10)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA busy_timeout=5000")
            self._connection.execute("PRAGMA foreign_keys=ON")
        return self._connection
