"""Tests for db module — connection management."""

import os
import sqlite3

import pytest

from openclaw_archiver.db import get_connection


class TestGetConnection:
    """Verify get_connection behavior."""

    def test_wal_mode_enabled(self, tmp_path: object) -> None:
        db_path = os.path.join(str(tmp_path), "test.sqlite3")
        conn = get_connection(db_path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
        conn.close()

    def test_foreign_keys_enabled(self, tmp_path: object) -> None:
        db_path = os.path.join(str(tmp_path), "test.sqlite3")
        conn = get_connection(db_path)
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1
        conn.close()

    def test_schema_initialized(self, tmp_path: object) -> None:
        db_path = os.path.join(str(tmp_path), "test.sqlite3")
        conn = get_connection(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "archives" in table_names
        assert "projects" in table_names
        conn.close()

    def test_auto_creates_parent_directories(self, tmp_path: object) -> None:
        db_path = os.path.join(str(tmp_path), "deep", "nested", "dir", "test.sqlite3")
        conn = get_connection(db_path)
        assert os.path.exists(db_path)
        conn.close()

    def test_env_var_override(self, tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
        db_path = os.path.join(str(tmp_path), "env_override.sqlite3")
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)
        conn = get_connection()
        assert os.path.exists(db_path)
        conn.close()

    def test_explicit_path_takes_precedence_over_env(
        self, tmp_path: object, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        env_path = os.path.join(str(tmp_path), "env.sqlite3")
        explicit_path = os.path.join(str(tmp_path), "explicit.sqlite3")
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", env_path)
        conn = get_connection(explicit_path)
        assert os.path.exists(explicit_path)
        assert not os.path.exists(env_path)
        conn.close()

    def test_user_version_set(self, tmp_path: object) -> None:
        db_path = os.path.join(str(tmp_path), "test.sqlite3")
        conn = get_connection(db_path)
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == 1
        conn.close()

    def test_connection_is_usable(self, tmp_path: object) -> None:
        db_path = os.path.join(str(tmp_path), "test.sqlite3")
        conn = get_connection(db_path)
        conn.execute(
            "INSERT INTO projects (user_id, name) VALUES (?, ?)",
            ("U001", "Test"),
        )
        row = conn.execute(
            "SELECT name FROM projects WHERE user_id = ?", ("U001",)
        ).fetchone()
        assert row[0] == "Test"
        conn.close()
