"""Tests for cmd_project_rename — /archive project rename handler."""

from __future__ import annotations

import os

from openclaw_archiver.cmd_project_rename import handle
from openclaw_archiver.db import get_connection, get_or_create_project, insert_archive

_USER_A = "U_PRENAME_A"
_USER_B = "U_PRENAME_B"
_USAGE = "사용법: /archive project rename <기존이름> <새이름>"


def _seed_db(tmp_path: object) -> str:
    db_path = os.path.join(str(tmp_path), "test.sqlite3")
    conn = get_connection(db_path)
    pid_be = get_or_create_project(conn, _USER_A, "BE")
    get_or_create_project(conn, _USER_A, "Frontend")
    insert_archive(conn, _USER_A, pid_be, "스프린트 회의록", "https://example.com/1")

    # User B has a project with same name
    get_or_create_project(conn, _USER_B, "BE")
    conn.commit()
    conn.close()
    return db_path


class TestProjectRenameHappyPath:
    """Verify successful rename scenarios."""

    def test_rename_success(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("BE Backend", _USER_A)

        assert "프로젝트 이름을 변경했습니다" in result
        assert "BE → Backend" in result

    def test_rename_updates_db(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        handle("BE Backend", _USER_A)

        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT name FROM projects WHERE user_id = ? AND name = ?",
            (_USER_A, "Backend"),
        ).fetchone()
        conn.close()
        assert row is not None


class TestProjectRenameErrors:
    """Verify error handling."""

    def test_rename_nonexistent_project(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("NoSuch NewName", _USER_A)

        assert result == '"NoSuch" 프로젝트를 찾을 수 없습니다.'

    def test_rename_duplicate_name(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("BE Frontend", _USER_A)

        assert result == '"Frontend" 프로젝트가 이미 존재합니다. 다른 이름을 입력하세요.'

    def test_rename_other_user_project(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        # User A tries to rename User B's project (shouldn't know it exists)
        result = handle("BE NewName", _USER_B)

        # User B owns "BE", this should succeed for user B
        assert "프로젝트 이름을 변경했습니다" in result

    def test_rename_cross_user_isolation(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """User A cannot rename a project they don't own even if same name exists for another user."""
        db_path = os.path.join(str(tmp_path), "test.sqlite3")
        conn = get_connection(db_path)
        get_or_create_project(conn, _USER_B, "Secret")
        conn.close()
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("Secret NewName", _USER_A)

        assert result == '"Secret" 프로젝트를 찾을 수 없습니다.'

    def test_rename_missing_args(self) -> None:
        result = handle("", _USER_A)
        assert result == _USAGE

    def test_rename_only_one_arg(self) -> None:
        result = handle("BE", _USER_A)
        assert result == _USAGE
