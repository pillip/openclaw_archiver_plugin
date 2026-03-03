"""Tests for cmd_list — /archive list handler."""

from __future__ import annotations

import os

from openclaw_archiver.cmd_list import handle
from openclaw_archiver.db import get_connection, get_or_create_project, insert_archive

_USER_A = "U_LIST_A"
_USER_B = "U_LIST_B"


def _seed_db(tmp_path: object) -> str:
    """Create and seed a temporary DB, return path."""
    db_path = os.path.join(str(tmp_path), "test.sqlite3")
    conn = get_connection(db_path)

    # User A: 2 projects, 3 archives.
    pid_be = get_or_create_project(conn, _USER_A, "Backend")
    insert_archive(conn, _USER_A, pid_be, "스프린트 회의록", "https://slack.com/C01/p001")
    insert_archive(conn, _USER_A, pid_be, "코드 리뷰 가이드", "https://slack.com/C01/p002")
    insert_archive(conn, _USER_A, None, "미분류 메모", "https://slack.com/C02/p003")

    # User B: separate data.
    pid_be_b = get_or_create_project(conn, _USER_B, "Backend")
    insert_archive(conn, _USER_B, pid_be_b, "B의 회의록", "https://slack.com/C04/p005")

    conn.close()
    return db_path


class TestListAll:
    """Verify /archive list (all archives)."""

    def test_list_all_returns_user_archives(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("", _USER_A)

        assert "저장된 메세지 (3건)" in result
        assert "스프린트 회의록" in result
        assert "코드 리뷰 가이드" in result
        assert "미분류 메모" in result

    def test_list_all_excludes_other_user(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("", _USER_A)

        assert "B의 회의록" not in result

    def test_list_all_shows_project_name(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("", _USER_A)

        assert "프로젝트: Backend" in result

    def test_list_all_shows_unclassified(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("", _USER_A)

        assert "미분류" in result

    def test_list_all_contains_id_title_link_date(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("", _USER_A)

        # Check format elements.
        assert "#" in result  # ID prefix
        assert "https://slack.com/" in result  # Link
        assert "─────" in result  # Separator

    def test_list_all_empty(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = os.path.join(str(tmp_path), "empty.sqlite3")
        conn = get_connection(db_path)
        conn.close()
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("", "U_EMPTY")

        assert result == "저장된 메세지가 없습니다. /archive save 로 메세지를 저장해보세요."


class TestListByProject:
    """Verify /archive list /p <project>."""

    def test_list_by_project(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("/p Backend", _USER_A)

        assert "저장된 메세지 — Backend (2건)" in result
        assert "스프린트 회의록" in result
        assert "코드 리뷰 가이드" in result
        assert "미분류 메모" not in result

    def test_list_by_project_excludes_project_label(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("/p Backend", _USER_A)

        # Per UX spec, project-filtered list does NOT repeat project name per item.
        assert "프로젝트: Backend" not in result

    def test_list_nonexistent_project(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("/p NoSuchProject", _USER_A)

        assert result == '"NoSuchProject" 프로젝트를 찾을 수 없습니다.'

    def test_list_project_exists_but_empty(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = os.path.join(str(tmp_path), "empty_proj.sqlite3")
        conn = get_connection(db_path)
        get_or_create_project(conn, _USER_A, "EmptyProject")
        conn.commit()
        conn.close()
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("/p EmptyProject", _USER_A)

        assert result == '"EmptyProject" 프로젝트에 저장된 메세지가 없습니다.'

    def test_list_by_project_other_user_not_visible(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        # User A cannot see User B's "Backend" project.
        result_a = handle("/p Backend", _USER_A)
        result_b = handle("/p Backend", _USER_B)

        assert "B의 회의록" not in result_a
        assert "스프린트 회의록" not in result_b
