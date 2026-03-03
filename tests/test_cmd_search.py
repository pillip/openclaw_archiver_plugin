"""Tests for cmd_search — /archive search handler."""

from __future__ import annotations

import os

from openclaw_archiver.cmd_search import handle
from openclaw_archiver.db import get_connection, get_or_create_project, insert_archive

_USER_A = "U_SEARCH_A"
_USER_B = "U_SEARCH_B"
_USAGE = "사용법: /archive search <키워드> [/p <프로젝트>]"


def _seed_db(tmp_path: object) -> str:
    db_path = os.path.join(str(tmp_path), "test.sqlite3")
    conn = get_connection(db_path)

    pid_be = get_or_create_project(conn, _USER_A, "Backend")
    insert_archive(conn, _USER_A, pid_be, "스프린트 회의록", "https://slack.com/C01/p001")
    insert_archive(conn, _USER_A, pid_be, "코드 리뷰 가이드", "https://slack.com/C01/p002")
    insert_archive(conn, _USER_A, None, "주간 회의록 정리", "https://slack.com/C02/p003")

    pid_be_b = get_or_create_project(conn, _USER_B, "Backend")
    insert_archive(conn, _USER_B, pid_be_b, "B의 회의록", "https://slack.com/C04/p005")

    conn.close()
    return db_path


class TestSearchAll:
    """Verify /archive search <keyword>."""

    def test_search_finds_matching(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("회의록", _USER_A)

        assert '검색 결과: "회의록" (2건)' in result
        assert "스프린트 회의록" in result
        assert "주간 회의록 정리" in result

    def test_search_excludes_other_user(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("회의록", _USER_A)

        assert "B의 회의록" not in result

    def test_search_case_insensitive(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = os.path.join(str(tmp_path), "case.sqlite3")
        conn = get_connection(db_path)
        insert_archive(conn, _USER_A, None, "Review Notes", "https://example.com/1")
        conn.close()
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("review", _USER_A)

        assert "Review Notes" in result

    def test_search_no_results(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("존재하지않는키워드", _USER_A)

        assert result == '"존재하지않는키워드"에 대한 검색 결과가 없습니다.'

    def test_search_shows_project_and_date(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("스프린트", _USER_A)

        assert "프로젝트: Backend" in result
        assert "#" in result


class TestSearchByProject:
    """Verify /archive search <keyword> /p <project>."""

    def test_search_in_project(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("회의록 /p Backend", _USER_A)

        assert '검색 결과: "회의록" — Backend (1건)' in result
        assert "스프린트 회의록" in result
        assert "주간 회의록 정리" not in result

    def test_search_in_project_no_results(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("없는키워드 /p Backend", _USER_A)

        assert result == '"Backend" 프로젝트에서 "없는키워드"에 대한 검색 결과가 없습니다.'

    def test_search_nonexistent_project(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("회의록 /p NoSuch", _USER_A)

        assert result == '"NoSuch" 프로젝트를 찾을 수 없습니다.'

    def test_search_project_excludes_project_label(self, tmp_path: object, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        db_path = _seed_db(tmp_path)
        monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

        result = handle("회의록 /p Backend", _USER_A)

        # Per UX spec, project-scoped results omit per-item project label.
        assert "프로젝트: Backend" not in result


class TestSearchValidation:
    """Verify error handling."""

    def test_missing_keyword(self) -> None:
        assert handle("", _USER_A) == _USAGE

    def test_whitespace_only(self) -> None:
        assert handle("   ", _USER_A) == _USAGE

    def test_only_project_option(self) -> None:
        assert handle("/p Backend", _USER_A) == _USAGE
