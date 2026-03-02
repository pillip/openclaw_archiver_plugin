"""Tests for schema_v1 and migrations modules."""

import sqlite3

import pytest

from openclaw_archiver.migrations import (
    MIGRATIONS,
    TARGET_VERSION,
    _get_user_version,
    run_migrations,
)
from openclaw_archiver.schema_v1 import SCHEMA_SQL


@pytest.fixture
def db() -> sqlite3.Connection:
    """In-memory SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


class TestSchemaV1:
    """Verify SCHEMA_SQL content."""

    def test_schema_contains_projects_table(self) -> None:
        assert "CREATE TABLE IF NOT EXISTS projects" in SCHEMA_SQL

    def test_schema_contains_archives_table(self) -> None:
        assert "CREATE TABLE IF NOT EXISTS archives" in SCHEMA_SQL

    def test_schema_contains_three_indexes(self) -> None:
        assert "idx_archives_user" in SCHEMA_SQL
        assert "idx_archives_user_project" in SCHEMA_SQL
        assert "idx_archives_title" in SCHEMA_SQL

    def test_schema_contains_unique_constraint(self) -> None:
        assert "UNIQUE(user_id, name)" in SCHEMA_SQL

    def test_schema_sets_user_version(self) -> None:
        assert "PRAGMA user_version = 1" in SCHEMA_SQL


class TestMigrations:
    """Verify run_migrations behavior."""

    def test_fresh_db_gets_version_1(self, db: sqlite3.Connection) -> None:
        assert _get_user_version(db) == 0
        run_migrations(db)
        assert _get_user_version(db) == 1

    def test_idempotent_rerun(self, db: sqlite3.Connection) -> None:
        run_migrations(db)
        run_migrations(db)  # should not raise
        assert _get_user_version(db) == 1

    def test_projects_insert_select(self, db: sqlite3.Connection) -> None:
        run_migrations(db)
        db.execute(
            "INSERT INTO projects (user_id, name) VALUES (?, ?)",
            ("U001", "Backend"),
        )
        row = db.execute(
            "SELECT user_id, name FROM projects WHERE user_id = ?", ("U001",)
        ).fetchone()
        assert row == ("U001", "Backend")

    def test_archives_insert_select(self, db: sqlite3.Connection) -> None:
        run_migrations(db)
        db.execute(
            "INSERT INTO archives (user_id, title, link) VALUES (?, ?, ?)",
            ("U001", "회의록", "https://slack.com/archives/C01/p123"),
        )
        row = db.execute(
            "SELECT user_id, title, link FROM archives WHERE user_id = ?",
            ("U001",),
        ).fetchone()
        assert row == ("U001", "회의록", "https://slack.com/archives/C01/p123")

    def test_archives_with_project_fk(self, db: sqlite3.Connection) -> None:
        run_migrations(db)
        db.execute(
            "INSERT INTO projects (user_id, name) VALUES (?, ?)",
            ("U001", "Backend"),
        )
        project_id = db.execute(
            "SELECT id FROM projects WHERE user_id = ? AND name = ?",
            ("U001", "Backend"),
        ).fetchone()[0]
        db.execute(
            "INSERT INTO archives (user_id, project_id, title, link) VALUES (?, ?, ?, ?)",
            ("U001", project_id, "회의록", "https://slack.com/archives/C01/p123"),
        )
        row = db.execute(
            "SELECT project_id FROM archives WHERE user_id = ?", ("U001",)
        ).fetchone()
        assert row[0] == project_id

    def test_unique_constraint_on_projects(self, db: sqlite3.Connection) -> None:
        run_migrations(db)
        db.execute(
            "INSERT INTO projects (user_id, name) VALUES (?, ?)",
            ("U001", "Backend"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO projects (user_id, name) VALUES (?, ?)",
                ("U001", "Backend"),
            )

    def test_unique_allows_different_users_same_name(
        self, db: sqlite3.Connection
    ) -> None:
        run_migrations(db)
        db.execute(
            "INSERT INTO projects (user_id, name) VALUES (?, ?)",
            ("U001", "Backend"),
        )
        db.execute(
            "INSERT INTO projects (user_id, name) VALUES (?, ?)",
            ("U002", "Backend"),
        )
        count = db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        assert count == 2

    def test_archives_null_project_id(self, db: sqlite3.Connection) -> None:
        run_migrations(db)
        db.execute(
            "INSERT INTO archives (user_id, title, link) VALUES (?, ?, ?)",
            ("U001", "미분류 메세지", "https://slack.com/archives/C01/p999"),
        )
        row = db.execute(
            "SELECT project_id FROM archives WHERE user_id = ?", ("U001",)
        ).fetchone()
        assert row[0] is None

    def test_target_version_equals_max_migration(self) -> None:
        assert TARGET_VERSION == max(MIGRATIONS)

    def test_foreign_key_violation(self, db: sqlite3.Connection) -> None:
        run_migrations(db)
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO archives (user_id, project_id, title, link) "
                "VALUES (?, ?, ?, ?)",
                ("U001", 9999, "orphan", "https://slack.com/test"),
            )
