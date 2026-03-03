"""Tests for cmd_remove — /archive remove handler."""

from __future__ import annotations

import os

from openclaw_archiver.cmd_remove import handle
from openclaw_archiver.db import get_connection, insert_archive

_USER_A = "U_REMOVE_A"
_USER_B = "U_REMOVE_B"
_USAGE = "사용법: /archive remove <ID>"


def _seed_db(tmp_path: object) -> str:
    db_path = os.path.join(str(tmp_path), "test.sqlite3")
    conn = get_connection(db_path)
    insert_archive(conn, _USER_A, None, "스프린트 회의록 (3월)", "https://example.com/1")
    insert_archive(conn, _USER_B, None, "B의 메시지", "https://example.com/2")
    conn.close()
    return db_path


class TestRemoveHappyPath:
    """Verify successful remove scenarios."""

    def test_remove_success(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("1", _USER_A)

        assert "삭제했습니다. (ID: 1)" in result
        assert "스프린트 회의록 (3월)" in result

    def test_remove_deletes_from_db(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        handle("1", _USER_A)

        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT id FROM archives WHERE id = 1"
        ).fetchone()
        conn.close()
        assert row is None

    def test_remove_response_includes_title(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("1", _USER_A)

        assert "스프린트 회의록 (3월)" in result


class TestRemoveErrors:
    """Verify error handling."""

    def test_remove_other_user_message(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("2", _USER_A)

        assert result == "해당 메세지를 찾을 수 없습니다. (ID: 2)"

    def test_remove_nonexistent_id(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("999", _USER_A)

        assert result == "해당 메세지를 찾을 수 없습니다. (ID: 999)"

    def test_remove_non_numeric_id(self) -> None:
        result = handle("abc", _USER_A)
        assert result == "ID는 숫자여야 합니다. 사용법: /archive remove <ID>"

    def test_remove_empty_args(self) -> None:
        result = handle("", _USER_A)
        assert result == _USAGE

    def test_remove_whitespace_only(self) -> None:
        result = handle("   ", _USER_A)
        assert result == _USAGE
