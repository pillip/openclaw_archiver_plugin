"""Tests for cmd_project_delete — /archive project delete handler."""

from __future__ import annotations

import os

from openclaw_archiver.cmd_project_delete import handle
from openclaw_archiver.db import get_connection, get_or_create_project, insert_archive

_USER_A = "U_PDEL_A"
_USER_B = "U_PDEL_B"
_USAGE = "사용법: /archive project delete <프로젝트이름>"


def _seed_db(tmp_path: object) -> str:
    db_path = os.path.join(str(tmp_path), "test.sqlite3")
    conn = get_connection(db_path)

    # User A: Backend project with 2 archives, EmptyProj with 0
    pid_be = get_or_create_project(conn, _USER_A, "Backend")
    get_or_create_project(conn, _USER_A, "EmptyProj")
    insert_archive(conn, _USER_A, pid_be, "스프린트 회의록", "https://example.com/1")
    insert_archive(conn, _USER_A, pid_be, "코드 리뷰 가이드", "https://example.com/2")
    # User A: one unclassified archive
    insert_archive(conn, _USER_A, None, "미분류 메시지", "https://example.com/3")

    # User B: same project name
    pid_b = get_or_create_project(conn, _USER_B, "Backend")
    insert_archive(conn, _USER_B, pid_b, "B의 메시지", "https://example.com/4")
    conn.commit()
    conn.close()
    return db_path


class TestProjectDeleteHappyPath:
    """Verify successful delete scenarios."""

    def test_delete_with_archives(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("Backend", _USER_A)

        assert '"Backend" 프로젝트를 삭제했습니다.' in result
        assert "2건의 메세지가 미분류로 변경되었습니다." in result

    def test_delete_empty_project(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("EmptyProj", _USER_A)

        assert '"EmptyProj" 프로젝트를 삭제했습니다.' in result
        assert "미분류" not in result

    def test_archives_preserved_after_delete(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        # Count User A's archives before
        conn = get_connection(db_path)
        before = conn.execute(
            "SELECT COUNT(*) FROM archives WHERE user_id = ?", (_USER_A,)
        ).fetchone()[0]
        conn.close()

        handle("Backend", _USER_A)

        # Count after — should be the same
        conn = get_connection(db_path)
        after = conn.execute(
            "SELECT COUNT(*) FROM archives WHERE user_id = ?", (_USER_A,)
        ).fetchone()[0]
        conn.close()
        assert before == after

    def test_archives_unlinked_after_delete(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        handle("Backend", _USER_A)

        conn = get_connection(db_path)
        rows = conn.execute(
            "SELECT project_id FROM archives WHERE user_id = ? AND title = '스프린트 회의록'",
            (_USER_A,),
        ).fetchone()
        conn.close()
        assert rows[0] is None  # project_id is NULL

    def test_project_removed_from_db(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        handle("Backend", _USER_A)

        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT id FROM projects WHERE user_id = ? AND name = 'Backend'",
            (_USER_A,),
        ).fetchone()
        conn.close()
        assert row is None


class TestProjectDeleteErrors:
    """Verify error handling."""

    def test_delete_nonexistent_project(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("NoSuch", _USER_A)

        assert result == '"NoSuch" 프로젝트를 찾을 수 없습니다.'

    def test_delete_other_user_project(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        # User A tries to delete User B's Backend project
        result = handle("Backend", _USER_A)

        # This actually deletes User A's Backend (both exist)
        # So let's test with a project only User B has
        conn = get_connection(db_path)
        get_or_create_project(conn, _USER_B, "SecretProject")
        conn.commit()
        conn.close()

        result = handle("SecretProject", _USER_A)
        assert result == '"SecretProject" 프로젝트를 찾을 수 없습니다.'

    def test_delete_missing_args(self) -> None:
        result = handle("", _USER_A)
        assert result == _USAGE

    def test_delete_whitespace_only(self) -> None:
        result = handle("   ", _USER_A)
        assert result == _USAGE

    def test_other_user_archives_unaffected(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """Deleting User A's Backend doesn't affect User B's Backend archives."""
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        handle("Backend", _USER_A)

        conn = get_connection(db_path)
        # User B's archive should still have its project_id
        row = conn.execute(
            "SELECT project_id FROM archives WHERE user_id = ? AND title = 'B의 메시지'",
            (_USER_B,),
        ).fetchone()
        conn.close()
        assert row[0] is not None  # Still linked to User B's project
