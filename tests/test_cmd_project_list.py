"""Tests for cmd_project_list — /archive project list handler."""

from __future__ import annotations

import os

from openclaw_archiver.cmd_project_list import handle
from openclaw_archiver.db import get_connection, get_or_create_project, insert_archive

_USER_A = "U_PLIST_A"
_USER_B = "U_PLIST_B"


def _seed_db(tmp_path: object) -> str:
    db_path = os.path.join(str(tmp_path), "test.sqlite3")
    conn = get_connection(db_path)

    # User A: 2 projects
    pid_backend = get_or_create_project(conn, _USER_A, "Backend")
    pid_frontend = get_or_create_project(conn, _USER_A, "Frontend")
    insert_archive(conn, _USER_A, pid_backend, "스프린트 회의록", "https://example.com/1")
    insert_archive(conn, _USER_A, pid_backend, "코드 리뷰 가이드", "https://example.com/2")
    insert_archive(conn, _USER_A, pid_frontend, "CSS 스타일 가이드", "https://example.com/3")

    # User B: 1 project
    pid_b = get_or_create_project(conn, _USER_B, "Backend")
    insert_archive(conn, _USER_B, pid_b, "B의 메시지", "https://example.com/4")

    conn.close()
    return db_path


class TestProjectListHappyPath:
    """Verify successful project list scenarios."""

    def test_lists_projects_with_counts(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("", _USER_A)

        assert "*프로젝트* (2개)" in result
        assert "Backend" in result
        assert "2건" in result
        assert "Frontend" in result
        assert "1건" in result

    def test_excludes_other_user_projects(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("", _USER_A)

        # User A should see 2 projects, not User B's
        assert "*프로젝트* (2개)" in result

    def test_user_b_sees_own_projects(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("", _USER_B)

        assert "*프로젝트* (1개)" in result
        assert "Backend" in result
        assert "1건" in result

    def test_header_contains_separator(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("", _USER_A)

        assert "───" in result


class TestProjectListEmpty:
    """Verify empty state."""

    def test_empty_projects(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = os.path.join(str(tmp_path), "test.sqlite3")
        conn = get_connection(db_path)
        conn.close()
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("", "U_NOBODY")

        assert "프로젝트가 없습니다" in result
        assert "/archive save" in result
