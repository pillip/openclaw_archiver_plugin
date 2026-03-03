"""UX message template conformance tests.

Validates that all command responses match the templates defined in
docs/ux_spec.md (Sections 3.1–3.10, 4.1–4.3).
"""

from __future__ import annotations

import os
import re

import pytest

from openclaw_archiver.plugin import handle_message

_USER = "U_UX_TEST"

_DATE_RE = r"\d{4}-\d{2}-\d{2}"
_SEPARATOR = "─────────────────────────────"


@pytest.fixture(autouse=True)
def _ux_db(tmp_path, monkeypatch):
    """Set up a temporary DB for UX tests."""
    from openclaw_archiver.db import get_connection

    db_path = os.path.join(str(tmp_path), "ux.sqlite3")
    conn = get_connection(db_path)
    conn.close()
    monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)


# =========================================================================
# 4.1 Success Messages
# =========================================================================


class TestSaveSuccess:
    """Section 3.1 / 4.1: save success templates."""

    def test_save_without_project(self) -> None:
        resp = handle_message(
            "/archive save 스프린트 회의록 https://slack.com/archives/C01/p123",
            _USER,
        )
        assert resp is not None
        # Pattern: 저장했습니다. (ID: {id})\n        제목: {title}
        assert "저장했습니다. (ID:" in resp
        assert "제목: 스프린트 회의록" in resp
        assert "프로젝트:" not in resp

    def test_save_with_project(self) -> None:
        resp = handle_message(
            "/archive save 스프린트 회의록 https://slack.com/archives/C01/p456 /p Backend",
            _USER,
        )
        assert resp is not None
        assert "저장했습니다. (ID:" in resp
        assert "제목: 스프린트 회의록" in resp
        assert "프로젝트: Backend" in resp


class TestEditSuccess:
    """Section 3.4 / 4.1: edit success template."""

    def test_edit_success_message(self) -> None:
        handle_message(
            "/archive save 원래제목 https://slack.com/archives/C01/p1", _USER
        )
        resp = handle_message("/archive edit 1 수정된제목", _USER)
        assert resp is not None
        # Pattern: 제목을 수정했습니다. (ID: {id})\n        {old} → {new}
        assert "제목을 수정했습니다. (ID: 1)" in resp
        assert "원래제목 → 수정된제목" in resp


class TestRemoveSuccess:
    """Section 3.5 / 4.1: remove success template."""

    def test_remove_success_message(self) -> None:
        handle_message(
            "/archive save 삭제대상 https://slack.com/archives/C01/p1", _USER
        )
        resp = handle_message("/archive remove 1", _USER)
        assert resp is not None
        # Pattern: 삭제했습니다. (ID: {id})\n        {title}
        assert "삭제했습니다. (ID: 1)" in resp
        assert "삭제대상" in resp


class TestProjectRenameSuccess:
    """Section 3.7 / 4.1: project rename success template."""

    def test_rename_success_message(self) -> None:
        handle_message(
            "/archive save 메모 https://slack.com/archives/C01/p1 /p BE", _USER
        )
        resp = handle_message("/archive project rename BE Backend", _USER)
        assert resp is not None
        # Pattern: 프로젝트 이름을 변경했습니다.\n        {old} → {new}
        assert "프로젝트 이름을 변경했습니다." in resp
        assert "BE → Backend" in resp


class TestProjectDeleteSuccess:
    """Section 3.8 / 4.1: project delete success template."""

    def test_delete_with_messages(self) -> None:
        handle_message(
            "/archive save 메모 https://slack.com/archives/C01/p1 /p DelProj",
            _USER,
        )
        resp = handle_message("/archive project delete DelProj", _USER)
        assert resp is not None
        assert '"DelProj" 프로젝트를 삭제했습니다.' in resp
        assert "1건의 메세지가 미분류로 변경되었습니다." in resp

    def test_delete_empty_project(self) -> None:
        # Create project via save, then remove the message so project is empty
        handle_message(
            "/archive save 임시 https://slack.com/archives/C01/p1 /p EmptyProj",
            _USER,
        )
        handle_message("/archive remove 1", _USER)
        # Project still exists but has 0 messages — actually project may be gone
        # Let's create another message in a project, then remove message
        handle_message(
            "/archive save 임시2 https://slack.com/archives/C01/p2 /p EmptyProj2",
            _USER,
        )
        # Remove message from project — but project still exists
        handle_message("/archive remove 2", _USER)
        resp = handle_message("/archive project delete EmptyProj2", _USER)
        assert resp is not None
        assert '"EmptyProj2" 프로젝트를 삭제했습니다.' in resp
        # No "미분류" line since 0 messages affected
        assert "미분류" not in resp


