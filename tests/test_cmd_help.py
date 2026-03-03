"""Tests for cmd_help — /archive help handler."""

from __future__ import annotations

from openclaw_archiver.cmd_help import handle


class TestHelp:
    """Verify help output matches UX spec Section 3.9."""

    def test_contains_all_commands(self) -> None:
        result = handle("", "U_TEST")

        assert "/archive save" in result
        assert "/archive list" in result
        assert "/archive search" in result
        assert "/archive edit" in result
        assert "/archive remove" in result

    def test_contains_project_commands(self) -> None:
        result = handle("", "U_TEST")

        assert "/archive project list" in result
        assert "/archive project rename" in result
        assert "/archive project delete" in result

    def test_contains_header_and_separator(self) -> None:
        result = handle("", "U_TEST")

        assert "/archive 사용법" in result
        assert "─────────────────────────────" in result

    def test_contains_project_management_section(self) -> None:
        result = handle("", "U_TEST")

        assert "프로젝트 관리" in result
