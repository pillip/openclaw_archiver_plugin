"""Handler for /archive project rename command."""

from __future__ import annotations

from openclaw_archiver.db import find_project, get_connection, rename_project

_USAGE = "사용법: /archive project rename <기존이름> <새이름>"
_NOT_FOUND = '"{name}" 프로젝트를 찾을 수 없습니다.'
_DUPLICATE = '"{name}" 프로젝트가 이미 존재합니다. 다른 이름을 입력하세요.'


def handle(args: str, user_id: str) -> str:
    """Rename a project."""
    parts = args.strip().split()

    if len(parts) < 2:
        return _USAGE

    old_name = parts[0]
    new_name = parts[1]

    conn = get_connection()
    try:
        # Check old project exists (owned by user)
        if find_project(conn, user_id, old_name) is None:
            return _NOT_FOUND.format(name=old_name)

        # Check new name not already taken
        if find_project(conn, user_id, new_name) is not None:
            return _DUPLICATE.format(name=new_name)

        renamed = rename_project(conn, user_id, old_name, new_name)
        if not renamed:
            return _NOT_FOUND.format(name=old_name)

        return f"프로젝트 이름을 변경했습니다.\n        {old_name} → {new_name}"
    finally:
        conn.close()
