# Issues: OpenClaw Archiver Plugin

> 이 문서는 OpenClaw Archiver Plugin 구현을 위한 이슈 목록이다.
> 각 이슈는 0.5d~1.5d 범위로 분할되어 있으며, 의존성 순서대로 정렬되어 있다.

---

## 이슈 요약

| ID | 제목 | 우선순위 | 견적 | 의존성 |
|----|------|----------|------|--------|
| ISSUE-001 | 프로젝트 스캐폴딩 및 개발 환경 설정 | P0 | 0.5d | none |
| ISSUE-002 | DB 스키마 정의 및 마이그레이션 구현 | P0 | 1d | ISSUE-001 |
| ISSUE-003 | DB 연결 관리 모듈 구현 | P0 | 0.5d | ISSUE-002 |
| ISSUE-004 | 입력 파서 모듈 구현 | P0 | 1d | ISSUE-001 |
| ISSUE-005 | 디스패처 및 플러그인 진입점 구현 | P0 | 1d | ISSUE-003, ISSUE-004 |
| ISSUE-006 | save 명령 핸들러 구현 | P0 | 1d | ISSUE-005 |
| ISSUE-007 | list 명령 핸들러 구현 | P0 | 1d | ISSUE-005 |
| ISSUE-008 | search 명령 핸들러 구현 | P1 | 1d | ISSUE-005 |
| ISSUE-009 | edit 명령 핸들러 구현 | P1 | 0.5d | ISSUE-005 |
| ISSUE-010 | remove 명령 핸들러 구현 | P0 | 0.5d | ISSUE-005 |
| ISSUE-011 | project list 명령 핸들러 구현 | P1 | 0.5d | ISSUE-005 |
| ISSUE-012 | project rename 명령 핸들러 구현 | P1 | 0.5d | ISSUE-005 |
| ISSUE-013 | project delete 명령 핸들러 구현 | P1 | 1d | ISSUE-005 |
| ISSUE-014 | help 명령 핸들러 구현 | P1 | 0.5d | ISSUE-005 |
| ISSUE-015 | HTTP 브릿지 서버 구현 | P1 | 1d | ISSUE-005 |
| ISSUE-016 | 데이터 격리 통합 테스트 작성 | P0 | 1d | ISSUE-006, ISSUE-007, ISSUE-009, ISSUE-010 |
| ISSUE-017 | UX 메시지 템플릿 일치 검증 및 최종 통합 테스트 | P1 | 1d | ISSUE-006 ~ ISSUE-014 |
| ISSUE-018 | formatters.py의 format_archive_rows를 Slack mrkdwn 형식으로 교체 | P0 | 1d | none |
| ISSUE-019 | cmd_list 및 cmd_search 헤더를 mrkdwn 볼드+구분선으로 교체 | P0 | 1d | ISSUE-018 |
| ISSUE-020 | cmd_save 응답을 mrkdwn 볼드 레이블로 교체 | P0 | 0.5d | none |
| ISSUE-021 | cmd_edit 및 cmd_remove 응답을 mrkdwn 볼드 레이블로 교체 | P0 | 0.5d | none |
| ISSUE-022 | cmd_project_list, cmd_project_rename, cmd_project_delete 응답을 mrkdwn으로 교체 | P0 | 1d | none |
| ISSUE-023 | cmd_help 도움말 텍스트를 mrkdwn으로 전면 재작성 | P0 | 0.5d | none |
| ISSUE-024 | NFR-008 준수 검증 테스트 작성 및 기존 테스트 수정 | P0 | 1.5d | ISSUE-018 ~ ISSUE-023 |

---

## 이슈 상세

---

### ISSUE-001: 프로젝트 스캐폴딩 및 개발 환경 설정
- Track: platform
- PRD-Ref: NFR-003, NFR-007, FR-022
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-001-scaffolding
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/1
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/2
- Depends-On: none

#### Goal
`uv` 기반 프로젝트 구조가 초기화되고, `pytest`로 빈 테스트를 실행할 수 있는 상태가 된다.

#### Scope (In/Out)
- In:
  - `pyproject.toml` 생성 (name, version, requires-python>=3.11, dependencies=[], entry-points, scripts)
  - `src/openclaw_archiver/__init__.py`, `__main__.py` 생성
  - `tests/` 디렉터리 및 `conftest.py` 생성
  - `uv sync` 로 개발 의존성(pytest, pytest-cov) 설치
  - `.gitignore` 설정
- Out:
  - 실제 비즈니스 로직 구현
  - CI/CD 파이프라인 설정

#### Acceptance Criteria (DoD)
- [ ] `uv sync` 가 에러 없이 완료된다.
- [ ] `uv run pytest -q` 가 0개 테스트, 0개 에러로 완료된다.
- [ ] `pyproject.toml`의 `dependencies` 가 빈 리스트(`[]`)이다.
- [ ] `pyproject.toml`에 `openclaw.plugins` entry-point와 `openclaw-archiver-server` script가 등록되어 있다.
- [ ] `python -m openclaw_archiver` 가 임포트 에러 없이 실행된다 (아직 동작은 안 해도 됨).

#### Implementation Notes
- `pyproject.toml` 구조는 `docs/architecture.md`의 Deployment 섹션 참조.
- `__init__.py` 에 `__version__ = "0.1.0"` 포함.
- `__main__.py` 는 빈 `main()` 함수 정도만 포함.
- dev dependency: `pytest`, `pytest-cov` (uv add --dev)

#### Tests
- [ ] `uv run pytest -q` 가 정상 종료된다 (smoke test).

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-002: DB 스키마 정의 및 마이그레이션 구현
- Track: platform
- PRD-Ref: FR-024, FR-025
- Priority: P0
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-002-schema-migration
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/3
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/4
- Depends-On: ISSUE-001

#### Goal
`schema_v1.py`와 `migrations.py`가 구현되어, `PRAGMA user_version` 기반으로 초기 스키마(projects, archives 테이블 + 인덱스)를 자동 생성할 수 있다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/schema_v1.py` 구현 (DDL 문자열 상수)
  - `src/openclaw_archiver/migrations.py` 구현 (user_version 체크, 순차 마이그레이션, 트랜잭션 보장)
  - MIGRATIONS 딕셔너리에 up/down DDL 정의
- Out:
  - DB 연결 관리 (ISSUE-003에서 처리)
  - WAL 모드 설정 (ISSUE-003에서 처리)

#### Acceptance Criteria (DoD)
- [ ] `schema_v1.py`에 `SCHEMA_SQL` 상수가 정의되어 있고, projects/archives 테이블 DDL과 3개 인덱스 DDL을 포함한다.
- [ ] `migrations.py`의 `run_migrations(conn)` 함수가 `user_version=0`인 DB에 대해 스키마 v1을 적용하고 `user_version=1`로 설정한다.
- [ ] 이미 `user_version=1`인 DB에 대해 `run_migrations`를 재실행해도 에러 없이 스킵된다.
- [ ] 각 마이그레이션은 트랜잭션 내에서 실행된다.
- [ ] `UNIQUE(user_id, name)` 제약이 projects 테이블에 적용되어 있다.

#### Implementation Notes
- `docs/data_model.md`의 DDL을 그대로 사용한다.
- `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS` 사용.
- MIGRATIONS 딕셔너리 패턴은 `docs/data_model.md` 마이그레이션 섹션 참조.

#### Tests
- [ ] 빈 in-memory DB에 `run_migrations`를 실행하면 `user_version=1`이 설정된다.
- [ ] 마이그레이션 후 projects 테이블에 INSERT/SELECT가 정상 동작한다.
- [ ] 마이그레이션 후 archives 테이블에 INSERT/SELECT가 정상 동작한다.
- [ ] `UNIQUE(user_id, name)` 위반 시 IntegrityError가 발생한다.
- [ ] 이미 `user_version=1`인 DB에 `run_migrations` 재실행 시 에러 없음.
- [ ] 마이그레이션 실패 시 트랜잭션이 롤백되는지 확인 (예: 의도적으로 잘못된 SQL 주입).

#### Rollback
해당 커밋을 revert한다. DB 파일 삭제 후 재생성.

---

### ISSUE-003: DB 연결 관리 모듈 구현
- Track: platform
- PRD-Ref: FR-024, FR-025
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-003-db-connection
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/5
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/6
- Depends-On: ISSUE-002

#### Goal
`db.py` 모듈이 구현되어 SQLite 연결 생성, WAL 모드 설정, foreign_keys 활성화, 스키마 자동 초기화가 한 번의 호출로 완료된다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/db.py` 구현
  - `get_connection()` 함수: 환경변수 `OPENCLAW_ARCHIVER_DB_PATH` 에서 경로 읽기, 디렉터리 자동 생성, WAL 모드 설정, foreign_keys ON, `ensure_schema()` 호출
  - DB 경로 기본값: `~/.openclaw/workspace/.archiver/archiver.sqlite3`
- Out:
  - 개별 CRUD 쿼리 함수 (각 cmd_* 이슈에서 구현)

#### Acceptance Criteria (DoD)
- [ ] `get_connection()` 호출 시 WAL 모드가 활성화된 SQLite 연결이 반환된다 (`PRAGMA journal_mode` 조회 결과가 `wal`).
- [ ] `PRAGMA foreign_keys` 조회 결과가 `1`(ON)이다.
- [ ] DB 파일의 상위 디렉터리가 존재하지 않으면 자동으로 생성된다.
- [ ] 환경변수 `OPENCLAW_ARCHIVER_DB_PATH`로 DB 경로를 오버라이드할 수 있다.
- [ ] 연결 반환 시 스키마가 이미 초기화되어 있다 (projects, archives 테이블 존재).