# =========================================================================
# 4.2 Error Messages
# =========================================================================


class TestErrorMessages:
    """Section 4.2: error message templates."""

    def test_edit_not_found(self) -> None:
        resp = handle_message("/archive edit 999 새제목", _USER)
        assert resp == "해당 메세지를 찾을 수 없습니다. (ID: 999)"

    def test_remove_not_found(self) -> None:
        resp = handle_message("/archive remove 999", _USER)
        assert resp == "해당 메세지를 찾을 수 없습니다. (ID: 999)"

    def test_project_not_found_rename(self) -> None:
        resp = handle_message("/archive project rename 없는프로젝트 새이름", _USER)
        assert resp == '"없는프로젝트" 프로젝트를 찾을 수 없습니다.'

    def test_project_not_found_delete(self) -> None:
        resp = handle_message("/archive project delete 없는프로젝트", _USER)
        assert resp == '"없는프로젝트" 프로젝트를 찾을 수 없습니다.'

    def test_project_duplicate_rename(self) -> None:
        handle_message(
            "/archive save m1 https://slack.com/a/1 /p ProjA", _USER
        )
        handle_message(
            "/archive save m2 https://slack.com/a/2 /p ProjB", _USER
        )
        resp = handle_message("/archive project rename ProjA ProjB", _USER)
        assert resp == '"ProjB" 프로젝트가 이미 존재합니다. 다른 이름을 입력하세요.'

    def test_edit_non_numeric_id(self) -> None:
        resp = handle_message("/archive edit abc 새제목", _USER)
        assert resp == "ID는 숫자여야 합니다. 사용법: /archive edit <ID> <새 제목>"

    def test_remove_non_numeric_id(self) -> None:
        resp = handle_message("/archive remove abc", _USER)
        assert resp == "ID는 숫자여야 합니다. 사용법: /archive remove <ID>"

    def test_save_usage(self) -> None:
        resp = handle_message("/archive save", _USER)
        assert resp == "사용법: /archive save <제목> <링크> [/p <프로젝트>]"

    def test_edit_usage_no_args(self) -> None:
        resp = handle_message("/archive edit", _USER)
        assert resp == "사용법: /archive edit <ID> <새 제목>"

    def test_edit_usage_id_only(self) -> None:
        resp = handle_message("/archive edit 1", _USER)
        assert resp == "사용법: /archive edit <ID> <새 제목>"

    def test_remove_usage(self) -> None:
        resp = handle_message("/archive remove", _USER)
        assert resp == "사용법: /archive remove <ID>"

    def test_search_usage(self) -> None:
        resp = handle_message("/archive search", _USER)
        assert resp == "사용법: /archive search <키워드> [/p <프로젝트>]"

    def test_project_rename_usage(self) -> None:
        resp = handle_message("/archive project rename", _USER)
        assert resp == "사용법: /archive project rename <기존이름> <새이름>"

    def test_project_delete_usage(self) -> None:
        resp = handle_message("/archive project delete", _USER)
        assert resp == "사용법: /archive project delete <프로젝트이름>"

    def test_unknown_command(self) -> None:
        resp = handle_message("/archive hello", _USER)
        assert resp == "알 수 없는 명령입니다. /archive help 로 사용법을 확인하세요."

    def test_bare_archive(self) -> None:
        resp = handle_message("/archive", _USER)
        assert resp == "알 수 없는 명령입니다. /archive help 로 사용법을 확인하세요."

    def test_list_nonexistent_project(self) -> None:
        resp = handle_message("/archive list /p 없는프로젝트", _USER)
        assert resp == '"없는프로젝트" 프로젝트를 찾을 수 없습니다.'

    def test_search_nonexistent_project(self) -> None:
        resp = handle_message("/archive search 키워드 /p 없는프로젝트", _USER)
        assert resp == '"없는프로젝트" 프로젝트를 찾을 수 없습니다.'


