"""DB migration engine — PRAGMA user_version based."""

from __future__ import annotations

import sqlite3

from openclaw_archiver.schema_v1 import SCHEMA_SQL

MIGRATIONS: dict[int, dict[str, str]] = {
    1: {
        "up": SCHEMA_SQL,
        "down": (
            "DROP TABLE IF EXISTS archives;"
            " DROP TABLE IF EXISTS projects;"
            " PRAGMA user_version = 0;"
        ),
    },
}

TARGET_VERSION = max(MIGRATIONS)


def _get_user_version(conn: sqlite3.Connection) -> int:
    row = conn.execute("PRAGMA user_version").fetchone()
    return row[0] if row else 0


def run_migrations(conn: sqlite3.Connection) -> None:
    """Apply pending migrations up to TARGET_VERSION.

    Each migration runs via executescript which handles its own
    transaction management. The up script must include
    ``PRAGMA user_version = N;`` as its final statement.
    """
    current = _get_user_version(conn)

    for version in range(current + 1, TARGET_VERSION + 1):
        migration = MIGRATIONS[version]
        conn.executescript(migration["up"])
