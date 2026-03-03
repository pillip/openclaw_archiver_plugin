"""Data isolation integration tests — verify user_id-based access control."""

from __future__ import annotations

import os

import pytest

from openclaw_archiver.db import get_connection
from openclaw_archiver.plugin import handle_message

_USER_A = "U_ISO_ALICE"
_USER_B = "U_ISO_BOB"


@pytest.fixture(autouse=True)
def _isolation_db(tmp_path, monkeypatch):
    """Set up a shared temporary DB and seed data for user A."""
    db_path = os.path.join(str(tmp_path), "isolation.sqlite3")
    conn = get_connection(db_path)
    conn.close()
    monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

    # Seed: User A saves two messages (one with project, one without)
    resp = handle_message("/archive save 앨리스메모 https://slack.com/a/1", _USER_A)
    assert resp is not None and "저장했습니다" in resp

    resp = handle_message(
        "/archive save 프로젝트메모 https://slack.com/a/2 /p 앨리스프로젝트",
        _USER_A,
    )
    assert resp is not None and "저장했습니다" in resp

    # Seed: User B saves one message with a different project
    resp = handle_message(
        "/archive save 밥메모 https://slack.com/b/1 /p 밥프로젝트",
        _USER_B,
    )
    assert resp is not None and "저장했습니다" in resp


# ---------------------------------------------------------------------------
# Helper: extract archive ID from a list response line like "  [3] 앨리스메모"
# ---------------------------------------------------------------------------

def _get_first_id(list_response: str) -> str:
    """Extract the first numeric ID from a list/search response.

    Format: ``#1  제목`` — extract the number after ``#``.
    """
    for line in list_response.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            token = stripped.split()[0]  # "#1"
            return token.lstrip("#")
    raise ValueError(f"No ID found in response: {list_response}")


# =========================================================================
# List isolation
# =========================================================================


class TestListIsolation:
    """User B cannot see User A's messages via /archive list."""

    def test_user_b_list_does_not_contain_user_a_messages(self) -> None:
        resp = handle_message("/archive list", _USER_B)
        assert resp is not None
        assert "앨리스메모" not in resp
        assert "프로젝트메모" not in resp

    def test_user_a_list_does_not_contain_user_b_messages(self) -> None:
        resp = handle_message("/archive list", _USER_A)
        assert resp is not None
        assert "밥메모" not in resp

    def test_user_b_list_with_user_a_project_not_found(self) -> None:
        resp = handle_message("/archive list /p 앨리스프로젝트", _USER_B)
        assert resp is not None
        assert "찾을 수 없습니다" in resp


# =========================================================================
# Search isolation
# =========================================================================


class TestSearchIsolation:
    """User B cannot find User A's messages via /archive search."""

    def test_user_b_search_does_not_find_user_a_messages(self) -> None:
        resp = handle_message("/archive search 앨리스", _USER_B)
        assert resp is not None
        assert "앨리스메모" not in resp

    def test_user_a_search_does_not_find_user_b_messages(self) -> None:
        resp = handle_message("/archive search 밥", _USER_A)
        assert resp is not None
        assert "밥메모" not in resp

    def test_user_b_search_in_user_a_project_not_found(self) -> None:
        resp = handle_message("/archive search 메모 /p 앨리스프로젝트", _USER_B)
        assert resp is not None
        assert "찾을 수 없습니다" in resp


# =========================================================================
# Edit isolation
# =========================================================================