# =========================================================================
# 4.3 Empty State Messages
# =========================================================================


class TestEmptyStates:
    """Section 4.3: empty state message templates."""

    def test_list_empty(self) -> None:
        resp = handle_message("/archive list", _USER)
        assert resp == "저장된 메세지가 없습니다. /archive save 로 메세지를 저장해보세요."

    def test_list_project_empty(self) -> None:
        # Create a project with a message, then remove the message
        handle_message(
            "/archive save 임시 https://slack.com/a/1 /p TestProj", _USER
        )
        handle_message("/archive remove 1", _USER)
        resp = handle_message("/archive list /p TestProj", _USER)
        assert resp == '"TestProj" 프로젝트에 저장된 메세지가 없습니다.'

    def test_search_no_results(self) -> None:
        resp = handle_message("/archive search 존재하지않는키워드", _USER)
        assert resp == '"존재하지않는키워드"에 대한 검색 결과가 없습니다.'

    def test_search_no_results_in_project(self) -> None:
        handle_message(
            "/archive save 메모 https://slack.com/a/1 /p SProj", _USER
        )
        resp = handle_message("/archive search 없는것 /p SProj", _USER)
        assert resp == '"SProj" 프로젝트에서 "없는것"에 대한 검색 결과가 없습니다.'

    def test_project_list_empty(self) -> None:
        resp = handle_message("/archive project list", _USER)
        assert resp == (
            "프로젝트가 없습니다. "
            "/archive save <제목> <링크> /p <프로젝트> 로 메세지를 저장하면 "
            "프로젝트가 자동으로 생성됩니다."
        )


# =========================================================================
# Formatting & Glossary
# =========================================================================


class TestListFormatting:
    """Section 5.2: list output formatting rules."""

    def test_list_header_count_unit(self) -> None:
        """Message count uses 건, not 개."""
        handle_message(
            "/archive save 메모1 https://slack.com/a/1", _USER
        )
        handle_message(
            "/archive save 메모2 https://slack.com/a/2", _USER
        )
        resp = handle_message("/archive list", _USER)
        assert resp is not None
        assert "저장된 메세지 (2건)" in resp
        assert _SEPARATOR in resp

    def test_list_date_format(self) -> None:
        """Dates must be YYYY-MM-DD."""
        handle_message(
            "/archive save 날짜테스트 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive list", _USER)
        assert resp is not None
        assert re.search(_DATE_RE, resp), f"No YYYY-MM-DD date found in: {resp}"

    def test_list_item_format(self) -> None:
        """Each item starts with #{id}, has link and metadata."""
        handle_message(
            "/archive save 아이템 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive list", _USER)
        assert resp is not None
        assert "#1" in resp
        assert "https://slack.com/a/1" in resp
        assert "미분류" in resp

    def test_list_project_filter_omits_project_name(self) -> None:
        """Project-filtered list omits project name per item (Section 3.2)."""
        handle_message(
            "/archive save 항목 https://slack.com/a/1 /p MyProj", _USER
        )
        resp = handle_message("/archive list /p MyProj", _USER)
        assert resp is not None
        # Header should show project name
        assert "MyProj" in resp.splitlines()[0]
        # Individual items should NOT repeat "프로젝트: MyProj"
        lines_after_header = resp.split(_SEPARATOR, 1)[1] if _SEPARATOR in resp else ""
        assert "프로젝트: MyProj" not in lines_after_header

    def test_search_header_format(self) -> None:
        """Search header: 검색 결과: "keyword" (N건)."""
        handle_message(
            "/archive save 검색대상 https://slack.com/a/1", _USER
        )
        resp = handle_message("/archive search 검색", _USER)
        assert resp is not None
        assert '검색 결과: "검색" (1건)' in resp


class TestProjectListFormatting:
    """Section 5.2: project list formatting."""

    def test_project_count_unit(self) -> None:
        """Project count uses 개, message count uses 건."""
        handle_message(
            "/archive save m1 https://slack.com/a/1 /p P1", _USER
        )
        handle_message(
            "/archive save m2 https://slack.com/a/2 /p P2", _USER
        )
        resp = handle_message("/archive project list", _USER)
        assert resp is not None
        assert "프로젝트 (2개)" in resp
        assert "1건" in resp


