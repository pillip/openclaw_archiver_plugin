"""Command dispatcher — routes /archive subcommands to handlers."""

from __future__ import annotations

from openclaw_archiver import (
    cmd_edit,
    cmd_help,
    cmd_list,
    cmd_project_delete,
    cmd_project_list,
    cmd_project_rename,
    cmd_remove,
    cmd_save,
    cmd_search,
)

_UNKNOWN_CMD = "알 수 없는 명령입니다. /archive help 로 사용법을 확인하세요."

_COMMANDS: dict[str, object] = {
    "save": cmd_save,
    "list": cmd_list,
    "search": cmd_search,
    "edit": cmd_edit,
    "remove": cmd_remove,
    "help": cmd_help,
}

_PROJECT_SUBCOMMANDS: dict[str, object] = {
    "list": cmd_project_list,
    "rename": cmd_project_rename,
    "delete": cmd_project_delete,
}


def dispatch(message: str, user_id: str) -> str:
    """Route a message (with ``/archive`` prefix already confirmed) to a handler.

    Args:
        message: Full message starting with ``/archive``.
        user_id: Slack user ID.

    Returns:
        Response string from the matched handler, or unknown-command message.
    """
    # Strip "/archive" prefix and get remaining text.
    rest = message[len("/archive"):].strip()

    if not rest:
        return _UNKNOWN_CMD

    parts = rest.split(None, 1)
    cmd = parts[0]
    args = parts[1] if len(parts) > 1 else ""

    # Handle "project" subcommand with 2nd-level routing.
    if cmd == "project":
        return _dispatch_project(args, user_id)

    handler = _COMMANDS.get(cmd)
    if handler is None:
        return _UNKNOWN_CMD

    return handler.handle(args, user_id)  # type: ignore[union-attr]


def _dispatch_project(args: str, user_id: str) -> str:
    """Route ``/archive project <subcmd>`` to a project handler."""
    if not args:
        return _UNKNOWN_CMD

    parts = args.split(None, 1)
    subcmd = parts[0]
    sub_args = parts[1] if len(parts) > 1 else ""

    handler = _PROJECT_SUBCOMMANDS.get(subcmd)
    if handler is None:
        return _UNKNOWN_CMD

    return handler.handle(sub_args, user_id)  # type: ignore[union-attr]
