"""Handler for /archive project list command."""

from __future__ import annotations

from openclaw_archiver.db import get_connection, list_projects
from openclaw_archiver.formatters import SEPARATOR

_EMPTY = (
    "프로젝트가 없습니다. "
    "/archive save <제목> <링크> /p <프로젝트> 로 메세지를 저장하면 "
    "프로젝트가 자동으로 생성됩니다."
)


def handle(args: str, user_id: str) -> str:
    """List all projects with archive counts."""
    conn = get_connection()
    try:
        projects = list_projects(conn, user_id)

        if not projects:
            return _EMPTY

        lines = [f"프로젝트 ({len(projects)}개)", f"        {SEPARATOR}"]
        for name, count in projects:
            lines.append(f"        {name}     {count}건")

        return "\n".join(lines)
    finally:
        conn.close()
