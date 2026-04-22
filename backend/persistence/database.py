from __future__ import annotations

import os

from persistence.postgres import PostgresStore
from persistence.sqlite import SQLiteStore


def build_store() -> PostgresStore | SQLiteStore:
    """Select PostgreSQL when DATABASE_URL is set, otherwise use embedded SQLite."""

    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return PostgresStore(database_url)
    return SQLiteStore()


db = build_store()
