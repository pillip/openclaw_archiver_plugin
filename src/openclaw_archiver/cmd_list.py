"""Handler for /archive list command."""

from __future__ import annotations

from openclaw_archiver.db import (
    get_connection,
    list_archives,
    list_archives_by_project,
)
from openclaw_archiver.formatters import (
    SEPARATOR,
    format_archive_rows,
    require_project,
)
from openclaw_archiver.parser import extract_project_option

_EMPTY_ALL = "저장된 메세지가 없습니다. /archive save 로 메세지를 저장해보세요."
_EMPTY_PROJECT = '"{name}" 프로젝트에 저장된 메세지가 없습니다.'


def handle(args: str, user_id: str) -> str:
    """List archived messages, optionally filtered by project."""
    # Prepend space so regex `\s+/p\s+` can match at start of args.
    _, project_name = extract_project_option(" " + args if args else args)

    conn = get_connection()
    try:
        if project_name:
            return _list_by_project(conn, user_id, project_name)
        return _list_all(conn, user_id)
    finally:
        conn.close()


def _list_all(conn, user_id: str) -> str:  # type: ignore[no-untyped-def]
    rows = list_archives(conn, user_id)
    if not rows:
        return _EMPTY_ALL

    count = len(rows)
    header = [f"*저장된 메세지* ({count}건)", SEPARATOR]
    items = format_archive_rows(rows, include_project=True)
    return "\n".join(header + items)


def _list_by_project(conn, user_id: str, project_name: str) -> str:  # type: ignore[no-untyped-def]
    project_id, err = require_project(conn, user_id, project_name)
    if err:
        return err

    rows = list_archives_by_project(conn, user_id, project_id)
    if not rows:
        return _EMPTY_PROJECT.format(name=project_name)

    count = len(rows)
    header = [
        f"*저장된 메세지 — {project_name}* ({count}건)",
        SEPARATOR,
    ]
    items = format_archive_rows(rows, include_project=False)
    return "\n".join(header + items)
