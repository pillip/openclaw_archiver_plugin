"""NFR-008 mrkdwn compliance tests.

Validates that all command responses conform to Slack mrkdwn formatting rules:
- No 4+ space indentation in output
- No backticks in output
- No bare URLs (all URLs wrapped in Slack link format <url|text>)
- Slack link format present where URLs appear
"""

from __future__ import annotations

import os
import re

import pytest

from openclaw_archiver.plugin import handle_message

_USER = "U_MRKDWN_TEST"

# Patterns that should NOT appear in any output.
_FOUR_SPACE_INDENT = re.compile(r"^ {4,}", re.MULTILINE)
_BACKTICK = re.compile(r"`")
_BARE_URL = re.compile(r"(?<![<|])https?://\S+(?![>|])")

# Pattern that SHOULD appear when URLs are present.
_SLACK_LINK = re.compile(r"<https?://[^|>]+\|[^>]+>")


@pytest.fixture(autouse=True)
def _mrkdwn_db(tmp_path, monkeypatch):
    """Set up a temporary DB for mrkdwn compliance tests."""
    from openclaw_archiver.db import get_connection

    db_path = os.path.join(str(tmp_path), "mrkdwn.sqlite3")
    conn = get_connection(db_path)
    conn.close()
    monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)


def _assert_no_indentation(text: str, context: str) -> None:
    """Assert no 4+ space indentation exists in text."""
    match = _FOUR_SPACE_INDENT.search(text)
    assert match is None, (
        f"Found 4+ space indentation in {context}: "
        f"line={text.splitlines()[text[:match.start()].count(chr(10))]!r}"
    )


def _assert_no_backticks(text: str, context: str) -> None:
    """Assert no backticks exist in text."""
    assert "`" not in text, f"Found backtick in {context}: {text!r}"


def _assert_no_bare_urls(text: str, context: str) -> None:
    """Assert no bare URLs exist (all should be Slack link format)."""
    match = _BARE_URL.search(text)
    assert match is None, (
        f"Found bare URL in {context}: {match.group()!r}"
    )


class TestSaveMrkdwn:
    """NFR-008: save command responses use mrkdwn."""

    def test_save_no_indentation(self) -> None:
        resp = handle_message(
            "/archive save 테스트메모 https://slack.com/a/1", _USER
        )
        assert resp is not None
        _assert_no_indentation(resp, "save response")
        _assert_no_backticks(resp, "save response")

    def test_save_with_project_no_indentation(self) -> None:
        resp = handle_message(
            "/archive save 메모 https://slack.com/a/2 /p TestProj", _USER
        )
        assert resp is not None
        _assert_no_indentation(resp, "save with project response")
        _assert_no_backticks(resp, "save with project response")

    def test_save_bold_labels(self) -> None:
        resp = handle_message(
            "/archive save 볼드테스트 https://slack.com/a/3 /p BoldProj", _USER
        )
        assert resp is not None
        assert "*제목:*" in resp
        assert "*프로젝트:*" in resp


class TestListMrkdwn:
    """NFR-008: list command responses use mrkdwn."""

    def test_list_no_indentation(self) -> None:
        handle_message(
            "/archive save 목록테스트 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive list", _USER)
        assert resp is not None
        _assert_no_indentation(resp, "list response")
        _assert_no_backticks(resp, "list response")

    def test_list_no_bare_urls(self) -> None:
        handle_message(
            "/archive save 링크테스트 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive list", _USER)
        assert resp is not None
        _assert_no_bare_urls(resp, "list response")

    def test_list_has_slack_links(self) -> None:
        handle_message(
            "/archive save 슬랙링크 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive list", _USER)
        assert resp is not None
        assert _SLACK_LINK.search(resp), f"No Slack link format found in: {resp}"

    def test_list_bold_header(self) -> None:
        handle_message(
            "/archive save 헤더테스트 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive list", _USER)
        assert resp is not None
        assert "*저장된 메세지*" in resp

    def test_list_by_project_bold_header(self) -> None:
        handle_message(
            "/archive save 프로젝트테스트 https://slack.com/a/1 /p MyProj", _USER
        )
        resp = handle_message("/archive list /p MyProj", _USER)
        assert resp is not None
        assert "*저장된 메세지 — MyProj*" in resp

    def test_list_separator_is_short(self) -> None:
        handle_message(
            "/archive save 구분선 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive list", _USER)
        assert resp is not None
        assert "───" in resp