# =========================================================================
# Help & Unknown Command
# =========================================================================


class TestHelpMessage:
    """Section 3.9: help output."""

    def test_help_contains_all_commands(self) -> None:
        resp = handle_message("/archive help", _USER)
        assert resp is not None
        assert "/archive 사용법" in resp
        assert _SEPARATOR in resp
        assert "/archive save" in resp
        assert "/archive list" in resp
        assert "/archive search" in resp
        assert "/archive edit" in resp
        assert "/archive remove" in resp
        assert "/archive project list" in resp
        assert "/archive project rename" in resp
        assert "/archive project delete" in resp


# =========================================================================
# End-to-End Flow
# =========================================================================


class TestEndToEnd:
    """Full lifecycle: save → list → search → edit → list → remove → list."""

    def test_full_lifecycle(self) -> None:
        # 1. Save
        resp = handle_message(
            "/archive save 라이프사이클 테스트 https://slack.com/archives/C01/p999",
            _USER,
        )
        assert resp is not None
        assert "저장했습니다. (ID:" in resp
        # Extract ID
        match = re.search(r"ID: (\d+)", resp)
        assert match
        aid = match.group(1)

        # 2. List — should contain the message
        resp = handle_message("/archive list", _USER)
        assert resp is not None
        assert "라이프사이클 테스트" in resp
        assert f"#{aid}" in resp
        assert re.search(_DATE_RE, resp)

        # 3. Search — should find it
        resp = handle_message("/archive search 라이프사이클", _USER)
        assert resp is not None
        assert "라이프사이클 테스트" in resp
        assert "1건" in resp

        # 4. Edit
        resp = handle_message(f"/archive edit {aid} 수정된 라이프사이클", _USER)
        assert resp is not None
        assert f"제목을 수정했습니다. (ID: {aid})" in resp
        assert "라이프사이클 테스트 → 수정된 라이프사이클" in resp

        # 5. List — should show updated title
        resp = handle_message("/archive list", _USER)
        assert resp is not None
        assert "수정된 라이프사이클" in resp
        assert "라이프사이클 테스트" not in resp

        # 6. Remove
        resp = handle_message(f"/archive remove {aid}", _USER)
        assert resp is not None
        assert f"삭제했습니다. (ID: {aid})" in resp
        assert "수정된 라이프사이클" in resp

        # 7. List — should be empty
        resp = handle_message("/archive list", _USER)
        assert resp == "저장된 메세지가 없습니다. /archive save 로 메세지를 저장해보세요."

    def test_lifecycle_with_project(self) -> None:
        """Save with project → list in project → delete project."""
        # Save with project
        resp = handle_message(
            "/archive save 프로젝트메모 https://slack.com/a/1 /p LifeProj",
            _USER,
        )
        assert resp is not None
        assert "저장했습니다" in resp
        assert "프로젝트: LifeProj" in resp

        # List in project
        resp = handle_message("/archive list /p LifeProj", _USER)
        assert resp is not None
        assert "프로젝트메모" in resp
        assert "LifeProj" in resp.splitlines()[0]

        # Project list
        resp = handle_message("/archive project list", _USER)
        assert resp is not None
        assert "LifeProj" in resp
        assert "1건" in resp

        # Delete project
        resp = handle_message("/archive project delete LifeProj", _USER)
        assert resp is not None
        assert '"LifeProj" 프로젝트를 삭제했습니다.' in resp
        assert "1건의 메세지가 미분류로 변경되었습니다." in resp

        # Message still exists but now unclassified
        resp = handle_message("/archive list", _USER)
        assert resp is not None
        assert "프로젝트메모" in resp
        assert "미분류" in resp


# =========================================================================
# Non-archive messages
# =========================================================================


class TestNonArchiveMessages:
    """Messages not starting with /archive return None."""

    def test_non_archive_returns_none(self) -> None:
        assert handle_message("hello world", _USER) is None

    def test_partial_prefix_returns_none(self) -> None:
        assert handle_message("/archivesave foo", _USER) is None
