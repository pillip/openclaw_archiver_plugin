"""Handler for /archive project delete command."""

from __future__ import annotations

from openclaw_archiver.db import delete_project, get_connection

_USAGE = "사용법: /archive project delete <프로젝트이름>"
_NOT_FOUND = '"{name}" 프로젝트를 찾을 수 없습니다.'


def handle(args: str, user_id: str) -> str:
    """Delete a project and move its archives to unclassified."""
    name = args.strip()

    if not name:
        return _USAGE

    conn = get_connection()
    try:
        unlinked = delete_project(conn, user_id, name)

        if unlinked < 0:
            return _NOT_FOUND.format(name=name)

        result = f'"{name}" 프로젝트를 삭제했습니다.'
        if unlinked > 0:
            result += f"\n{unlinked}건의 메세지가 미분류로 변경되었습니다."

        return result
    finally:
        conn.close()
