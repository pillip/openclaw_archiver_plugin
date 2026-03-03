"""Tests for dispatcher and plugin entry point — command routing."""

from unittest.mock import patch

from openclaw_archiver.plugin import handle_message


_UNKNOWN_MSG = "알 수 없는 명령입니다. /archive help 로 사용법을 확인하세요."


class TestPluginHandleMessage:
    """Verify plugin.handle_message routes correctly."""

    def test_non_archive_message_returns_none(self) -> None:
        assert handle_message("안녕하세요", "U01") is None

    def test_random_message_returns_none(self) -> None:
        assert handle_message("just some text", "U01") is None

    def test_empty_message_returns_none(self) -> None:
        assert handle_message("", "U01") is None

    def test_archive_prefix_without_space_returns_none(self) -> None:
        """'/archivesave' should NOT be treated as '/archive save'."""
        assert handle_message("/archivesave", "U01") is None
        assert handle_message("/archiver", "U01") is None
        assert handle_message("/archives", "U01") is None

    def test_archive_no_subcommand_returns_unknown(self) -> None:
        assert handle_message("/archive", "U01") == _UNKNOWN_MSG

    def test_archive_with_trailing_space_returns_unknown(self) -> None:
        assert handle_message("/archive   ", "U01") == _UNKNOWN_MSG

    def test_unknown_subcommand_returns_unknown(self) -> None:
        assert handle_message("/archive xyz", "U01") == _UNKNOWN_MSG

    def test_unknown_subcommand_foobar(self) -> None:
        assert handle_message("/archive foobar", "U01") == _UNKNOWN_MSG


class TestCommandRouting:
    """Verify /archive <cmd> routes to correct handler."""

    @patch("openclaw_archiver.dispatcher.cmd_save.handle", return_value="saved")
    def test_save_routing(self, mock_handle) -> None:  # type: ignore[no-untyped-def]
        result = handle_message("/archive save 제목 https://example.com", "U01")
        assert result == "saved"
        mock_handle.assert_called_once_with("제목 https://example.com", "U01")

    @patch("openclaw_archiver.dispatcher.cmd_list.handle", return_value="listed")
    def test_list_routing(self, mock_handle) -> None:  # type: ignore[no-untyped-def]
        result = handle_message("/archive list", "U01")
        assert result == "listed"
        mock_handle.assert_called_once_with("", "U01")

    @patch("openclaw_archiver.dispatcher.cmd_search.handle", return_value="found")
    def test_search_routing(self, mock_handle) -> None:  # type: ignore[no-untyped-def]
        result = handle_message("/archive search 키워드", "U01")
        assert result == "found"
        mock_handle.assert_called_once_with("키워드", "U01")

    @patch("openclaw_archiver.dispatcher.cmd_edit.handle", return_value="edited")
    def test_edit_routing(self, mock_handle) -> None:  # type: ignore[no-untyped-def]
        result = handle_message("/archive edit 1 새제목", "U01")
        assert result == "edited"
        mock_handle.assert_called_once_with("1 새제목", "U01")

    @patch("openclaw_archiver.dispatcher.cmd_remove.handle", return_value="removed")
    def test_remove_routing(self, mock_handle) -> None:  # type: ignore[no-untyped-def]
        result = handle_message("/archive remove 1", "U01")
        assert result == "removed"
        mock_handle.assert_called_once_with("1", "U01")

    @patch("openclaw_archiver.dispatcher.cmd_help.handle", return_value="help text")
    def test_help_routing(self, mock_handle) -> None:  # type: ignore[no-untyped-def]
        result = handle_message("/archive help", "U01")
        assert result == "help text"
        mock_handle.assert_called_once_with("", "U01")


class TestProjectSubcommandRouting:
    """Verify /archive project <subcmd> routes correctly."""

    @patch("openclaw_archiver.dispatcher.cmd_project_list.handle", return_value="projects")
    def test_project_list_routing(self, mock_handle) -> None:  # type: ignore[no-untyped-def]
        result = handle_message("/archive project list", "U01")
        assert result == "projects"
        mock_handle.assert_called_once_with("", "U01")

    @patch("openclaw_archiver.dispatcher.cmd_project_rename.handle", return_value="renamed")
    def test_project_rename_routing(self, mock_handle) -> None:  # type: ignore[no-untyped-def]
        result = handle_message("/archive project rename old new", "U01")
        assert result == "renamed"
        mock_handle.assert_called_once_with("old new", "U01")

    @patch("openclaw_archiver.dispatcher.cmd_project_delete.handle", return_value="deleted")
    def test_project_delete_routing(self, mock_handle) -> None:  # type: ignore[no-untyped-def]
        result = handle_message("/archive project delete Backend", "U01")
        assert result == "deleted"
        mock_handle.assert_called_once_with("Backend", "U01")

    def test_project_no_subcommand_returns_unknown(self) -> None:
        assert handle_message("/archive project", "U01") == _UNKNOWN_MSG

    def test_project_unknown_subcommand_returns_unknown(self) -> None:
        assert handle_message("/archive project xyz", "U01") == _UNKNOWN_MSG


class TestCmdStubs:
    """Verify all cmd_* modules have handle(args, user_id) -> str."""

    def test_cmd_save_handle_exists(self) -> None:
        from openclaw_archiver.cmd_save import handle
        assert callable(handle)
        assert isinstance(handle("", "U01"), str)

    def test_cmd_list_handle_exists(self) -> None:
        from openclaw_archiver.cmd_list import handle
        assert callable(handle)
        assert isinstance(handle("", "U01"), str)

    def test_cmd_search_handle_exists(self) -> None:
        from openclaw_archiver.cmd_search import handle
        assert callable(handle)
        assert isinstance(handle("", "U01"), str)

    def test_cmd_edit_handle_exists(self) -> None:
        from openclaw_archiver.cmd_edit import handle
        assert callable(handle)
        assert isinstance(handle("", "U01"), str)

    def test_cmd_remove_handle_exists(self) -> None:
        from openclaw_archiver.cmd_remove import handle
        assert callable(handle)
        assert isinstance(handle("", "U01"), str)

    def test_cmd_project_list_handle_exists(self) -> None:
        from openclaw_archiver.cmd_project_list import handle
        assert callable(handle)
        assert isinstance(handle("", "U01"), str)

    def test_cmd_project_rename_handle_exists(self) -> None:
        from openclaw_archiver.cmd_project_rename import handle
        assert callable(handle)
        assert isinstance(handle("", "U01"), str)

    def test_cmd_project_delete_handle_exists(self) -> None:
        from openclaw_archiver.cmd_project_delete import handle
        assert callable(handle)
        assert isinstance(handle("", "U01"), str)

    def test_cmd_help_handle_exists(self) -> None:
        from openclaw_archiver.cmd_help import handle
        assert callable(handle)
        assert isinstance(handle("", "U01"), str)