#### Implementation Notes
- `os.makedirs(parent_dir, exist_ok=True)` 로 디렉터리 생성.
- `os.environ.get("OPENCLAW_ARCHIVER_DB_PATH", default_path)` 패턴.
- `pathlib.Path` 보다 `os.path` 사용 권장 (표준 라이브러리 내 호환성).
- 테스트에서는 `:memory:` 또는 `tmp_path`를 사용.

#### Tests
- [ ] in-memory DB로 `get_connection()` 호출 시 WAL 관련 PRAGMA가 설정된다 (in-memory는 WAL 미지원이므로, 파일 기반 tmp_path 테스트 추가).
- [ ] tmp_path에 DB 파일 생성 후 테이블 존재 확인.
- [ ] 환경변수로 경로를 지정하면 해당 위치에 DB가 생성된다.
- [ ] 존재하지 않는 하위 디렉터리 경로 지정 시 자동 생성된다.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-004: 입력 파서 모듈 구현
- Track: product
- PRD-Ref: FR-020, FR-004
- Priority: P0
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-004-parser
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/7
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/8
- Depends-On: ISSUE-001

#### Goal
`parser.py` 모듈이 구현되어 URL 추출, `/p` 옵션 분리, save 명령 인자 파싱이 결정론적으로 동작한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/parser.py` 구현
  - `extract_project_option(text: str) -> tuple[str, str | None]`: 문자열 끝에서 `/p <project>` 추출
  - `extract_url(text: str) -> tuple[str, str | None]`: URL 패턴 추출 (https?://...)
  - `parse_save(args: str) -> tuple[str | None, str | None, str | None]`: (title, link, project) 반환
  - 파싱 순서: (1) `/p` 옵션 분리 (2) URL 추출 (3) 나머지 = title
- Out:
  - 디스패처 로직 (ISSUE-005)
  - 하위 명령 분기 로직

#### Acceptance Criteria (DoD)
- [ ] `extract_project_option("text /p Backend")` 이 `("text", "Backend")`를 반환한다.
- [ ] `extract_project_option("text without project")` 이 `("text without project", None)`을 반환한다.
- [ ] `extract_url("제목 https://slack.com/archives/C01/p123")` 이 `("제목", "https://slack.com/archives/C01/p123")`을 반환한다.
- [ ] `parse_save("스프린트 회의록 https://slack.com/archives/C01/p123 /p Backend")` 이 `("스프린트 회의록", "https://...", "Backend")`을 반환한다.
- [ ] title 중간에 `/p`가 포함된 경우 (`a/p 패턴 분석 https://... /p Backend`) 올바르게 파싱된다.
- [ ] title에 공백이 포함된 경우 (`3월 스프린트 회의록 https://...`) 전체 텍스트가 title로 파싱된다.

#### Implementation Notes
- `docs/architecture.md` Module: parser 섹션과 `docs/ux_spec.md` Edge Case 6.1~6.2 참조.
- `/p` 옵션은 문자열 끝에서만 인식한다 (R-001 대응).
- URL 정규식: `https?://\S+` 정도로 시작. Slack 링크 형태 `https://slack.com/archives/...`에 맞추되, 범용 URL도 허용.
- `re` 모듈만 사용 (표준 라이브러리).

#### Tests
- [ ] `/p Backend` 가 문자열 끝에 있을 때 올바르게 분리된다.
- [ ] `/p` 없으면 project가 None이다.
- [ ] 제목 중간의 `a/p` 는 `/p` 옵션으로 인식되지 않는다.
- [ ] URL이 없으면 link가 None이다.
- [ ] 제목과 URL이 모두 없으면 title, link 모두 None이다.
- [ ] 공백이 포함된 제목이 올바르게 파싱된다.
- [ ] URL 뒤에 `/p` 옵션이 오는 경우 올바르게 파싱된다.
- [ ] URL 앞에 `/p` 옵션이 오는 경우 (비표준이지만) title의 일부로 처리되는지 확인.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-005: 디스패처 및 플러그인 진입점 구현
- Track: platform
- PRD-Ref: FR-020, FR-021, FR-022
- Priority: P0
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-005-dispatcher
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/9
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/10
- Depends-On: ISSUE-003, ISSUE-004

#### Goal
`dispatcher.py`와 `plugin.py`가 구현되어 `/archive <subcommand>` 메시지를 적절한 핸들러로 라우팅하고, 미인식 명령에 대해 안내 메시지를 반환한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/plugin.py`: `handle_message(message, user_id) -> str | None`
  - `src/openclaw_archiver/dispatcher.py`: `dispatch(message, user_id) -> str`
  - `/archive`로 시작하지 않는 메시지 -> `None` 반환 (LLM bypass)
  - 하위 명령 라우팅: save, list, search, edit, remove, project, help
  - `project` 하위 명령 2차 라우팅: list, rename, delete
  - 미인식 명령 -> `알 수 없는 명령입니다. /archive help 로 사용법을 확인하세요.`
  - 각 cmd_* 핸들러는 stub으로 생성 (빈 `handle(args, user_id) -> str` 함수)
- Out:
  - 각 명령의 실제 비즈니스 로직 (ISSUE-006~014)

#### Acceptance Criteria (DoD)
- [ ] `handle_message("/archive save ...", "U01")` 호출 시 `cmd_save.handle`이 호출된다.
- [ ] `handle_message("/archive list", "U01")` 호출 시 `cmd_list.handle`이 호출된다.
- [ ] `handle_message("/archive project list", "U01")` 호출 시 `cmd_project_list.handle`이 호출된다.
- [ ] `handle_message("일반 메시지", "U01")` 호출 시 `None`이 반환된다.
- [ ] `handle_message("/archive", "U01")` 호출 시 알 수 없는 명령 메시지가 반환된다.
- [ ] `handle_message("/archive xyz", "U01")` 호출 시 알 수 없는 명령 메시지가 반환된다.
- [ ] 모든 cmd_* 모듈에 `handle(args: str, user_id: str) -> str` 함수 stub이 존재한다.

#### Implementation Notes
- `plugin.py`는 메시지가 `/archive`로 시작하는지 확인 후 `dispatcher.dispatch()`를 호출.
- `dispatcher.py`는 메시지에서 `/archive ` 접두사를 제거하고 첫 번째 토큰으로 하위 명령을 식별.
- `project` 하위 명령은 두 번째 토큰으로 `list/rename/delete`를 식별.
- 각 cmd_* 모듈 파일을 stub으로 생성: `cmd_save.py`, `cmd_list.py`, `cmd_search.py`, `cmd_edit.py`, `cmd_remove.py`, `cmd_project_list.py`, `cmd_project_rename.py`, `cmd_project_delete.py`, `cmd_help.py`.

#### Tests
- [ ] `/archive save ...` -> cmd_save 라우팅 확인.
- [ ] `/archive list` -> cmd_list 라우팅 확인.
- [ ] `/archive search ...` -> cmd_search 라우팅 확인.
- [ ] `/archive edit ...` -> cmd_edit 라우팅 확인.
- [ ] `/archive remove ...` -> cmd_remove 라우팅 확인.
- [ ] `/archive project list` -> cmd_project_list 라우팅 확인.
- [ ] `/archive project rename ...` -> cmd_project_rename 라우팅 확인.
- [ ] `/archive project delete ...` -> cmd_project_delete 라우팅 확인.
- [ ] `/archive help` -> cmd_help 라우팅 확인.
- [ ] `/archive` (하위 명령 없음) -> 알 수 없는 명령 메시지.
- [ ] `/archive foobar` -> 알 수 없는 명령 메시지.
- [ ] `안녕하세요` (비 /archive 메시지) -> None 반환.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-006: save 명령 핸들러 구현
- Track: product
- PRD-Ref: FR-001, FR-002, FR-003, FR-004, FR-005, US-001
- Priority: P0
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-006-cmd-save
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/11
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/12
- Depends-On: ISSUE-005

#### Goal
`/archive save <제목> <링크> [/p <프로젝트>]` 명령이 정상 동작하여, 메시지를 DB에 저장하고 UX 스펙에 맞는 응답을 반환한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/cmd_save.py` 구현
  - `db.py`에 save 관련 CRUD 함수 추가: `insert_archive()`, `get_or_create_project()`
  - parser를 활용한 title/link/project 파싱
  - 프로젝트 자동 생성 (INSERT OR IGNORE)
  - 프로젝트 미지정 시 project_id=NULL 저장
  - 성공/에러 응답 문자열 생성 (ux_spec.md Section 3.1 참조)
- Out:
  - list, search 등 다른 명령

#### Acceptance Criteria (DoD)
- [ ] `/archive save 스프린트 회의록 https://slack.com/archives/C01/p123` 실행 시 archives 테이블에 레코드가 생성되고, 성공 메시지에 ID와 제목이 포함된다.
- [ ] `/archive save 회의록 https://slack.com/... /p Backend` 실행 시 "Backend" 프로젝트가 없으면 자동 생성되고, 응답에 프로젝트명이 포함된다.
- [ ] 프로젝트 미지정 시 project_id가 NULL로 저장된다.
- [ ] 제목 또는 링크 누락 시 사용법 안내 메시지(`사용법: /archive save <제목> <링크> [/p <프로젝트>]`)가 반환된다.
- [ ] 저장 시 user_id가 archives.user_id에 기록된다.
- [ ] SQL 파라미터 바인딩을 사용한다 (문자열 포매팅 금지).

