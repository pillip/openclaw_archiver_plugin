"""Tests for cmd_edit — /archive edit handler."""

from __future__ import annotations

import os

from openclaw_archiver.cmd_edit import handle
from openclaw_archiver.db import get_connection, insert_archive

_USER_A = "U_EDIT_A"
_USER_B = "U_EDIT_B"
_USAGE = "사용법: /archive edit <ID> <새 제목>"


def _seed_db(tmp_path: object) -> str:
    db_path = os.path.join(str(tmp_path), "test.sqlite3")
    conn = get_connection(db_path)
    insert_archive(conn, _USER_A, None, "원래 제목", "https://example.com/1")
    insert_archive(conn, _USER_B, None, "B의 메시지", "https://example.com/2")
    conn.close()
    return db_path


class TestEditHappyPath:
    """Verify successful edit scenarios."""

    def test_edit_success(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("1 새로운 제목", _USER_A)

        assert "제목을 수정했습니다. (ID: 1)" in result
        assert "원래 제목 → 새로운 제목" in result

    def test_edit_updates_db(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        handle("1 수정된 제목", _USER_A)

        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT title FROM archives WHERE id = 1"
        ).fetchone()
        conn.close()
        assert row[0] == "수정된 제목"

    def test_edit_with_spaces_in_title(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("1 3월 스프린트 회의록 (수정)", _USER_A)

        assert "3월 스프린트 회의록 (수정)" in result


class TestEditErrors:
    """Verify error handling."""

    def test_edit_other_user_message(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("2 해킹시도", _USER_A)

        assert result == "해당 메세지를 찾을 수 없습니다. (ID: 2)"

    def test_edit_nonexistent_id(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("999 새제목", _USER_A)

        assert result == "해당 메세지를 찾을 수 없습니다. (ID: 999)"

    def test_edit_non_numeric_id(self) -> None:
        result = handle("abc 새제목", _USER_A)
        assert result == "ID는 숫자여야 합니다. 사용법: /archive edit <ID> <새 제목>"

    def test_edit_missing_new_title(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("1", _USER_A)
        assert result == _USAGE

    def test_edit_empty_args(self) -> None:
        result = handle("", _USER_A)
        assert result == _USAGE

    def test_edit_id_only_with_spaces(self) -> None:
        result = handle("1   ", _USER_A)
        assert result == _USAGE
