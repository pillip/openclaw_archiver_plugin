"""Handler for /archive save command."""

from __future__ import annotations

from openclaw_archiver.db import get_connection, get_or_create_project, insert_archive
from openclaw_archiver.parser import parse_save

_USAGE = "사용법: /archive save <제목> <링크> [/p <프로젝트>]"


def handle(args: str, user_id: str) -> str:
    """Save a Slack message link."""
    title, link, project = parse_save(args)

    if not title or not link:
        return _USAGE

    conn = get_connection()
    try:
        project_id: int | None = None
        if project:
            project_id = get_or_create_project(conn, user_id, project)

        archive_id = insert_archive(conn, user_id, project_id, title, link)

        lines = [
            f"저장했습니다. (ID: {archive_id})",
            f"*제목:* {title}",
        ]
        if project:
            lines.append(f"*프로젝트:* {project}")

        return "\n".join(lines)
    finally:
        conn.close()