#### Implementation Notes
- `db.py`에 추가할 함수:
  - `get_or_create_project(conn, user_id, name) -> int`: `INSERT OR IGNORE` + `SELECT id` 패턴.
  - `insert_archive(conn, user_id, project_id, title, link) -> int`: INSERT 후 `lastrowid` 반환.
- 파싱 순서: `parser.parse_save(args)` 호출 -> (title, link, project) 추출.
- 응답 포맷은 `docs/ux_spec.md` Section 3.1 및 4.1 참조.

#### Tests
- [ ] 제목+링크만 제공 시 미분류로 저장 성공.
- [ ] 제목+링크+프로젝트 제공 시 프로젝트 자동 생성 후 저장 성공.
- [ ] 이미 존재하는 프로젝트로 저장 시 기존 프로젝트 사용.
- [ ] 제목 누락 시 사용법 안내 반환.
- [ ] 링크 누락 시 사용법 안내 반환.
- [ ] 공백 포함 제목 (`3월 스프린트 회의록`) 정상 저장.
- [ ] 응답 메시지에 생성된 ID가 포함됨.
- [ ] 프로젝트 지정 시 응답에 프로젝트명 포함됨.

#### Rollback
해당 커밋을 revert한다. 테스트 DB에 삽입된 데이터는 테스트 격리로 자동 정리.

---

### ISSUE-007: list 명령 핸들러 구현
- Track: product
- PRD-Ref: FR-006, FR-007, US-002
- Priority: P0
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-007-cmd-list
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/13
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/14
- Depends-On: ISSUE-005

#### Goal
`/archive list [/p <프로젝트>]` 명령이 동작하여, 전체 또는 프로젝트별 메시지 목록을 UX 스펙에 맞는 형식으로 반환한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/cmd_list.py` 구현
  - `db.py`에 list 관련 쿼리 함수 추가: `list_archives()`, `list_archives_by_project()`, `find_project()`
  - 전체 목록 조회 (LEFT JOIN projects)
  - 프로젝트별 필터링 (프로젝트 존재 확인 포함)
  - 빈 상태/에러 응답 (ux_spec.md Section 3.2)
  - 목록 출력 포맷팅 (id, title, link, project/미분류, date)
- Out:
  - 검색 기능 (ISSUE-008)

#### Acceptance Criteria (DoD)
- [ ] `/archive list` 실행 시 본인의 전체 메시지 목록이 created_at 내림차순으로 반환된다.
- [ ] 목록의 각 항목에 `#{id}`, 제목, 링크, 프로젝트명(또는 `미분류`), 날짜(`YYYY-MM-DD`)가 포함된다.
- [ ] `/archive list /p Backend` 실행 시 "Backend" 프로젝트의 메시지만 반환된다.
- [ ] 프로젝트별 조회 시 헤더에 프로젝트명이 포함되고, 개별 항목에는 프로젝트명이 생략된다.
- [ ] 저장된 메시지가 없으면 `저장된 메세지가 없습니다. /archive save 로 메세지를 저장해보세요.` 가 반환된다.
- [ ] 존재하지 않는 프로젝트 지정 시 `"ProjectName" 프로젝트를 찾을 수 없습니다.` 가 반환된다.
- [ ] 타인의 메시지는 결과에 포함되지 않는다.

#### Implementation Notes
- `db.py`에 추가할 함수:
  - `list_archives(conn, user_id) -> list[Row]`: LEFT JOIN + ORDER BY created_at DESC.
  - `list_archives_by_project(conn, user_id, project_id) -> list[Row]`: WHERE project_id = ?.
  - `find_project(conn, user_id, name) -> Row | None`: 프로젝트 존재 확인.
- 출력 포맷은 `docs/ux_spec.md` Section 3.2 및 5.2 참조.
- 날짜는 `created_at[:10]` 으로 `YYYY-MM-DD` 추출.

#### Tests
- [ ] 시드 데이터로 전체 목록 조회 시 본인 메시지만 반환.
- [ ] 프로젝트별 조회 시 해당 프로젝트 메시지만 반환.
- [ ] 빈 목록 시 빈 상태 메시지 반환.
- [ ] 존재하지 않는 프로젝트 조회 시 에러 메시지 반환.
- [ ] 프로젝트 존재하지만 메시지 0건 시 빈 상태 메시지 반환.
- [ ] 타 사용자 메시지가 결과에 포함되지 않음.
- [ ] 출력 포맷에 `#id`, 제목, 링크, 날짜가 포함됨.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-008: search 명령 핸들러 구현
- Track: product
- PRD-Ref: FR-008, FR-009, US-003
- Priority: P1
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-008-cmd-search
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/15
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/16
- Depends-On: ISSUE-005

#### Goal
`/archive search <키워드> [/p <프로젝트>]` 명령이 동작하여, title LIKE 검색 결과를 UX 스펙에 맞게 반환한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/cmd_search.py` 구현
  - `db.py`에 search 관련 쿼리 함수 추가: `search_archives()`, `search_archives_by_project()`
  - LIKE '%keyword%' COLLATE NOCASE 검색
  - 프로젝트 범위 검색
  - 키워드 누락 시 사용법 안내
  - 빈 결과/에러 응답 (ux_spec.md Section 3.3)
- Out:
  - FTS5 기반 검색 (향후 확장)

#### Acceptance Criteria (DoD)
- [ ] `/archive search 회의록` 실행 시 title에 "회의록"이 포함된 본인의 메시지가 반환된다.
- [ ] `/archive search 회의록 /p Backend` 실행 시 "Backend" 프로젝트 범위 내에서만 검색된다.
- [ ] 검색은 대소문자를 구분하지 않는다 (COLLATE NOCASE).
- [ ] 검색 결과 헤더에 키워드와 건수가 포함된다 (`검색 결과: "회의록" (N건)`).
- [ ] 키워드 누락 시 `사용법: /archive search <키워드> [/p <프로젝트>]` 가 반환된다.
- [ ] 검색 결과 없을 시 `"회의록"에 대한 검색 결과가 없습니다.` 가 반환된다.
- [ ] 존재하지 않는 프로젝트 지정 시 `"ProjectName" 프로젝트를 찾을 수 없습니다.` 가 반환된다.

#### Implementation Notes
- `db.py` 쿼리는 `docs/data_model.md` 쿼리 패턴 4, 5 참조.
- LIKE 파라미터: `'%' + keyword + '%'`. SQL Injection 방지를 위해 반드시 파라미터 바인딩.
- 출력 포맷은 list와 동일한 목록 형식. `docs/ux_spec.md` Section 3.3 참조.

#### Tests
- [ ] 시드 데이터에서 "회의록" 검색 시 관련 메시지 반환.
- [ ] 대소문자 무시 검색 확인.
- [ ] 프로젝트 범위 검색 시 해당 프로젝트 내 결과만 반환.
- [ ] 매칭 결과 없을 시 빈 상태 메시지.
- [ ] 존재하지 않는 프로젝트 지정 시 에러 메시지.
- [ ] 키워드 누락 시 사용법 안내.
- [ ] 타 사용자 메시지가 검색 결과에 포함되지 않음.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-009: edit 명령 핸들러 구현
- Track: product
- PRD-Ref: FR-010, FR-011, US-006
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-009-cmd-edit
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/17
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/18
- Depends-On: ISSUE-005

#### Goal
`/archive edit <ID> <새 제목>` 명령이 동작하여, 본인 소유 메시지의 제목을 수정하고 UX 스펙에 맞는 응답을 반환한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/cmd_edit.py` 구현
  - `db.py`에 edit 관련 함수 추가: `get_archive_title()`, `update_archive_title()`
  - ID 정수 검증
  - 권한 검증 (user_id 필터, 존재 여부 비노출)
  - 성공/에러 응답 (ux_spec.md Section 3.4)
- Out:
  - 링크 수정, 프로젝트 변경

#### Acceptance Criteria (DoD)
- [ ] `/archive edit 5 새로운 제목` 실행 시 본인 소유 메시지의 title이 변경되고 `제목을 수정했습니다. (ID: 5)\n이전 제목 → 새로운 제목` 형태로 응답된다.
- [ ] 존재하지 않는 ID 또는 타인 소유 메시지 수정 시도 시 `해당 메세지를 찾을 수 없습니다. (ID: N)` 가 반환된다.
- [ ] ID가 숫자가 아닌 경우 `ID는 숫자여야 합니다. 사용법: /archive edit <ID> <새 제목>` 이 반환된다.
- [ ] 새 제목 누락 시 `사용법: /archive edit <ID> <새 제목>` 이 반환된다.

#### Implementation Notes
- `db.py` 쿼리는 `docs/data_model.md` 쿼리 패턴 6 참조.
- args에서 첫 번째 토큰 = ID, 나머지 전체 = new_title.
- 존재하지 않는 ID와 타인 소유를 동일한 에러로 처리 (FR-019).

#### Tests
- [ ] 본인 메시지 제목 수정 성공.
- [ ] 수정 후 DB에 새 제목이 반영됨.
- [ ] 타인 메시지 수정 시 에러 (존재 여부 비노출).
- [ ] 존재하지 않는 ID 수정 시 동일 에러.
- [ ] ID가 문자열일 때 적절한 에러 반환.
- [ ] 새 제목 누락 시 사용법 안내.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-010: remove 명령 핸들러 구현
- Track: product
- PRD-Ref: FR-012, FR-013, US-004
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-010-cmd-remove
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/19

- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/20
- Depends-On: ISSUE-005

#### Goal
`/archive remove <ID>` 명령이 동작하여, 본인 소유 메시지를 삭제하고 UX 스펙에 맞는 응답을 반환한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/cmd_remove.py` 구현
  - `db.py`에 remove 관련 함수 추가: `delete_archive()`
  - ID 정수 검증
  - 권한 검증 (user_id 필터, 존재 여부 비노출)
  - 삭제 전 title 조회 (응답에 포함)
  - 성공/에러 응답 (ux_spec.md Section 3.5)
- Out:
  - 벌크 삭제

#### Acceptance Criteria (DoD)
- [ ] `/archive remove 5` 실행 시 본인 소유 메시지가 삭제되고 `삭제했습니다. (ID: 5)\n스프린트 회의록` 형태로 응답된다.
- [ ] 존재하지 않는 ID 또는 타인 소유 메시지 삭제 시도 시 `해당 메세지를 찾을 수 없습니다. (ID: N)` 가 반환된다.
- [ ] ID가 숫자가 아닌 경우 `ID는 숫자여야 합니다. 사용법: /archive remove <ID>` 가 반환된다.
- [ ] ID 누락 시 `사용법: /archive remove <ID>` 가 반환된다.

#### Implementation Notes
- `db.py` 쿼리는 `docs/data_model.md` 쿼리 패턴 7 참조.
- 삭제 전 SELECT로 title 조회 -> DELETE 실행 -> 응답에 title 포함.

#### Tests
- [ ] 본인 메시지 삭제 성공.
- [ ] 삭제 후 DB에서 해당 레코드 미존재 확인.
- [ ] 타인 메시지 삭제 시 에러 (존재 여부 비노출).
- [ ] 존재하지 않는 ID 삭제 시 동일 에러.
- [ ] ID가 문자열일 때 적절한 에러 반환.
- [ ] ID 누락 시 사용법 안내.
- [ ] 응답에 삭제된 메시지의 제목이 포함됨.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-011: project list 명령 핸들러 구현
- Track: product
- PRD-Ref: FR-014, US-007
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-011-cmd-project-list
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/21
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/22
- Depends-On: ISSUE-005

#### Goal
`/archive project list` 명령이 동작하여, 본인의 프로젝트 목록을 메시지 수와 함께 반환한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/cmd_project_list.py` 구현
  - `db.py`에 프로젝트 목록 쿼리 함수 추가: `list_projects()`
  - 프로젝트별 메시지 수 (LEFT JOIN + COUNT)
  - 빈 상태 응답 (ux_spec.md Section 3.6)
- Out:
  - 프로젝트 rename/delete

#### Acceptance Criteria (DoD)
- [ ] `/archive project list` 실행 시 본인의 프로젝트 목록이 이름+메시지 수 형태로 반환된다.
- [ ] 프로젝트가 없으면 `프로젝트가 없습니다. /archive save <제목> <링크> /p <프로젝트> 로 메세지를 저장하면 프로젝트가 자동으로 생성됩니다.` 가 반환된다.
- [ ] 타인의 프로젝트는 결과에 포함되지 않는다.
- [ ] 헤더에 프로젝트 수가 `(N개)` 형태로 포함된다.
- [ ] 각 프로젝트의 메시지 수 단위는 `건`이다.

#### Implementation Notes
- `db.py` 쿼리는 `docs/data_model.md` 쿼리 패턴 8 참조.
- 출력 포맷은 `docs/ux_spec.md` Section 3.6 참조.

#### Tests
- [ ] 시드 데이터로 프로젝트 목록 조회 시 본인 프로젝트만 반환.
- [ ] 각 프로젝트에 올바른 메시지 수 표시.
- [ ] 프로젝트 없을 때 빈 상태 메시지.
- [ ] 타 사용자 프로젝트가 포함되지 않음.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-012: project rename 명령 핸들러 구현
- Track: product
- PRD-Ref: FR-015, US-007
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-012-cmd-project-rename
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/23
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/24
- Depends-On: ISSUE-005

#### Goal
`/archive project rename <기존이름> <새이름>` 명령이 동작하여, 본인 소유 프로젝트의 이름을 변경한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/cmd_project_rename.py` 구현
  - `db.py`에 rename 관련 함수 추가: `rename_project()`
  - 기존 프로젝트 존재 확인
  - 새 이름 중복 확인
  - 성공/에러 응답 (ux_spec.md Section 3.7)
- Out:
  - 프로젝트 삭제, 목록

#### Acceptance Criteria (DoD)
- [ ] `/archive project rename BE Backend` 실행 시 프로젝트 이름이 변경되고 `프로젝트 이름을 변경했습니다.\nBE → Backend` 가 반환된다.
- [ ] 기존 프로젝트가 존재하지 않으면 `"BE" 프로젝트를 찾을 수 없습니다.` 가 반환된다.
- [ ] 새 이름이 이미 존재하면 `"Backend" 프로젝트가 이미 존재합니다. 다른 이름을 입력하세요.` 가 반환된다.
- [ ] 인자 부족 시 `사용법: /archive project rename <기존이름> <새이름>` 이 반환된다.
- [ ] 타인의 프로젝트 이름 변경 시도 시 "찾을 수 없습니다" 에러 반환.

#### Implementation Notes
- `db.py` 쿼리는 `docs/data_model.md` 쿼리 패턴 9 참조.
- args에서 첫 번째 토큰 = old_name, 두 번째 토큰 = new_name.

#### Tests
- [ ] 정상 이름 변경 성공.
- [ ] 변경 후 DB에 새 이름 반영 확인.
- [ ] 존재하지 않는 프로젝트 시 에러.
- [ ] 새 이름 중복 시 에러.
- [ ] 인자 부족 시 사용법 안내.
- [ ] 타인 프로젝트 변경 시도 시 에러 (존재 여부 비노출).

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-013: project delete 명령 핸들러 구현
- Track: product
- PRD-Ref: FR-016, FR-017, US-007
- Priority: P1
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-013-cmd-project-delete
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/25
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/26
- Depends-On: ISSUE-005

#### Goal
`/archive project delete <이름>` 명령이 동작하여, 프로젝트를 삭제하고 소속 메시지를 미분류로 전환한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/cmd_project_delete.py` 구현
  - `db.py`에 delete 관련 함수 추가: `delete_project()`
  - 프로젝트 존재 확인
  - 소속 메시지 project_id=NULL 갱신 (트랜잭션 내)
  - 프로젝트 삭제 (트랜잭션 내)
  - 영향받은 메시지 수 응답에 포함
  - 성공/에러 응답 (ux_spec.md Section 3.8)
- Out:
  - 메시지 자체 삭제 (메시지는 보존됨)

#### Acceptance Criteria (DoD)
- [ ] `/archive project delete Backend` 실행 시 프로젝트가 삭제되고 `"Backend" 프로젝트를 삭제했습니다.` 가 반환된다.
- [ ] 삭제된 프로젝트에 속한 메시지들의 project_id가 NULL로 변경된다.
- [ ] 영향받은 메시지가 있으면 응답에 `N건의 메세지가 미분류로 변경되었습니다.` 가 추가된다.
- [ ] 영향받은 메시지가 0건이면 미분류 변경 안내가 생략된다.
- [ ] 메시지 보존: 프로젝트 삭제 전후로 해당 메시지의 총 수가 변하지 않는다.
- [ ] 프로젝트+메시지 갱신이 하나의 트랜잭션으로 실행된다.
- [ ] 존재하지 않는 프로젝트 삭제 시 `"Backend" 프로젝트를 찾을 수 없습니다.` 가 반환된다.
- [ ] 인자 누락 시 `사용법: /archive project delete <프로젝트이름>` 이 반환된다.

#### Implementation Notes
- `db.py` 쿼리는 `docs/data_model.md` 쿼리 패턴 10 참조.
- 10b (UPDATE archives SET project_id=NULL)와 10c (DELETE FROM projects)를 반드시 동일 트랜잭션에서 실행.
- `cursor.rowcount`로 영향받은 메시지 수를 얻을 수 있다.

#### Tests
- [ ] 메시지 있는 프로젝트 삭제 시 메시지 보존 + project_id=NULL 확인.
- [ ] 메시지 없는 프로젝트 삭제 시 응답에 미분류 안내 미포함.
- [ ] 삭제 후 프로젝트가 DB에서 사라짐.
- [ ] 존재하지 않는 프로젝트 삭제 시 에러.
- [ ] 트랜잭션 원자성: 삭제 과정 중 오류 시 롤백 확인.
- [ ] 타인 프로젝트 삭제 시도 시 에러 (존재 여부 비노출).
- [ ] 인자 누락 시 사용법 안내.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-014: help 명령 핸들러 구현
- Track: product
- PRD-Ref: FR-020
- Priority: P1
- Estimate: 0.5d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-014-cmd-help
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/27
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/28
- Depends-On: ISSUE-005

