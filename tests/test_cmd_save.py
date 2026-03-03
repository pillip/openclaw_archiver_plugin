"""Tests for cmd_save — /archive save handler."""

from __future__ import annotations

import os

from openclaw_archiver.cmd_save import handle
from openclaw_archiver.db import get_connection

_USAGE = "사용법: /archive save <제목> <링크> [/p <프로젝트>]"
_USER = "U_TEST_SAVE"


def _make_db(tmp_path: object) -> str:
    """Create a temporary DB and return its path."""
    db_path = os.path.join(str(tmp_path), "test.sqlite3")
    conn = get_connection(db_path)
    conn.close()
    return db_path


class TestSaveHappyPath:
    """Verify successful save scenarios."""

    def test_save_title_and_link(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _make_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("스프린트 회의록 https://slack.com/archives/C01/p123", _USER)

        assert "저장했습니다." in result
        assert "ID:" in result
        assert "스프린트 회의록" in result
        assert "프로젝트:" not in result

    def test_save_with_project(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _make_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle(
            "회의록 https://slack.com/archives/C01/p123 /p Backend", _USER
        )

        assert "저장했습니다." in result
        assert "회의록" in result
        assert "프로젝트: Backend" in result

    def test_save_creates_project_automatically(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _make_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        handle("제목 https://example.com /p NewProject", _USER)

        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT name FROM projects WHERE user_id = ? AND name = ?",
            (_USER, "NewProject"),
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "NewProject"

    def test_save_uses_existing_project(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _make_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        # Save twice with same project.
        handle("첫번째 https://example.com/1 /p Backend", _USER)
        handle("두번째 https://example.com/2 /p Backend", _USER)

        conn = get_connection(db_path)
        projects = conn.execute(
            "SELECT COUNT(*) FROM projects WHERE user_id = ? AND name = ?",
            (_USER, "Backend"),
        ).fetchone()
        archives = conn.execute(
            "SELECT COUNT(*) FROM archives WHERE user_id = ?", (_USER,)
        ).fetchone()
        conn.close()
        assert projects[0] == 1  # Only one project created.
        assert archives[0] == 2  # Two archives saved.

    def test_save_without_project_stores_null(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _make_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        handle("제목 https://example.com", _USER)

        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT project_id FROM archives WHERE user_id = ?", (_USER,)
        ).fetchone()
        conn.close()
        assert row[0] is None

    def test_save_records_user_id(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _make_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        handle("제목 https://example.com", _USER)

        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT user_id FROM archives WHERE user_id = ?", (_USER,)
        ).fetchone()
        conn.close()
        assert row[0] == _USER

    def test_save_response_contains_id(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _make_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("제목 https://example.com", _USER)

        # Extract ID from response like "저장했습니다. (ID: 1)"
        assert "(ID: " in result

    def test_save_title_with_spaces(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _make_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle(
            "3월 스프린트 회의록 https://slack.com/archives/C01/p123", _USER
        )

        assert "3월 스프린트 회의록" in result

        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT title FROM archives WHERE user_id = ?", (_USER,)
        ).fetchone()
        conn.close()
        assert row[0] == "3월 스프린트 회의록"


class TestSaveValidation:
    """Verify error handling for missing arguments."""

    def test_missing_title_and_link(self) -> None:
        result = handle("", _USER)
        assert result == _USAGE

    def test_missing_link(self) -> None:
        result = handle("제목만", _USER)
        assert result == _USAGE

    def test_missing_title(self) -> None:
        # Only a URL, no title.
        result = handle("https://example.com", _USER)
        assert result == _USAGE

    def test_whitespace_only(self) -> None:
        result = handle("   ", _USER)
        assert result == _USAGE
