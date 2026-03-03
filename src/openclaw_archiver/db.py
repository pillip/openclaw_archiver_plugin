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


def find_project(
    conn: sqlite3.Connection, user_id: str, name: str
) -> tuple[int, str] | None:
    """Find a project by user_id and name. Returns (id, name) or None."""
    row = conn.execute(
        "SELECT id, name FROM projects WHERE user_id = ? AND name = ?",
        (user_id, name),
    ).fetchone()
    return (row[0], row[1]) if row else None


def list_archives(conn: sqlite3.Connection, user_id: str) -> list[tuple]:
    """List all archives for a user, newest first."""
    return conn.execute(
        "SELECT a.id, a.title, a.link, p.name, a.created_at "
        "FROM archives a "
        "LEFT JOIN projects p ON a.project_id = p.id "
        "WHERE a.user_id = ? "
        "ORDER BY a.created_at DESC",
        (user_id,),
    ).fetchall()


def list_archives_by_project(
    conn: sqlite3.Connection, user_id: str, project_id: int
) -> list[tuple]:
    """List archives for a user filtered by project, newest first."""
    return conn.execute(
        "SELECT a.id, a.title, a.link, a.created_at "
        "FROM archives a "
        "WHERE a.user_id = ? AND a.project_id = ? "
        "ORDER BY a.created_at DESC",
        (user_id, project_id),
    ).fetchall()


def search_archives(
    conn: sqlite3.Connection, user_id: str, keyword: str
) -> list[tuple]:
    """Search archives by title keyword (case-insensitive), newest first."""
    return conn.execute(
        "SELECT a.id, a.title, a.link, p.name, a.created_at "
        "FROM archives a "
        "LEFT JOIN projects p ON a.project_id = p.id "
        "WHERE a.user_id = ? AND a.title LIKE ? COLLATE NOCASE "
        "ORDER BY a.created_at DESC",
        (user_id, f"%{keyword}%"),
    ).fetchall()


def search_archives_by_project(
    conn: sqlite3.Connection, user_id: str, project_id: int, keyword: str
) -> list[tuple]:
    """Search archives by keyword within a project (case-insensitive)."""
    return conn.execute(
        "SELECT a.id, a.title, a.link, a.created_at "
        "FROM archives a "
        "WHERE a.user_id = ? AND a.project_id = ? "
        "AND a.title LIKE ? COLLATE NOCASE "
        "ORDER BY a.created_at DESC",
        (user_id, project_id, f"%{keyword}%"),
    ).fetchall()


def get_archive_title(
    conn: sqlite3.Connection, archive_id: int, user_id: str
) -> str | None:
    """Get the title of an archive owned by user_id, or None if not found."""
    row = conn.execute(
        "SELECT title FROM archives WHERE id = ? AND user_id = ?",
        (archive_id, user_id),
    ).fetchone()
    return row[0] if row else None


def update_archive_title(
    conn: sqlite3.Connection, archive_id: int, user_id: str, new_title: str
) -> bool:
    """Update archive title. Returns True if a row was updated."""
    cur = conn.execute(
        "UPDATE archives SET title = ? WHERE id = ? AND user_id = ?",
        (new_title, archive_id, user_id),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_archive(
    conn: sqlite3.Connection, archive_id: int, user_id: str
) -> bool:
    """Delete an archive owned by user_id. Returns True if a row was deleted."""
    cur = conn.execute(
        "DELETE FROM archives WHERE id = ? AND user_id = ?",
        (archive_id, user_id),
    )
    conn.commit()
    return cur.rowcount > 0


def list_projects(
    conn: sqlite3.Connection, user_id: str
) -> list[tuple[str, int]]:
    """List projects with archive counts for a user.

    Returns list of (name, archive_count) tuples.
    """
    return conn.execute(
        "SELECT p.name, COUNT(a.id) AS archive_count "
        "FROM projects p "
        "LEFT JOIN archives a ON p.id = a.project_id AND a.user_id = ? "
        "WHERE p.user_id = ? "
        "GROUP BY p.id, p.name "
        "ORDER BY p.name",
        (user_id, user_id),
    ).fetchall()