#### Goal
`/archive help` 명령이 UX 스펙에 정의된 도움말 텍스트를 반환한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/cmd_help.py` 구현
  - ux_spec.md Section 3.9에 정의된 도움말 출력 그대로 반환
- Out:
  - 명령별 개별 도움말 (서브커맨드별 help)

#### Acceptance Criteria (DoD)
- [ ] `/archive help` 실행 시 ux_spec.md Section 3.9에 정의된 도움말 텍스트가 반환된다.
- [ ] 도움말에 모든 명령(save, list, search, edit, remove)과 프로젝트 관리 명령(project list, rename, delete)이 포함된다.
- [ ] 구분선(`─`)이 올바르게 표시된다.

#### Implementation Notes
- 도움말 텍스트는 상수 문자열로 정의.
- `docs/ux_spec.md` Section 3.9의 출력을 그대로 복사하여 사용.

#### Tests
- [ ] help 명령 응답에 "save", "list", "search", "edit", "remove" 명령이 포함됨.
- [ ] help 명령 응답에 "project list", "project rename", "project delete" 명령이 포함됨.
- [ ] 응답이 ux_spec.md의 예시와 일치함.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-015: HTTP 브릿지 서버 구현
- Track: platform
- PRD-Ref: FR-023
- Priority: P1
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-015-http-bridge
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/29
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/30
- Depends-On: ISSUE-005

#### Goal
`openclaw-archiver-server` 스크립트로 HTTP 서버가 실행되어 POST /message 와 GET /health 엔드포인트가 동작한다.

#### Scope (In/Out)
- In:
  - `src/openclaw_archiver/server.py` 구현
  - `http.server` 기반 HTTP 서버
  - POST `/message` 엔드포인트: JSON body에서 message, user_id 추출 -> handle_message 호출 -> JSON 응답
  - GET `/health` 엔드포인트: ok, plugin, version 반환
  - 환경변수 `OPENCLAW_ARCHIVER_PORT` (기본값 8201) 지원
  - localhost(127.0.0.1) 바인딩
  - 400 에러 (message/user_id 누락), 500 에러 처리
  - `__main__.py` 에서 서버 실행 연동
- Out:
  - HTTPS, 인증 메커니즘

#### Acceptance Criteria (DoD)
- [ ] `openclaw-archiver-server` 스크립트로 서버가 시작된다.
- [ ] `POST /message` 에 `{"message": "/archive help", "user_id": "U01"}` 전송 시 `{"ok": true, "response": "..."}` 가 반환된다.
- [ ] `POST /message` 에 message 또는 user_id 누락 시 `{"ok": false, "error": "message and user_id are required"}` 가 반환된다 (400).
- [ ] `GET /health` 시 `{"ok": true, "plugin": "archiver", "version": "0.1.0"}` 가 반환된다.
- [ ] 서버가 127.0.0.1에만 바인딩된다.
- [ ] 환경변수 `OPENCLAW_ARCHIVER_PORT` 로 포트 변경이 가능하다.

#### Implementation Notes
- `http.server.HTTPServer` + `BaseHTTPRequestHandler` 사용.
- `docs/architecture.md` API Design 섹션의 HTTP 브릿지 스펙 참조.
- JSON 처리는 `json` 모듈 사용.
- `run()` 함수를 entry point script로 등록 (pyproject.toml에 이미 정의됨).

#### Tests
- [ ] 서버 시작 후 /health GET 요청에 올바른 JSON 응답.
- [ ] /message POST 요청에 올바른 JSON 응답.
- [ ] message/user_id 누락 시 400 에러.
- [ ] 잘못된 JSON body 시 400 에러.
- [ ] 비 /archive 메시지 전송 시 response가 null인 200 응답.
- [ ] (통합 테스트) 실제 save -> list 플로우가 HTTP를 통해 동작.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-016: 데이터 격리 통합 테스트 작성
- Track: product
- PRD-Ref: FR-018, FR-019, US-005
- Priority: P0
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-016-data-isolation
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/31
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/32
- Depends-On: ISSUE-006, ISSUE-007, ISSUE-009, ISSUE-010

#### Goal
데이터 격리(user_id 기반)가 모든 명령에서 올바르게 작동하는지 검증하는 통합 테스트 스위트가 존재한다.

#### Scope (In/Out)
- In:
  - `tests/test_isolation.py` 작성
  - 2명의 사용자(U_TEST_01, U_TEST_02)로 교차 접근 테스트
  - 모든 명령(save, list, search, edit, remove, project *)에 대한 격리 검증
  - 존재 여부 비노출 검증 (타인 데이터 접근 시 "찾을 수 없습니다" 반환)
  - 모든 DB 쿼리에 user_id 조건 포함 여부 코드 검증
- Out:
  - 성능 테스트
  - HTTP 브릿지 테스트

#### Acceptance Criteria (DoD)
- [ ] 사용자 A가 저장한 메시지를 사용자 B가 list로 조회할 수 없다.
- [ ] 사용자 A가 저장한 메시지를 사용자 B가 edit/remove로 수정/삭제할 수 없다.
- [ ] 사용자 A의 프로젝트를 사용자 B가 project rename/delete로 조작할 수 없다.
- [ ] 타인 데이터 접근 시 "존재하지 않음"과 동일한 에러 메시지가 반환된다 (존재 여부 비노출).
- [ ] 사용자 B의 search 결과에 사용자 A의 메시지가 포함되지 않는다.

#### Implementation Notes
- 시드 데이터는 `docs/data_model.md`의 테스트 시드 데이터 SQL을 활용.
- `conftest.py`에 테스트용 DB fixture를 만들고, 시드 데이터를 삽입.
- 각 테스트에서 `handle_message(message, user_id_A)` vs `handle_message(message, user_id_B)` 를 교차 호출.

#### Tests
- [ ] (list 격리) A가 저장한 메시지가 B의 list에 미포함.
- [ ] (search 격리) A가 저장한 메시지가 B의 search에 미포함.
- [ ] (edit 격리) B가 A의 메시지 ID로 edit 시 "찾을 수 없습니다" 반환.
- [ ] (remove 격리) B가 A의 메시지 ID로 remove 시 "찾을 수 없습니다" 반환.
- [ ] (project list 격리) A의 프로젝트가 B의 project list에 미포함.
- [ ] (project rename 격리) B가 A의 프로젝트명으로 rename 시 "찾을 수 없습니다" 반환.
- [ ] (project delete 격리) B가 A의 프로젝트명으로 delete 시 "찾을 수 없습니다" 반환.
- [ ] (에러 메시지 동일성) 존재하지 않는 ID와 타인 소유 ID에 대한 에러 메시지가 동일.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-017: UX 메시지 템플릿 일치 검증 및 최종 통합 테스트
- Track: product
- PRD-Ref: US-001 ~ US-007
- Priority: P1
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-017-ux-messages
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/33
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/34
- Depends-On: ISSUE-006, ISSUE-007, ISSUE-008, ISSUE-009, ISSUE-010, ISSUE-011, ISSUE-012, ISSUE-013, ISSUE-014

#### Goal
모든 명령의 응답 메시지가 `docs/ux_spec.md`에 정의된 템플릿과 정확히 일치하는지 검증하는 테스트 스위트가 존재한다.

#### Scope (In/Out)
- In:
  - `tests/test_ux_messages.py` 작성
  - 모든 성공 메시지 템플릿 검증 (ux_spec Section 4.1)
  - 모든 에러 메시지 템플릿 검증 (ux_spec Section 4.2)
  - 모든 빈 상태 메시지 템플릿 검증 (ux_spec Section 4.3)
  - 용어 사전 준수 확인 (메세지/건/개 등 일관성)
  - 날짜 형식 `YYYY-MM-DD` 검증
  - end-to-end 흐름 테스트: save -> list -> search -> edit -> remove
- Out:
  - 성능 벤치마크
  - HTTP 계층 테스트

#### Acceptance Criteria (DoD)
- [ ] save 성공 메시지가 `저장했습니다. (ID: {id})\n제목: {title}` 패턴과 일치한다.
- [ ] edit 성공 메시지가 `제목을 수정했습니다. (ID: {id})\n{old} → {new}` 패턴과 일치한다.
- [ ] remove 성공 메시지가 `삭제했습니다. (ID: {id})\n{title}` 패턴과 일치한다.
- [ ] 알 수 없는 명령 시 `알 수 없는 명령입니다. /archive help 로 사용법을 확인하세요.` 가 반환된다.
- [ ] 메시지 수 단위가 `건`, 프로젝트 수 단위가 `개`로 일관 사용된다.
- [ ] end-to-end 흐름 (save -> list에서 확인 -> edit -> list에서 확인 -> remove -> list에서 미포함)이 정상 동작한다.

#### Implementation Notes
- 시드 데이터를 활용하거나, 테스트 내에서 save로 데이터를 생성.
- 응답 문자열을 정규식 또는 `in` 연산자로 패턴 매칭.
- `docs/ux_spec.md` Section 3.1~3.10, 4.1~4.3의 모든 예시를 테스트 케이스로 변환.

#### Tests
- [ ] 각 명령의 happy path 응답이 ux_spec 템플릿과 일치.
- [ ] 각 명령의 error path 응답이 ux_spec 템플릿과 일치.
- [ ] 각 명령의 빈 상태 응답이 ux_spec 템플릿과 일치.
- [ ] end-to-end: save -> list -> search -> edit -> remove 전체 흐름 테스트.
- [ ] 날짜 형식이 모든 출력에서 `YYYY-MM-DD` 패턴.

#### Rollback
해당 커밋을 revert한다.

---

## 이슈 의존성 그래프

```
ISSUE-001 (스캐폴딩)
├── ISSUE-002 (스키마/마이그레이션)
│   └── ISSUE-003 (DB 연결)
│       └── ISSUE-005 (디스패처/진입점)
│           ├── ISSUE-006 (save)     ─┐
│           ├── ISSUE-007 (list)      │
│           ├── ISSUE-008 (search)    ├── ISSUE-016 (격리 테스트)
│           ├── ISSUE-009 (edit)      │
│           ├── ISSUE-010 (remove)   ─┘
│           ├── ISSUE-011 (project list)
│           ├── ISSUE-012 (project rename)
│           ├── ISSUE-013 (project delete)
│           ├── ISSUE-014 (help)
│           ├── ISSUE-015 (HTTP 서버)
│           └── ISSUE-006~014 전체 ──── ISSUE-017 (UX 검증)
└── ISSUE-004 (파서) ─── ISSUE-005에 합류

