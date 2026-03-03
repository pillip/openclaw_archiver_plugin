"""Plugin entry point for OpenClaw framework."""

from __future__ import annotations

from openclaw_archiver.dispatcher import dispatch

_PREFIX = "/archive"


def handle_message(message: str, user_id: str) -> str | None:
    """Process an incoming message.

    Args:
        message: Full user input (e.g. "/archive save ...")
        user_id: Slack user ID (e.g. "U01234567")

    Returns:
        Response string if handled, None otherwise.
    """
    if not message.startswith(_PREFIX):
        return None
    return dispatch(message, user_id)
