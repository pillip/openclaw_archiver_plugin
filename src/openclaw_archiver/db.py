"""SQLite connection management."""

from __future__ import annotations

import os
import sqlite3

from openclaw_archiver.migrations import run_migrations

_DEFAULT_DB_PATH = os.path.join(
    os.path.expanduser("~"),
    ".openclaw",
    "workspace",
    ".archiver",
    "archiver.sqlite3",
)


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Create and return a configured SQLite connection.

    - Reads path from *db_path* arg, then ``OPENCLAW_ARCHIVER_DB_PATH``
      env-var, falling back to the default location.
    - Creates parent directories if they don't exist.
    - Enables WAL journal mode and foreign key enforcement.
    - Runs pending schema migrations.
    """
    path = db_path or os.environ.get("OPENCLAW_ARCHIVER_DB_PATH", _DEFAULT_DB_PATH)

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    run_migrations(conn)

    return conn


def get_or_create_project(conn: sqlite3.Connection, user_id: str, name: str) -> int:
    """Return the project id for *user_id* / *name*, creating it if needed."""
    conn.execute(
        "INSERT OR IGNORE INTO projects (user_id, name) VALUES (?, ?)",
        (user_id, name),
    )
    row = conn.execute(
        "SELECT id FROM projects WHERE user_id = ? AND name = ?",
        (user_id, name),
    ).fetchone()
    return row[0]  # type: ignore[index]


def insert_archive(
    conn: sqlite3.Connection,
    user_id: str,
    project_id: int | None,
    title: str,
    link: str,
) -> int:
    """Insert an archive row and return the new row id."""
    cur = conn.execute(
        "INSERT INTO archives (user_id, project_id, title, link) VALUES (?, ?, ?, ?)",
        (user_id, project_id, title, link),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]