병렬 가능:
- ISSUE-002 와 ISSUE-004 는 독립적으로 병렬 진행 가능
- ISSUE-006~014 는 ISSUE-005 완료 후 모두 병렬 진행 가능
- ISSUE-015 는 ISSUE-006~014 와 병렬 진행 가능
```

---

## NFR-008: Slack mrkdwn 포맷팅 마이그레이션 이슈

> 기존 8칸 들여쓰기 기반 응답 포맷팅을 Slack 네이티브 mrkdwn 서식으로 전면 교체한다.
> 모든 이슈는 ISSUE-001~017 (done) 이후에 수행한다.

### NFR-008 이슈 요약

| ID | 제목 | 우선순위 | 견적 | 의존성 |
|----|------|----------|------|--------|
| ISSUE-018 | formatters.py의 format_archive_rows를 Slack mrkdwn 형식으로 교체 | P0 | 1d | none |
| ISSUE-019 | cmd_list 및 cmd_search 헤더를 mrkdwn 볼드+구분선으로 교체 | P0 | 1d | ISSUE-018 |
| ISSUE-020 | cmd_save 응답을 mrkdwn 볼드 레이블로 교체 | P0 | 0.5d | none |
| ISSUE-021 | cmd_edit 및 cmd_remove 응답을 mrkdwn 볼드 레이블로 교체 | P0 | 0.5d | none |
| ISSUE-022 | cmd_project_list, cmd_project_rename, cmd_project_delete 응답을 mrkdwn으로 교체 | P0 | 1d | none |
| ISSUE-023 | cmd_help 도움말 텍스트를 mrkdwn으로 전면 재작성 | P0 | 0.5d | none |
| ISSUE-024 | NFR-008 준수 검증 테스트 작성 및 기존 테스트 수정 | P0 | 1.5d | ISSUE-018, ISSUE-019, ISSUE-020, ISSUE-021, ISSUE-022, ISSUE-023 |

---

### ISSUE-018: formatters.py의 format_archive_rows를 Slack mrkdwn 형식으로 교체
- Track: product
- PRD-Ref: FR-026, FR-027, FR-028, NFR-008
- Priority: P0
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-018-formatters-mrkdwn
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/39
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/42
- Depends-On: none

#### Goal
`formatters.py`의 `SEPARATOR` 상수와 `format_archive_rows()` 함수가 Slack mrkdwn 형식으로 출력하며, 8칸 들여쓰기와 bare URL이 제거된다.

#### Scope (In/Out)
- In:
  - `SEPARATOR` 상수를 `───` (U+2500 3개)로 축소 (현재 29개 -> ux_spec에 맞게 3개)
  - `format_archive_rows()`가 각 항목을 2행 구조로 출력:
    - 1행: `#{id} {title}` (들여쓰기 없음)
    - 2행: `<{link}|링크> | {project_or_미분류} | {date}` (Slack 링크 형식)
  - `include_project=False` 시 프로젝트명 생략, 2행: `<{link}|링크> | {date}`
  - 항목 간 빈 줄 1개로 구분
- Out:
  - cmd_*.py 파일의 헤더/응답 문자열 변경 (ISSUE-019~023에서 처리)
  - 테스트 수정 (ISSUE-024에서 처리)

#### Acceptance Criteria (DoD)
- [ ] `SEPARATOR`가 `"───"` (U+2500 3개)이다.
- [ ] `format_archive_rows()` 반환값의 어떤 줄도 4칸 이상의 선행 공백으로 시작하지 않는다.
- [ ] 링크가 `<{url}|링크>` Slack 링크 형식으로 출력된다.
- [ ] `include_project=True` 시 프로젝트명이 파이프 구분자로 표시된다 (예: `<url|링크> | Backend | 2026-03-01`).
- [ ] `include_project=True`이고 프로젝트가 없으면 `미분류`로 표시된다.
- [ ] `include_project=False` 시 프로젝트명이 생략되고 `<url|링크> | {date}`로 표시된다.
- [ ] 항목 간 빈 줄(`""`)이 1개씩 삽입된다.

#### Implementation Notes
- 파일: `src/openclaw_archiver/formatters.py`
- `SEPARATOR` 변경: 5행 `"─────────────────────────────"` -> `"───"`
- `format_archive_rows()` 변경: 29~50행 전체 재작성
  - 기존: `f"        #{aid}  {title}"`, `f"            {link}"`, `f"            {proj_label} | {date}"`
  - 변경: `f"#{aid} {title}"`, `f"<{link}|링크> | {proj_label} | {date}"` (include_project=True)
  - 변경: `f"#{aid} {title}"`, `f"<{link}|링크> | {date}"` (include_project=False)
  - `프로젝트: {name}` 레이블을 `{name}`으로 단순화 (ux_spec Section 6.2 참조)
- `format_date()`, `parse_archive_id()`, `require_project()`는 변경 불필요

#### Tests
- [ ] `format_archive_rows()` 5-tuple 입력 시 `<url|링크>` 형식이 출력에 포함된다.
- [ ] `format_archive_rows()` 출력의 모든 줄이 `^ {4,}` 패턴에 매치되지 않는다.
- [ ] `include_project=True`에서 프로젝트명이 `| {name} |` 형태로 포함된다.
- [ ] `include_project=True`에서 프로젝트가 None이면 `| 미분류 |` 가 포함된다.
- [ ] `include_project=False`에서 프로젝트명이 출력에 없다.
- [ ] 항목 간 빈 줄이 정확히 1개씩 존재한다.
- [ ] `SEPARATOR`가 `"───"`과 일치한다.

#### Rollback
해당 커밋을 revert한다. formatters.py만 되돌리면 된다.

---

### ISSUE-019: cmd_list 및 cmd_search 헤더를 mrkdwn 볼드+구분선으로 교체
- Track: product
- PRD-Ref: FR-027, FR-028, NFR-008
- Priority: P0
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-019-list-search-mrkdwn
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/49
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/50
- Depends-On: ISSUE-018

#### Goal
`cmd_list.py`와 `cmd_search.py`의 헤더 문자열이 Slack mrkdwn 볼드 서식과 새 `SEPARATOR`를 사용하며, 8칸 들여쓰기가 제거된다.

#### Scope (In/Out)
- In:
  - `cmd_list.py`: `_list_all()`, `_list_by_project()` 헤더 변경
    - `"저장된 메세지 ({count}건)"` -> `"*저장된 메세지* ({count}건)"`
    - `"저장된 메세지 — {project} ({count}건)"` -> `"*저장된 메세지 — {project}* ({count}건)"`
    - `f"        {SEPARATOR}"` -> `SEPARATOR`
  - `cmd_search.py`: `_search_all()`, `_search_by_project()` 헤더 변경
    - `'검색 결과: "{keyword}" ({count}건)'` -> `'*검색 결과: "{keyword}"* ({count}건)'`
    - `'검색 결과: "{keyword}" — {project} ({count}건)'` -> `'*검색 결과: "{keyword}" — {project}* ({count}건)'`
    - `f"        {SEPARATOR}"` -> `SEPARATOR`
- Out:
  - format_archive_rows 본문 변경 (ISSUE-018에서 완료)
  - 테스트 수정 (ISSUE-024에서 처리)

#### Acceptance Criteria (DoD)
- [ ] `cmd_list._list_all()` 헤더가 `*저장된 메세지* ({count}건)\n───` 형태이다.
- [ ] `cmd_list._list_by_project()` 헤더가 `*저장된 메세지 — {project}* ({count}건)\n───` 형태이다.
- [ ] `cmd_search._search_all()` 헤더가 `*검색 결과: "{keyword}"* ({count}건)\n───` 형태이다.
- [ ] `cmd_search._search_by_project()` 헤더가 `*검색 결과: "{keyword}" — {project}* ({count}건)\n───` 형태이다.
- [ ] 모든 헤더 줄에 8칸 이상의 선행 공백이 없다.
- [ ] 전체 응답 문자열에 4칸 이상의 선행 공백이 없다.

#### Implementation Notes
- 파일: `src/openclaw_archiver/cmd_list.py` (35~61행), `src/openclaw_archiver/cmd_search.py` (40~68행)
- cmd_list.py 41행: `header = [f"저장된 메세지 ({count}건)", f"        {SEPARATOR}"]`
  -> `header = [f"*저장된 메세지* ({count}건)", SEPARATOR]`
- cmd_list.py 56~59행: 유사하게 볼드 래핑 + SEPARATOR 들여쓰기 제거
- cmd_search.py 46행, 63~66행: 동일 패턴 적용
- ux_spec.md Section 4.2, 4.3의 헤더 템플릿 정확히 따르기

