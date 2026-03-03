"""Handler for /archive search command."""

from __future__ import annotations

from openclaw_archiver.db import (
    find_project,
    get_connection,
    search_archives,
    search_archives_by_project,
)
from openclaw_archiver.parser import extract_project_option

_USAGE = "사용법: /archive search <키워드> [/p <프로젝트>]"
_SEPARATOR = "─────────────────────────────"
_NO_RESULT = '"{keyword}"에 대한 검색 결과가 없습니다.'
_NO_RESULT_PROJECT = '"{project}" 프로젝트에서 "{keyword}"에 대한 검색 결과가 없습니다.'
_NOT_FOUND = '"{name}" 프로젝트를 찾을 수 없습니다.'


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
    lines = [f'검색 결과: "{keyword}" ({count}건)', f"        {_SEPARATOR}"]

    for aid, title, link, project_name, created_at in rows:
        date = created_at[:10] if created_at else ""
        proj_label = f"프로젝트: {project_name}" if project_name else "미분류"
        lines.append(f"        #{aid}  {title}")
        lines.append(f"            {link}")
        lines.append(f"            {proj_label} | {date}")
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


def _search_by_project(
    conn, user_id: str, keyword: str, project_name: str  # type: ignore[no-untyped-def]
) -> str:
    project = find_project(conn, user_id, project_name)
    if project is None:
        return _NOT_FOUND.format(name=project_name)

    project_id = project[0]
    rows = search_archives_by_project(conn, user_id, project_id, keyword)
    if not rows:
        return _NO_RESULT_PROJECT.format(project=project_name, keyword=keyword)

    count = len(rows)
    lines = [
        f'검색 결과: "{keyword}" — {project_name} ({count}건)',
        f"        {_SEPARATOR}",
    ]

    for aid, title, link, created_at in rows:
        date = created_at[:10] if created_at else ""
        lines.append(f"        #{aid}  {title}")
        lines.append(f"            {link}")
        lines.append(f"            {date}")
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)
