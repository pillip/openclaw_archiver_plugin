# PRD: OpenClaw Archiver Plugin

## Background

팀에서 Slack을 사용하다 보면 중요한 메세지 링크를 나중에 다시 찾아야 할 때가 많다. Slack의 "저장된 항목" 기능은 프로젝트별 분류가 불가능하고, 팀 단위로 공유되는 OpenClaw 환경에서 개인 아카이브를 관리할 방법이 없다.

OpenClaw Archiver Plugin은 Slack DM을 통해 메세지 링크를 **개인별로 격리**하여 저장·관리하는 플러그인이다. 기존 [openclaw_todo_plugin](https://github.com/pillip/openclaw_todo_plugin)과 동일한 아키텍처(LLM bypass, SQLite, 명령 파싱 기반)를 따른다.

## Goals

1. 사용자가 Slack 메세지 링크를 title + link 쌍으로 저장하고, 프로젝트별로 분류·관리할 수 있다.
2. 각 사용자의 아카이브는 완전히 격리되어 다른 사용자가 열람할 수 없다.
3. LLM을 bypass하여 명령 파싱 기반으로 결정론적으로 동작한다.
4. 저장된 메세지가 많아져도 검색을 통해 빠르게 찾을 수 있다.

## Target User

- OpenClaw가 설치된 Slack 워크스페이스의 팀원
- Slack 메세지 링크를 체계적으로 아카이빙하고 싶은 개인 사용자

## User Stories

1. **메세지 저장**: 사용자로서, Slack 메세지 링크를 title과 함께 저장하고 싶다. 나중에 빠르게 다시 찾을 수 있도록.
2. **프로젝트 분류**: 사용자로서, 저장한 메세지를 프로젝트별로 분류하고 싶다. 주제별로 정리하여 관리 효율을 높이기 위해.
3. **메세지 조회**: 사용자로서, 전체 또는 특정 프로젝트의 저장된 메세지 목록을 확인하고 싶다. 필요한 메세지를 찾기 위해.
4. **메세지 검색**: 사용자로서, 저장된 메세지를 title 키워드로 검색하고 싶다. 많은 메세지 중에서 빠르게 원하는 것을 찾기 위해.
5. **타이틀 수정**: 사용자로서, 저장된 메세지의 title을 수정하고 싶다. 더 나은 설명으로 업데이트하기 위해.
6. **메세지 삭제**: 사용자로서, 저장된 메세지를 삭제(해제)하고 싶다. 더 이상 필요 없는 아카이브를 정리하기 위해.
7. **프로젝트 관리**: 사용자로서, 프로젝트 이름을 변경하거나 삭제하고 싶다. 프로젝트 구조를 정리하기 위해.
8. **개인 격리**: 사용자로서, 내가 저장한 메세지를 다른 팀원이 볼 수 없도록 하고 싶다. 개인 아카이브의 프라이버시를 보장하기 위해.

## Functional Requirements

### 1. 메세지 저장 (`/archive save`)

- Slack 메세지 링크(URL)와 title을 함께 저장한다.
- 선택적으로 프로젝트를 지정할 수 있다 (`/p <project_name>`).
- 프로젝트를 지정하면 해당 프로젝트가 없을 경우 자동 생성된다.
- 프로젝트를 지정하지 않으면 **프로젝트 미분류** 상태로 저장된다 (디폴트 프로젝트 없음).
- 저장 시 Slack user ID를 owner로 기록한다.

### 2. 메세지 목록 조회 (`/archive list`)

- 전체 저장된 메세지를 조회한다.
- `/p <project_name>` 옵션으로 특정 프로젝트의 메세지만 필터링한다.
- 본인의 메세지만 조회 가능하다.

### 3. 메세지 검색 (`/archive search <keyword>`)

- title에서 키워드를 검색한다.
- 선택적으로 프로젝트 범위를 지정할 수 있다.
- 본인의 메세지만 검색 가능하다.

### 4. 타이틀 수정 (`/archive edit <id> <new_title>`)

- 저장된 메세지의 title을 수정한다.
- 본인의 메세지만 수정 가능하다.

### 5. 메세지 삭제 (`/archive remove <id>`)

- 저장된 메세지를 삭제한다.
- 본인의 메세지만 삭제 가능하다.

### 6. 프로젝트 관리

- **목록 조회** (`/archive project list`): 본인의 프로젝트 목록을 조회한다.
- **이름 변경** (`/archive project rename <old> <new>`): 프로젝트 이름을 변경한다. (유저, 프로젝트명) pair가 유니크하면 된다.
- **삭제** (`/archive project delete <name>`): 프로젝트를 삭제한다. 해당 프로젝트에 속한 메세지는 미분류 상태로 변경된다.

### 7. 데이터 격리

- 모든 조회/수정/삭제 쿼리에 Slack user ID 조건을 포함한다.
- 다른 사용자의 데이터에 접근할 수 있는 경로가 없어야 한다.

## Non-functional Requirements

1. **외부 의존성 0개**: Python 표준 라이브러리만 사용한다 (openclaw_todo_plugin과 동일).
2. **SQLite (WAL 모드)**: 데이터 저장소로 SQLite를 사용하고, 동시성을 위해 WAL 모드를 적용한다.
3. **LLM Bypass**: 명령 파싱 기반으로 동작하며, LLM을 거치지 않는다.
4. **이중 실행 모드**: 직접 통합 모드 (Python OpenClaw)와 HTTP 브릿지 모드 (JS/TS OpenClaw)를 모두 지원한다.
5. **결정론적 응답**: 동일 입력에 대해 항상 동일한 출력을 보장한다.
6. **Slack mrkdwn 기반 출력 포맷팅**: 모든 응답 메세지에서 코드블럭(들여쓰기 기반 preformatted text 포함)을 사용하지 않는다. 대신 Slack 네이티브 mrkdwn 서식을 활용하여 가독성을 확보한다.
   - 볼드(`*text*`)로 제목·레이블 강조
   - Slack 링크 형식(`<url|text>`)으로 클릭 가능한 하이퍼링크 표시
   - 구분선, 줄바꿈 등으로 시각적 구조를 표현하되 코드블럭은 사용 금지
   - 기존 8칸 들여쓰기 기반 포맷팅을 전면 교체

## Out of Scope

- Slack 메세지 내용 크롤링/캐싱 (링크만 저장)
- 메세지 공유 기능 (완전 개인 격리)
- 태그/라벨 시스템
- 알림/리마인더 기능
- Slack 메세지 링크 유효성 검증

## Success Metrics

1. 메세지 저장~조회 응답 시간 200ms 이내
2. 1만 건 이상의 메세지에서 검색 응답 500ms 이내
3. 외부 의존성 0개 유지

## Technical Notes

### 아키텍처

[openclaw_todo_plugin](https://github.com/pillip/openclaw_todo_plugin)과 동일한 패턴을 따른다:

```
src/openclaw_archiver/
├── __init__.py
├── __main__.py          # python -m 실행
├── plugin.py            # handle_message() 진입점
├── server.py            # HTTP 브릿지 서버
├── dispatcher.py        # 명령 분배
├── parser.py            # 입력 파싱
├── db.py                # SQLite 데이터베이스 작업
├── schema_v1.py         # DB 스키마 정의
├── migrations.py        # DB 마이그레이션
├── cmd_save.py          # 메세지 저장
├── cmd_list.py          # 메세지 목록 조회
├── cmd_search.py        # 메세지 검색
├── cmd_edit.py          # 타이틀 수정
├── cmd_remove.py        # 메세지 삭제
├── cmd_project_list.py  # 프로젝트 목록
├── cmd_project_rename.py # 프로젝트 이름 변경
└── cmd_project_delete.py # 프로젝트 삭제
```

### DB 스키마 (초안)

```sql
-- 프로젝트 테이블
CREATE TABLE projects (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL,           -- Slack user ID
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, name)
);

-- 아카이브 메세지 테이블
CREATE TABLE archives (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL,           -- Slack user ID
    project_id INTEGER,                 -- NULL이면 미분류
    title      TEXT NOT NULL,
    link       TEXT NOT NULL,           -- Slack 메세지 URL
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_archives_user ON archives(user_id);
CREATE INDEX idx_archives_user_project ON archives(user_id, project_id);
CREATE INDEX idx_archives_title ON archives(user_id, title);
```

### Entry Point

```toml
[project.entry-points."openclaw.plugins"]
archiver = "openclaw_archiver.plugin:handle_message"

[project.scripts]
openclaw-archiver-server = "openclaw_archiver.server:run"
```

### 명령 체계

| 명령                         | 설명            | 예시                                                    |
| ---------------------------- | --------------- | ------------------------------------------------------- |
| `save <title> <link>`        | 메세지 저장     | `/archive save 회의록 https://slack.com/... /p Backend` |
| `list`                       | 전체 목록       | `/archive list`                                         |
| `list /p <project>`          | 프로젝트별 목록 | `/archive list /p Backend`                              |
| `search <keyword>`           | 검색            | `/archive search 회의록`                                |
| `edit <id> <new_title>`      | 타이틀 수정     | `/archive edit 3 수정된 제목`                           |
| `remove <id>`                | 삭제            | `/archive remove 3`                                     |
| `project list`               | 프로젝트 목록   | `/archive project list`                                 |
| `project rename <old> <new>` | 이름 변경       | `/archive project rename BE Backend`                    |
| `project delete <name>`      | 프로젝트 삭제   | `/archive project delete Backend`                       |

### 환경 변수

| 변수                        | 설명                  | 기본값                                             |
| --------------------------- | --------------------- | -------------------------------------------------- |
| `OPENCLAW_ARCHIVER_PORT`    | HTTP 브릿지 서버 포트 | `8201`                                             |
| `OPENCLAW_ARCHIVER_DB_PATH` | DB 파일 경로          | `~/.openclaw/workspace/.archiver/archiver.sqlite3` |