#### Tests
- [ ] list 전체 조회 응답 첫 줄이 `*저장된 메세지*`로 시작한다.
- [ ] list 프로젝트 필터 응답 첫 줄에 `*저장된 메세지 —`이 포함된다.
- [ ] search 전체 조회 응답 첫 줄이 `*검색 결과:`로 시작한다.
- [ ] search 프로젝트 범위 응답 첫 줄에 `*검색 결과:`이 포함된다.
- [ ] 모든 응답에서 `^ {4,}` 패턴 매치 줄이 0건이다.
- [ ] 모든 응답에 `───` 구분선이 포함된다.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-020: cmd_save 응답을 mrkdwn 볼드 레이블로 교체
- Track: product
- PRD-Ref: FR-029, NFR-008
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-020-cmd-save-mrkdwn
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/40
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/43
- Depends-On: none

#### Goal
`cmd_save.py`의 성공 응답에서 8칸 들여쓰기가 제거되고 `*제목:*`, `*프로젝트:*` 볼드 레이블이 사용된다.

#### Scope (In/Out)
- In:
  - `cmd_save.py` 26~31행의 응답 문자열 변경:
    - `f"        제목: {title}"` -> `f"*제목:* {title}"`
    - `f"        프로젝트: {project}"` -> `f"*프로젝트:* {project}"`
- Out:
  - 에러/사용법 메시지 (이미 mrkdwn 규칙 준수 -- 들여쓰기 없음)

#### Acceptance Criteria (DoD)
- [ ] save 성공 응답이 `저장했습니다. (ID: {id})\n*제목:* {title}` 형태이다.
- [ ] 프로젝트 지정 시 응답에 `\n*프로젝트:* {project}` 줄이 추가된다.
- [ ] 응답 문자열에 8칸 이상의 선행 공백이 없다.
- [ ] 응답 문자열에 4칸 이상의 선행 공백이 없다.

#### Implementation Notes
- 파일: `src/openclaw_archiver/cmd_save.py` 26~31행
- 기존 코드:
  ```python
  lines = [
      f"저장했습니다. (ID: {archive_id})",
      f"        제목: {title}",
  ]
  if project:
      lines.append(f"        프로젝트: {project}")
  ```
- 변경:
  ```python
  lines = [
      f"저장했습니다. (ID: {archive_id})",
      f"*제목:* {title}",
  ]
  if project:
      lines.append(f"*프로젝트:* {project}")
  ```

#### Tests
- [ ] save 프로젝트 미지정 시 응답이 `저장했습니다. (ID: N)\n*제목:* {title}` 형태이다.
- [ ] save 프로젝트 지정 시 응답 3행이 `*프로젝트:* {project}` 형태이다.
- [ ] 응답에 `"        "` (8칸 공백)이 포함되지 않는다.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-021: cmd_edit 및 cmd_remove 응답을 mrkdwn 볼드 레이블로 교체
- Track: product
- PRD-Ref: FR-029, NFR-008
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-021-cmd-edit-remove-mrkdwn
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/41
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/44
- Depends-On: none

#### Goal
`cmd_edit.py`와 `cmd_remove.py`의 성공 응답에서 8칸 들여쓰기가 제거되고 mrkdwn 볼드 레이블(`*변경:*`, `*제목:*`)이 사용된다.

#### Scope (In/Out)
- In:
  - `cmd_edit.py` 36~39행: `f"        {old_title} → {new_title}"` -> `f"*변경:* {old_title} → {new_title}"`
  - `cmd_remove.py` 33행: `f"삭제했습니다. (ID: {archive_id})\n        {title}"` -> `f"삭제했습니다. (ID: {archive_id})\n*제목:* {title}"`
- Out:
  - 에러/사용법 메시지 (이미 mrkdwn 규칙 준수)

#### Acceptance Criteria (DoD)
- [ ] edit 성공 응답이 `제목을 수정했습니다. (ID: {id})\n*변경:* {old_title} → {new_title}` 형태이다.
- [ ] remove 성공 응답이 `삭제했습니다. (ID: {id})\n*제목:* {title}` 형태이다.
- [ ] 두 명령의 응답 문자열에 4칸 이상의 선행 공백이 없다.

#### Implementation Notes
- `cmd_edit.py` 36~39행:
  - 기존: `f"제목을 수정했습니다. (ID: {archive_id})\n" f"        {old_title} → {new_title}"`
  - 변경: `f"제목을 수정했습니다. (ID: {archive_id})\n" f"*변경:* {old_title} → {new_title}"`
- `cmd_remove.py` 33행:
  - 기존: `f"삭제했습니다. (ID: {archive_id})\n        {title}"`
  - 변경: `f"삭제했습니다. (ID: {archive_id})\n*제목:* {title}"`
- ux_spec.md Section 5.1 템플릿과 정확히 일치하도록 변경

#### Tests
- [ ] edit 성공 응답에 `*변경:*`이 포함된다.
- [ ] edit 성공 응답에 `→` 화살표가 포함된다.
- [ ] remove 성공 응답에 `*제목:*`이 포함된다.
- [ ] 두 명령 응답에 `"        "` (8칸 공백)이 포함되지 않는다.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-022: cmd_project_list, cmd_project_rename, cmd_project_delete 응답을 mrkdwn으로 교체
- Track: product
- PRD-Ref: FR-029, NFR-008
- Priority: P0
- Estimate: 1d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-022-project-cmds-mrkdwn
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/45
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/47
- Depends-On: none

#### Goal
3개 프로젝트 관리 명령의 응답에서 8칸 들여쓰기가 제거되고, mrkdwn 볼드 헤더/레이블과 새 구분선 형식이 사용된다.

#### Scope (In/Out)
- In:
  - `cmd_project_list.py`: 헤더 볼드 + 구분선 변경 + 항목 들여쓰기 제거 + em dash 구분자
  - `cmd_project_rename.py`: 성공 응답 볼드 레이블 + 들여쓰기 제거
  - `cmd_project_delete.py`: 성공 응답 들여쓰기 제거
- Out:
  - 에러/사용법/빈상태 메시지 (이미 mrkdwn 규칙 준수)
  - 테스트 수정 (ISSUE-024에서 처리)

#### Acceptance Criteria (DoD)
- [ ] project list 헤더가 `*프로젝트* ({count}개)\n───` 형태이다.
- [ ] project list 각 항목이 `{name} — {count}건` 형태이다 (em dash 사용, 들여쓰기 없음).
- [ ] project rename 성공 응답이 `프로젝트 이름을 변경했습니다.\n*변경:* {old} → {new}` 형태이다.
- [ ] project delete 성공 응답에서 미분류 안내 줄에 8칸 들여쓰기가 없다.
- [ ] 3개 명령 모든 응답에서 4칸 이상의 선행 공백이 없다.

#### Implementation Notes
- `cmd_project_list.py` (24~26행):
  - 기존: `[f"프로젝트 ({len(projects)}개)", f"        {SEPARATOR}"]`, `f"        {name}     {count}건"`
  - 변경: `[f"*프로젝트* ({len(projects)}개)", SEPARATOR]`, `f"{name} — {count}건"`
  - SEPARATOR import는 유지 (값이 ISSUE-018에서 `───`로 변경됨)
  - 주의: ISSUE-018이 아직 병합되지 않은 경우에도 동작하도록 SEPARATOR 직접 사용
- `cmd_project_rename.py` (38행):
  - 기존: `f"프로젝트 이름을 변경했습니다.\n        {old_name} → {new_name}"`
  - 변경: `f"프로젝트 이름을 변경했습니다.\n*변경:* {old_name} → {new_name}"`
- `cmd_project_delete.py` (27행):
  - 기존: `f"\n        {unlinked}건의 메세지가 미분류로 변경되었습니다."`
  - 변경: `f"\n{unlinked}건의 메세지가 미분류로 변경되었습니다."`

#### Tests
- [ ] project list 응답 첫 줄이 `*프로젝트*`로 시작한다.
- [ ] project list 항목에 ` — ` (em dash)가 포함된다.
- [ ] project rename 응답에 `*변경:*`이 포함된다.
- [ ] project delete 메시지 있는 프로젝트 삭제 시 미분류 안내에 들여쓰기가 없다.
- [ ] 3개 명령의 모든 응답에 `"        "` (8칸 공백)이 포함되지 않는다.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-023: cmd_help 도움말 텍스트를 mrkdwn으로 전면 재작성
- Track: product
- PRD-Ref: FR-030, NFR-008
- Priority: P0
- Estimate: 0.5d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-023-cmd-help-mrkdwn
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/46
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/48
- Depends-On: none

#### Goal
`cmd_help.py`의 도움말 텍스트가 ux_spec.md Section 4.9에 정의된 mrkdwn 형식과 정확히 일치한다.

#### Scope (In/Out)
- In:
  - `cmd_help.py`의 `_HELP_TEXT` 상수 전면 재작성
  - 볼드 명령어 레이블, mrkdwn 구분선, 들여쓰기 제거
- Out:
  - handle() 함수 자체는 변경 불필요

#### Acceptance Criteria (DoD)
- [ ] help 응답이 ux_spec.md Section 4.9의 봇 응답과 정확히 일치한다.
- [ ] 응답 첫 줄이 `*/archive 사용법*`이다.
- [ ] 구분선이 `───`이다.
- [ ] 각 명령어 레이블이 `*저장*`, `*목록*` 등 볼드로 표시된다.
- [ ] `*프로젝트 관리*` 섹션이 별도 줄에 존재한다.
- [ ] 응답 문자열에 4칸 이상의 선행 공백이 없다.
- [ ] 응답 문자열에 백틱 문자가 없다.