class TestEditIsolation:
    """User B cannot edit User A's messages."""

    def test_user_b_edit_user_a_message_fails(self) -> None:
        # Get User A's message ID
        a_list = handle_message("/archive list", _USER_A)
        assert a_list is not None
        a_id = _get_first_id(a_list)

        # User B tries to edit it
        resp = handle_message(f"/archive edit {a_id} 해킹됨", _USER_B)
        assert resp is not None
        assert "찾을 수 없습니다" in resp

    def test_edit_error_same_for_nonexistent_and_other_user(self) -> None:
        """Error for other user's ID must be identical to non-existent ID."""
        # Get User A's message ID
        a_list = handle_message("/archive list", _USER_A)
        assert a_list is not None
        a_id = _get_first_id(a_list)

        # User B tries to edit User A's message
        resp_other = handle_message(f"/archive edit {a_id} 해킹", _USER_B)

        # User B tries to edit a non-existent ID
        resp_none = handle_message("/archive edit 99999 해킹", _USER_B)

        # Both must return the same error pattern (existence non-disclosure)
        assert resp_other is not None
        assert resp_none is not None
        assert "찾을 수 없습니다" in resp_other
        assert "찾을 수 없습니다" in resp_none

    def test_user_a_message_unchanged_after_user_b_edit_attempt(self) -> None:
        """Verify User A's message is actually unchanged after B's attempt."""
        a_list_before = handle_message("/archive list", _USER_A)
        assert a_list_before is not None
        a_id = _get_first_id(a_list_before)

        # User B tries to edit
        handle_message(f"/archive edit {a_id} 변조시도", _USER_B)

        # User A's list should be unchanged
        a_list_after = handle_message("/archive list", _USER_A)
        assert a_list_after is not None
        assert "앨리스메모" in a_list_after
        assert "변조시도" not in a_list_after


# =========================================================================
# Remove isolation
# =========================================================================


class TestRemoveIsolation:
    """User B cannot remove User A's messages."""

    def test_user_b_remove_user_a_message_fails(self) -> None:
        a_list = handle_message("/archive list", _USER_A)
        assert a_list is not None
        a_id = _get_first_id(a_list)

        resp = handle_message(f"/archive remove {a_id}", _USER_B)
        assert resp is not None
        assert "찾을 수 없습니다" in resp

    def test_remove_error_same_for_nonexistent_and_other_user(self) -> None:
        a_list = handle_message("/archive list", _USER_A)
        assert a_list is not None
        a_id = _get_first_id(a_list)

        resp_other = handle_message(f"/archive remove {a_id}", _USER_B)
        resp_none = handle_message("/archive remove 99999", _USER_B)

        assert resp_other is not None
        assert resp_none is not None
        assert "찾을 수 없습니다" in resp_other
        assert "찾을 수 없습니다" in resp_none

    def test_user_a_message_still_exists_after_user_b_remove_attempt(self) -> None:
        a_list = handle_message("/archive list", _USER_A)
        assert a_list is not None
        a_id = _get_first_id(a_list)

        handle_message(f"/archive remove {a_id}", _USER_B)

        a_list_after = handle_message("/archive list", _USER_A)
        assert a_list_after is not None
        assert "앨리스메모" in a_list_after


# =========================================================================
# Project list isolation
# =========================================================================


class TestProjectListIsolation:
    """User B cannot see User A's projects."""

    def test_user_b_project_list_does_not_show_user_a_projects(self) -> None:
        resp = handle_message("/archive project list", _USER_B)
        assert resp is not None
        assert "앨리스프로젝트" not in resp

    def test_user_a_project_list_does_not_show_user_b_projects(self) -> None:
        resp = handle_message("/archive project list", _USER_A)
        assert resp is not None
        assert "밥프로젝트" not in resp


# =========================================================================
# Project rename isolation
# =========================================================================


class TestProjectRenameIsolation:
    """User B cannot rename User A's projects."""

    def test_user_b_rename_user_a_project_fails(self) -> None:
        resp = handle_message(
            "/archive project rename 앨리스프로젝트 탈취됨", _USER_B
        )
        assert resp is not None
        assert "찾을 수 없습니다" in resp

    def test_user_a_project_unchanged_after_user_b_rename_attempt(self) -> None:
        handle_message("/archive project rename 앨리스프로젝트 탈취됨", _USER_B)

        resp = handle_message("/archive project list", _USER_A)
        assert resp is not None
        assert "앨리스프로젝트" in resp
        assert "탈취됨" not in resp


# =========================================================================
# Project delete isolation
# =========================================================================


class TestProjectDeleteIsolation:
    """User B cannot delete User A's projects."""

    def test_user_b_delete_user_a_project_fails(self) -> None:
        resp = handle_message("/archive project delete 앨리스프로젝트", _USER_B)
        assert resp is not None
        assert "찾을 수 없습니다" in resp

    def test_user_a_project_still_exists_after_user_b_delete_attempt(self) -> None:
        handle_message("/archive project delete 앨리스프로젝트", _USER_B)

        resp = handle_message("/archive project list", _USER_A)
        assert resp is not None
        assert "앨리스프로젝트" in resp
