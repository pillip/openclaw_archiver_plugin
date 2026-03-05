"""Handler for /archive search command."""

from __future__ import annotations

from openclaw_archiver.db import (
    get_connection,
    search_archives,
    search_archives_by_project,
)
from openclaw_archiver.formatters import (
    SEPARATOR,
    format_archive_rows,
    require_project,
)
from openclaw_archiver.parser import extract_project_option

_USAGE = "사용법: /archive search <키워드> [/p <프로젝트>]"
_NO_RESULT = '"{keyword}"에 대한 검색 결과가 없습니다.'
_NO_RESULT_PROJECT = '"{project}" 프로젝트에서 "{keyword}"에 대한 검색 결과가 없습니다.'


def handle(args: str, user_id: str) -> str:
    """Search archived messages by keyword."""
    # Extract /p option first, then keyword is the remaining text.
    remaining, project_name = extract_project_option(" " + args if args else args)
    keyword = remaining.strip()

    if not keyword:
        return _USAGE

    conn = get_connection()
    try:
        if project_name:
            return _search_by_project(conn, user_id, keyword, project_name)
        return _search_all(conn, user_id, keyword)
    finally:
        conn.close()


def _search_all(conn, user_id: str, keyword: str) -> str:  # type: ignore[no-untyped-def]
    rows = search_archives(conn, user_id, keyword)
    if not rows:
        return _NO_RESULT.format(keyword=keyword)

    count = len(rows)
    header = [f'*검색 결과: "{keyword}"* ({count}건)', SEPARATOR]
    items = format_archive_rows(rows, include_project=True)
    return "\n".join(header + items)


def _search_by_project(
    conn, user_id: str, keyword: str, project_name: str  # type: ignore[no-untyped-def]
) -> str:
    project_id, err = require_project(conn, user_id, project_name)
    if err:
        return err

    rows = search_archives_by_project(conn, user_id, project_id, keyword)
    if not rows:
        return _NO_RESULT_PROJECT.format(project=project_name, keyword=keyword)

    count = len(rows)
    header = [
        f'*검색 결과: "{keyword}" — {project_name}* ({count}건)',
        SEPARATOR,
    ]
    items = format_archive_rows(rows, include_project=False)
    return "\n".join(header + items)