#### Implementation Notes
- 파일: `src/openclaw_archiver/cmd_help.py` 7~21행
- 기존 `_HELP_TEXT`를 ux_spec.md Section 4.9의 템플릿으로 완전 교체:
  ```python
  _HELP_TEXT = (
      "*/archive 사용법*\n"
      "───\n"
      "*저장* /archive save <제목> <링크> [/p <프로젝트>]\n"
      "*목록* /archive list [/p <프로젝트>]\n"
      "*검색* /archive search <키워드> [/p <프로젝트>]\n"
      "*수정* /archive edit <ID> <새 제목>\n"
      "*삭제* /archive remove <ID>\n"
      "\n"
      "*프로젝트 관리*\n"
      "───\n"
      "*목록* /archive project list\n"
      "*이름변경* /archive project rename <기존이름> <새이름>\n"
      "*삭제* /archive project delete <프로젝트이름>"
  )
  ```
- `SEPARATOR` import가 더 이상 필요하지 않을 수 있음 (구분선을 인라인으로 넣으므로). 단, 다른 곳에서 사용하므로 import 제거는 선택.

#### Tests
- [ ] help 응답 첫 줄이 `*/archive 사용법*`이다.
- [ ] help 응답에 `*저장*`, `*목록*`, `*검색*`, `*수정*`, `*삭제*`가 포함된다.
- [ ] help 응답에 `*프로젝트 관리*`가 포함된다.
- [ ] help 응답에 `───` 구분선이 2개 포함된다.
- [ ] help 응답에 `"        "` (8칸 공백)이 포함되지 않는다.
- [ ] help 응답이 ux_spec.md Section 4.9의 전체 텍스트와 정확히 일치한다.

#### Rollback
해당 커밋을 revert한다.

---

### ISSUE-024: NFR-008 준수 검증 테스트 작성 및 기존 테스트 수정
- Track: product
- PRD-Ref: FR-026, NFR-008, NFR-008-NEG
- Priority: P0
- Estimate: 1.5d
- Status: done
- Owner: claude
- Branch: issue/ISSUE-024-test-mrkdwn
- GH-Issue: https://github.com/pillip/openclaw_archiver_plugin/issues/51
- PR: https://github.com/pillip/openclaw_archiver_plugin/pull/52
- Depends-On: ISSUE-018, ISSUE-019, ISSUE-020, ISSUE-021, ISSUE-022, ISSUE-023

#### Goal
모든 기존 테스트가 새 mrkdwn 포맷에 맞게 수정되고, NFR-008 준수를 자동 검증하는 새 테스트가 추가된다.

#### Scope (In/Out)
- In:
  - 기존 테스트 assertion 수정 (8칸 들여쓰기 패턴 -> mrkdwn 패턴):
    - `tests/test_cmd_save.py`: `"제목:"` -> `"*제목:*"`, `"프로젝트:"` -> `"*프로젝트:*"`
    - `tests/test_cmd_list.py`: 헤더 볼드 패턴, `format_archive_rows` 출력 형식
    - `tests/test_cmd_search.py`: 헤더 볼드 패턴, 출력 형식
    - `tests/test_cmd_edit.py`: `"→"` 패턴에 `"*변경:*"` 추가
    - `tests/test_cmd_remove.py`: `"*제목:*"` 패턴
    - `tests/test_cmd_project_list.py`: 볼드 헤더, em dash, 들여쓰기 제거
    - `tests/test_cmd_project_rename.py`: `"*변경:*"` 패턴
    - `tests/test_cmd_project_delete.py`: 들여쓰기 제거 확인
    - `tests/test_cmd_help.py`: mrkdwn 도움말 전체 매칭
    - `tests/test_ux_messages.py`: 성공/에러/빈상태 메시지 패턴 업데이트
  - 새 테스트 파일 `tests/test_mrkdwn_compliance.py` 작성:
    - 모든 cmd_*.handle() 함수의 반환값에 대해:
      - `^ {4,}` 패턴 매치 0건 검증
      - 백틱 문자 0건 검증
    - 링크 포함 응답에서 bare URL 없음 검증
    - 링크 포함 응답에서 `<https?://...|...>` 패턴 존재 검증
- Out:
  - 소스 코드 변경 (ISSUE-018~023에서 완료)

#### Acceptance Criteria (DoD)
- [ ] `uv run pytest -q` 가 전체 통과한다 (0 failures).
- [ ] `tests/test_mrkdwn_compliance.py`가 존재하고, 모든 명령 핸들러의 응답에 대해 NFR-008 규칙을 검증한다.
- [ ] 기존 `tests/test_ux_messages.py`의 모든 assertion이 새 mrkdwn 형식에 맞게 업데이트된다.
- [ ] mrkdwn compliance 테스트가 다음을 검증한다:
  - 모든 응답에 4칸 이상 선행 공백 줄 없음
  - 모든 응답에 백틱 없음
  - list/search 응답에 bare URL 없음
  - list/search 응답에 `<url|text>` Slack 링크 형식 존재
- [ ] help 응답이 ux_spec Section 4.9와 정확히 일치하는 테스트가 통과한다.

#### Implementation Notes
- `test_mrkdwn_compliance.py` 구현 전략:
  - 시드 데이터로 각 명령의 happy path 응답을 수집
  - 각 응답에 대해 정규식 검증 수행
  - 검증 패턴 (ux_spec Section 9.4에서 가져옴):
    - `re.compile(r"^ {4,}", re.MULTILINE)` -> 매치 0건
    - `` "`" in response`` -> False
    - `re.compile(r"(?<![|<])https?://\S+(?![|>])")` -> 매치 0건 (링크 포함 응답만)
    - `re.compile(r"<https?://[^|]+\|[^>]+>")` -> 매치 1건 이상 (링크 포함 응답만)
- 기존 테스트 수정 범위:
  - `test_ux_messages.py` TestSaveSuccess: `"제목: "` -> `"*제목:*"`, `"프로젝트: "` -> `"*프로젝트:*"`
  - `test_ux_messages.py` TestEditSuccess: `"→"` assertion에 `"*변경:*"` 추가
  - `test_ux_messages.py` TestRemoveSuccess: 들여쓰기 제거된 패턴 확인
  - `test_ux_messages.py` TestListFormatting: 볼드 헤더 패턴, `"저장된 메세지 (2건)"` -> `"*저장된 메세지* (2건)"`
  - `test_ux_messages.py` TestProjectListFormatting: `"프로젝트 (2개)"` -> `"*프로젝트* (2개)"`
  - `test_ux_messages.py` TestHelpMessage: 볼드 명령어 검증
  - `test_ux_messages.py` TestEndToEnd: 모든 assertion 문자열 패턴 업데이트

#### Tests
- [ ] `test_mrkdwn_compliance.py`: save 응답에 4칸+ 공백 줄 없음.
- [ ] `test_mrkdwn_compliance.py`: list 응답에 bare URL 없고 `<url|링크>` 형식 존재.
- [ ] `test_mrkdwn_compliance.py`: search 응답에 bare URL 없고 `<url|링크>` 형식 존재.
- [ ] `test_mrkdwn_compliance.py`: help 응답에 백틱 없음.
- [ ] `test_mrkdwn_compliance.py`: 모든 cmd_* 응답에 4칸+ 공백 줄 없음.
- [ ] 기존 전체 테스트 스위트 통과 (`uv run pytest -q` 0 failures).

#### Rollback
해당 커밋을 revert한다.

---

## NFR-008 이슈 의존성 그래프

```
ISSUE-018 (formatters mrkdwn) ─────────┐
ISSUE-019 (list/search 헤더) ──────────┤ (ISSUE-019 depends on 018)
ISSUE-020 (save mrkdwn) ──────────────┤
ISSUE-021 (edit/remove mrkdwn) ───────┼── ISSUE-024 (테스트 수정 + 검증)
ISSUE-022 (project cmds mrkdwn) ──────┤
ISSUE-023 (help mrkdwn) ─────────────┘

병렬 가능:
- ISSUE-020, ISSUE-021, ISSUE-022, ISSUE-023은 서로 독립적으로 병렬 진행 가능
- ISSUE-018은 먼저 완료해야 ISSUE-019가 시작 가능
- ISSUE-020~023은 ISSUE-018에 의존하지 않음 (각자 독립적인 파일 수정)
- ISSUE-024는 모든 코드 변경이 완료된 후에 진행
```

---

## 총 견적 요약

### 기존 이슈 (v0 구현, 완료)

| 우선순위 | 이슈 수 | 총 견적 |
|----------|---------|---------|
| P0 | 8개 | 6.5d |
| P1 | 9개 | 7d |
| **소계** | **17개** | **13.5d** |

### NFR-008 이슈 (mrkdwn 마이그레이션)

| 우선순위 | 이슈 수 | 총 견적 |
|----------|---------|---------|
| P0 | 7개 | 5.5d |
| **소계** | **7개** | **5.5d** |

### 전체

| 구분 | 이슈 수 | 총 견적 |
|------|---------|---------|
| 완료 (v0) | 17개 | 13.5d |
| 신규 (NFR-008) | 7개 | 5.5d |
| **합계** | **24개** | **19d** |

NFR-008 크리티컬 패스: ISSUE-018 -> ISSUE-019 -> ISSUE-024
크리티컬 패스 길이: 1d + 1d + 1.5d = **3.5d**

최단 경로 (병렬 활용 시): ISSUE-018 (1d) -> ISSUE-019 + 020 + 021 + 022 + 023 병렬 (1d) -> ISSUE-024 (1.5d) = **3.5d**