class TestSearchMrkdwn:
    """NFR-008: search command responses use mrkdwn."""

    def test_search_no_indentation(self) -> None:
        handle_message(
            "/archive save 검색대상 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive search 검색", _USER)
        assert resp is not None
        _assert_no_indentation(resp, "search response")
        _assert_no_backticks(resp, "search response")

    def test_search_no_bare_urls(self) -> None:
        handle_message(
            "/archive save 검색링크 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive search 검색", _USER)
        assert resp is not None
        _assert_no_bare_urls(resp, "search response")

    def test_search_bold_header(self) -> None:
        handle_message(
            "/archive save 검색볼드 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive search 검색", _USER)
        assert resp is not None
        assert re.search(r'\*검색 결과: ".+"\*', resp), f"No bold header in: {resp}"


class TestEditMrkdwn:
    """NFR-008: edit command responses use mrkdwn."""

    def test_edit_no_indentation(self) -> None:
        handle_message(
            "/archive save 수정전 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive edit 1 수정후", _USER)
        assert resp is not None
        _assert_no_indentation(resp, "edit response")
        _assert_no_backticks(resp, "edit response")

    def test_edit_bold_label(self) -> None:
        handle_message(
            "/archive save 원래제목 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive edit 1 새제목", _USER)
        assert resp is not None
        assert "*변경:*" in resp


class TestRemoveMrkdwn:
    """NFR-008: remove command responses use mrkdwn."""

    def test_remove_no_indentation(self) -> None:
        handle_message(
            "/archive save 삭제대상 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive remove 1", _USER)
        assert resp is not None
        _assert_no_indentation(resp, "remove response")
        _assert_no_backticks(resp, "remove response")

    def test_remove_bold_label(self) -> None:
        handle_message(
            "/archive save 삭제제목 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive remove 1", _USER)
        assert resp is not None
        assert "*제목:*" in resp


class TestProjectListMrkdwn:
    """NFR-008: project list command responses use mrkdwn."""

    def test_project_list_no_indentation(self) -> None:
        handle_message(
            "/archive save 메모 https://slack.com/a/1 /p Proj1", _USER
        )
        resp = handle_message("/archive project list", _USER)
        assert resp is not None
        _assert_no_indentation(resp, "project list response")
        _assert_no_backticks(resp, "project list response")

    def test_project_list_bold_header(self) -> None:
        handle_message(
            "/archive save 메모 https://slack.com/a/1 /p Proj1", _USER
        )
        resp = handle_message("/archive project list", _USER)
        assert resp is not None
        assert "*프로젝트*" in resp

    def test_project_list_em_dash_format(self) -> None:
        handle_message(
            "/archive save 메모 https://slack.com/a/1 /p Proj1", _USER
        )
        resp = handle_message("/archive project list", _USER)
        assert resp is not None
        assert "Proj1 — 1건" in resp


class TestProjectRenameMrkdwn:
    """NFR-008: project rename command responses use mrkdwn."""

    def test_rename_no_indentation(self) -> None:
        handle_message(
            "/archive save 메모 https://slack.com/a/1 /p OldName", _USER
        )
        resp = handle_message("/archive project rename OldName NewName", _USER)
        assert resp is not None
        _assert_no_indentation(resp, "project rename response")
        _assert_no_backticks(resp, "project rename response")

    def test_rename_bold_label(self) -> None:
        handle_message(
            "/archive save 메모 https://slack.com/a/1 /p RenameOld", _USER
        )
        resp = handle_message("/archive project rename RenameOld RenameNew", _USER)
        assert resp is not None
        assert "*변경:*" in resp


class TestProjectDeleteMrkdwn:
    """NFR-008: project delete command responses use mrkdwn."""

    def test_delete_no_indentation(self) -> None:
        handle_message(
            "/archive save 메모 https://slack.com/a/1 /p DelProj", _USER
        )
        resp = handle_message("/archive project delete DelProj", _USER)
        assert resp is not None
        _assert_no_indentation(resp, "project delete response")
        _assert_no_backticks(resp, "project delete response")


class TestHelpMrkdwn:
    """NFR-008: help command response uses mrkdwn."""

    def test_help_no_indentation(self) -> None:
        resp = handle_message("/archive help", _USER)
        assert resp is not None
        _assert_no_indentation(resp, "help response")
        _assert_no_backticks(resp, "help response")

    def test_help_bold_title(self) -> None:
        resp = handle_message("/archive help", _USER)
        assert resp is not None
        assert "*/archive 사용법*" in resp

    def test_help_bold_section_headers(self) -> None:
        resp = handle_message("/archive help", _USER)
        assert resp is not None
        assert "*프로젝트 관리*" in resp

    def test_help_bold_command_labels(self) -> None:
        resp = handle_message("/archive help", _USER)
        assert resp is not None
        assert "*저장*" in resp
        assert "*목록*" in resp
        assert "*검색*" in resp
        assert "*수정*" in resp
        assert "*삭제*" in resp
        assert "*이름변경*" in resp

    def test_help_short_separator(self) -> None:
        resp = handle_message("/archive help", _USER)
        assert resp is not None
        assert "───" in resp
