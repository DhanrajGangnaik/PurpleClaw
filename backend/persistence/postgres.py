from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TypeVar

try:
    import psycopg
except ImportError:  # pragma: no cover - optional advanced backend.
    psycopg = None

from pydantic import BaseModel

from persistence.schema import ENTITY_TABLES, json_dumps


ModelT = TypeVar("ModelT", bound=BaseModel)


class PostgresStore:
    """JSONB-backed PostgreSQL store for tracking-mode records."""

    backend_name = "postgres"

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    @property
    def enabled(self) -> bool:
        return bool(self.database_url and psycopg is not None)

    def init_schema(self) -> None:
        if not self.enabled:
            return
        with self._connect() as connection:
            with connection.cursor() as cursor:
                for table_name in ENTITY_TABLES:
                    cursor.execute(
                        f"""
                        CREATE TABLE IF NOT EXISTS {table_name} (
                            id TEXT PRIMARY KEY,
                            environment_id TEXT NOT NULL,
                            data JSONB NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                        )
                        """
                    )
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_environment ON {table_name} (environment_id)")
            connection.commit()

    def upsert_many(self, table_name: str, records: Iterable[BaseModel], id_field: str | None = None) -> None:
        if not self.enabled:
            return
        key = id_field or ENTITY_TABLES[table_name]
        with self._connect() as connection:
            with connection.cursor() as cursor:
                for record in records:
                    payload = record.model_dump(mode="json")
                    cursor.execute(
                        f"""
                        INSERT INTO {table_name} (id, environment_id, data, created_at, updated_at)
                        VALUES (%s, %s, %s::jsonb, now(), now())
                        ON CONFLICT (id) DO UPDATE
                        SET environment_id = EXCLUDED.environment_id,
                            data = EXCLUDED.data,
                            updated_at = now()
                        """,
                        (
                            str(payload[key]),
                            str(payload.get("environment_id", "global")),
                            json_dumps(payload),
                        ),
                    )
            connection.commit()

    def replace_environment(self, table_name: str, environment_id: str, records: Iterable[BaseModel], id_field: str | None = None) -> None:
        if not self.enabled:
            return
        key = id_field or ENTITY_TABLES[table_name]
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {table_name} WHERE environment_id = %s", (environment_id,))
                for record in records:
                    payload = record.model_dump(mode="json")
                    cursor.execute(
                        f"""
                        INSERT INTO {table_name} (id, environment_id, data, created_at, updated_at)
                        VALUES (%s, %s, %s::jsonb, now(), now())
                        """,
                        (
                            str(payload[key]),
                            str(payload.get("environment_id", environment_id)),
                            json_dumps(payload),
                        ),
                    )
            connection.commit()

    def list_records(self, table_name: str, model: type[ModelT], environment_id: str | None = None) -> list[ModelT]:
        if not self.enabled:
            return []
        sql = f"SELECT data FROM {table_name}"
        params: tuple[str, ...] = ()
        if environment_id:
            sql = f"{sql} WHERE environment_id = %s"
            params = (environment_id,)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                return [model.model_validate(row[0]) for row in cursor.fetchall()]

    def delete_record(self, table_name: str, record_id: str) -> None:
        if not self.enabled:
            return
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (record_id,))
            connection.commit()

    def purge_environment(self, environment_id: str, *, keep_tables: set[str] | None = None) -> None:
        if not self.enabled:
            return
        protected_tables = keep_tables or set()
        with self._connect() as connection:
            with connection.cursor() as cursor:
                for table_name in ENTITY_TABLES:
                    if table_name in protected_tables:
                        continue
                    cursor.execute(f"DELETE FROM {table_name} WHERE environment_id = %s", (environment_id,))
            connection.commit()

    def platform_health(self, scheduler_status: dict[str, object], environment_count: int) -> dict[str, object]:
        status = self.status()
        status.update(
            {
                "database_path": None,
                "connection_status": self.connection_status(),
                "writable": self.writable(),
                "scheduler": scheduler_status,
                "environment_count": environment_count,
                "metrics": self.metrics(),
            }
        )
        return status

    def connection_status(self) -> str:
        if not self.enabled:
            return "unavailable"
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            return "connected"
        except Exception:
            return "unavailable"

    def writable(self) -> bool:
        if not self.enabled:
            return False
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("CREATE TABLE IF NOT EXISTS __healthcheck (id TEXT PRIMARY KEY)")
                    cursor.execute("INSERT INTO __healthcheck (id) VALUES ('write') ON CONFLICT (id) DO NOTHING")
                connection.commit()
            return True
        except Exception:
            return False

    def metrics(self) -> dict[str, object]:
        if not self.enabled:
            return {"database_size_bytes": None, "record_counts": {}}
        counts: dict[str, int] = {}
        with self._connect() as connection:
            with connection.cursor() as cursor:
                for table_name in ENTITY_TABLES:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    counts[table_name] = int(cursor.fetchone()[0])
        return {"database_size_bytes": None, "record_counts": counts}

    def backup(self, retention: int = 10) -> dict[str, object]:
        raise NotImplementedError("platform backup is available for embedded SQLite only")

    def list_backups(self) -> list[dict[str, object]]:
        return []

    def restore(self, filename: str) -> dict[str, object]:
        raise NotImplementedError("platform restore is available for embedded SQLite only")

    def cleanup_backups(self, retention: int = 10) -> int:
        return 0

    def cleanup_stale_telemetry(self, max_records: int = 5000) -> int:
        return 0

    def status(self) -> dict[str, object]:
        return {
            "backend": self.backend_name,
            "enabled": self.enabled,
            "configured": bool(self.database_url),
            "driver_available": psycopg is not None,
        }

    def _connect(self) -> Any:
        if not self.enabled:
            raise RuntimeError("PostgreSQL persistence is not enabled")
        return psycopg.connect(self.database_url)
