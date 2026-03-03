"""Handler for /archive remove command."""

from __future__ import annotations

from openclaw_archiver.db import delete_archive, get_archive_title, get_connection
from openclaw_archiver.formatters import parse_archive_id

_USAGE = "사용법: /archive remove <ID>"
_NOT_FOUND = "해당 메세지를 찾을 수 없습니다. (ID: {id})"


def handle(args: str, user_id: str) -> str:
    """Remove an archived message."""
    stripped = args.strip()

    if not stripped:
        return _USAGE

    archive_id, err = parse_archive_id(stripped, "remove <ID>")
    if err:
        return err

    conn = get_connection()
    try:
        title = get_archive_title(conn, archive_id, user_id)
        if title is None:
            return _NOT_FOUND.format(id=archive_id)

        deleted = delete_archive(conn, archive_id, user_id)
        if not deleted:
            return _NOT_FOUND.format(id=archive_id)

        return f"삭제했습니다. (ID: {archive_id})\n        {title}"
    finally:
        conn.close()
