"""Handler for /archive help command."""

from __future__ import annotations

from openclaw_archiver.formatters import SEPARATOR

_HELP_TEXT = (
    "/archive 사용법\n"
    f"        {SEPARATOR}\n"
    "        저장    /archive save <제목> <링크> [/p <프로젝트>]\n"
    "        목록    /archive list [/p <프로젝트>]\n"
    "        검색    /archive search <키워드> [/p <프로젝트>]\n"
    "        수정    /archive edit <ID> <새 제목>\n"
    "        삭제    /archive remove <ID>\n"
    "\n"
    "        프로젝트 관리\n"
    f"        {SEPARATOR}\n"
    "        목록    /archive project list\n"
    "        이름변경 /archive project rename <기존이름> <새이름>\n"
    "        삭제    /archive project delete <프로젝트이름>"
)


def handle(args: str, user_id: str) -> str:
    """Show help message."""
    return _HELP_TEXT
