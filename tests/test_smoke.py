"""Smoke tests — verify scaffolding is importable and entry points are wired."""

from openclaw_archiver import __version__
from openclaw_archiver.plugin import handle_message
from openclaw_archiver.server import run


class TestScaffolding:
    """Basic import and signature checks for the initial scaffolding."""

    def test_version_is_string(self) -> None:
        assert isinstance(__version__, str)

    def test_handle_message_returns_none_for_empty_input(self) -> None:
        result = handle_message(message="", user_id="U00000000")
        assert result is None

    def test_handle_message_returns_none_for_arbitrary_input(self) -> None:
        result = handle_message(message="/archive save test link", user_id="U12345678")
        assert result is None

    def test_run_is_callable(self) -> None:
        assert callable(run)
