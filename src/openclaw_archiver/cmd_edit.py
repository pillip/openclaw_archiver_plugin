"""Handler for /archive edit command."""

from __future__ import annotations

from openclaw_archiver.db import get_archive_title, get_connection, update_archive_title

_USAGE = "사용법: /archive edit <ID> <새 제목>"
_NOT_FOUND = "해당 메세지를 찾을 수 없습니다. (ID: {id})"
_BAD_ID = "ID는 숫자여야 합니다. 사용법: /archive edit <ID> <새 제목>"


def handle(args: str, user_id: str) -> str:
    """Edit the title of an archived message."""
    parts = args.strip().split(None, 1)

    if len(parts) < 1 or not parts[0]:
        return _USAGE

    raw_id = parts[0]
    try:
        archive_id = int(raw_id)
    except ValueError:
        return _BAD_ID

    if len(parts) < 2 or not parts[1].strip():
        return _USAGE

    new_title = parts[1].strip()

    conn = get_connection()
    try:
        old_title = get_archive_title(conn, archive_id, user_id)
        if old_title is None:
            return _NOT_FOUND.format(id=archive_id)

        update_archive_title(conn, archive_id, user_id, new_title)

        return (
            f"제목을 수정했습니다. (ID: {archive_id})\n"
            f"        {old_title} → {new_title}"
        )
    finally:
        conn.close()
