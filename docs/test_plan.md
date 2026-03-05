# Test Plan: OpenClaw Archiver Plugin

> 이 문서는 OpenClaw Archiver Plugin의 테스트 전략, 리스크 매트릭스, 테스트 케이스의 단일 출처이다.
> NFR-008 (Slack mrkdwn 포맷팅) 마이그레이션에 초점을 맞추고 있으며, 기존 기능 회귀 방지를 포함한다.
> 작성일: 2026-03-05

---

## Strategy

### 테스팅 피라미드

| 계층 | 비율 | 대상 | 근거 |
|------|------|------|------|
| Unit | 50% | parser.py, formatters.py 출력 포맷 검증, NFR-008 정규식 기반 자동 검증, 각 cmd_* 핸들러의 응답 문자열 | mrkdwn 마이그레이션의 핵심은 출력 문자열 변경이다. 순수 함수 출력을 정규식으로 검증하는 것이 가장 효율적이다. |
| Integration | 40% | cmd_* + db.py 조합, 데이터 격리, 프로젝트 삭제 원자성, 기능 회귀 검증 | SQLite와의 실제 상호작용을 포함한 CRUD 흐름에서 응답 포맷이 올바른지 검증. |
| E2E | 10% | plugin.handle_message() 전체 흐름, HTTP 브릿지, Slack 렌더링 수동 검증 | 진입점부터 응답까지 전체 경로. 소수의 핵심 시나리오만. |

### 테스트 프레임워크

- **pytest** (팀 표준)
- **pytest-cov**: 커버리지 리포트
- 외부 의존성이 0개인 프로젝트이므로, mock이 필요한 외부 서비스가 없다. SQLite는 `tmp_path` fixture 기반으로 테스트한다.

### CI 통합

| 실행 시점 | 범위 |
|-----------|------|
| 모든 PR | Unit + Integration 테스트, ruff lint, black format check, **NFR-008 포맷 검증** |
| 모든 PR (매트릭스) | Python 3.11, 3.12, 3.13에서 전체 테스트 실행 (NFR-007) |
| Nightly | E2E 테스트, 성능 벤치마크 (NFR-001, NFR-002), 동시성 테스트 (NFR-006) |
| 릴리스 전 | 수동 스모크 테스트, Slack DM에서 실제 mrkdwn 렌더링 확인 |

---

## Risk Matrix

포맷팅 마이그레이션(NFR-008) 관점에서 리스크를 재평가했다.

| 흐름 | 가능성 | 영향도 | 리스크 | 커버리지 레벨 |
|------|--------|--------|--------|---------------|
| NFR-008 위반: 8칸 들여쓰기 잔존 (모든 cmd_*.py) | 높음 | 높음 | **Critical** | Unit (정규식 자동 검증) |
| NFR-008 위반: `<url\|text>` 미적용 (formatters.py) | 높음 | 높음 | **Critical** | Unit (정규식 자동 검증) |
| NFR-008 위반: 볼드 `*label:*` 미적용 또는 오적용 | 높음 | 중간 | **High** | Unit (정규식 + 문자열 비교) |
| 기존 테스트 대량 실패 (R-007: 응답 문자열 assertion 불일치) | 높음 | 중간 | **High** | 전체 테스트 스위트 재작성 |
| 제목에 `*` 포함 시 mrkdwn 볼드 깨짐 (R-008) | 중간 | 낮음 | **Medium** | Unit (엣지 케이스) |
| 기능 회귀: save/list/search/edit/remove CRUD 동작 변경 | 낮음 | 높음 | **High** | Integration |
| 데이터 격리 (user_id 필터 누락) | 낮음 | 치명적 | **Critical** | Integration |
| save 명령 파싱 (공백 제목, URL 추출, /p 분리) | 높음 | 높음 | **Critical** | Unit + Integration |
| project delete 원자성 (메세지 미분류 전환 + 삭제) | 중간 | 높음 | **High** | Integration |
| search LIKE 패턴 성능 (10k+ 레코드) | 중간 | 중간 | **Medium** | 성능 벤치마크 |
| 백틱 코드블럭 잔존 | 중간 | 높음 | **High** | Unit (정규식 자동 검증) |
| help 명령 전면 재작성 후 누락/오류 | 중간 | 낮음 | **Medium** | Unit (문자열 비교) |
| 구분선 변경 (SEPARATOR 상수) | 낮음 | 낮음 | **Low** | Unit |

---

## NFR-008 Format Validation (Cross-cutting)

이 섹션의 검증은 **모든 cmd_\*.py 핸들러에 일괄 적용**된다. 개별 플로우 테스트와 별도로, 응답 문자열 자체에 대한 구조적 검증이다.

### 검증 정규식 (CI 자동 실행)

| 검증 항목 | 정규식 패턴 | 적용 대상 | 기대 매치 수 |
|-----------|------------|-----------|-------------|
| 4칸+ 들여쓰기 없음 | `^ {4,}` (각 줄 대상, multiline) | 모든 cmd_*.py 핸들러 반환 문자열 | 0 |
| 8칸+ 들여쓰기 없음 | `^ {8,}` (각 줄 대상, multiline) | 모든 cmd_*.py 핸들러 반환 문자열 | 0 |
| 백틱 없음 | `` ` `` | 모든 cmd_*.py 핸들러 반환 문자열 | 0 |
| Slack 링크 형식 사용 | `<https?://[^\|]+\|[^>]+>` | link를 포함하는 응답 | 1 이상 |
| bare URL 없음 | `(?<![<\|])https?://\S+(?![>\|])` | link를 포함하는 응답 | 0 |
| 볼드 레이블 사용 | `\*[^*]+:\*` (예: `*제목:*`) | 레이블이 포함된 응답 (save, edit, remove, list header, search header) | 1 이상 |

### NFR-008 Test Cases (전체 핸들러 대상)

| ID | 핸들러 | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|--------|-----------|------|-----------|------|
| MK-001 | cmd_save | DB 비어있음 | `/archive save 제목 https://slack.com/a/1` | 응답의 모든 줄이 4칸 미만 선행 공백. 백틱 0건. `*제목:*` 볼드 레이블 포함 | Unit |
| MK-002 | cmd_save | DB 비어있음 | `/archive save 제목 https://slack.com/a/1 /p Backend` | 응답에 `*제목:*`, `*프로젝트:*` 볼드 레이블 포함. 들여쓰기 없음 | Unit |
| MK-003 | cmd_list | 시드 데이터 로드 | `/archive list` | 각 항목의 link가 `<https://slack.com/..\|링크>` 형식. bare URL 없음. 헤더에 `*저장된 메세지*` 볼드. 8칸 들여쓰기 0건 | Unit |
| MK-004 | cmd_list | 시드 데이터, Backend에 메세지 존재 | `/archive list /p Backend` | 헤더: `*저장된 메세지 — Backend*`. 항목에 프로젝트명 미반복. 들여쓰기 없음 | Unit |
| MK-005 | cmd_search | 시드 데이터 로드 | `/archive search 회의록` | 헤더: `*검색 결과: "회의록"*`. link가 `<url\|링크>` 형식. 들여쓰기 없음 | Unit |
| MK-006 | cmd_search | 시드 데이터, Backend에 메세지 존재 | `/archive search 회의록 /p Backend` | 헤더: `*검색 결과: "회의록" — Backend*`. 항목에 프로젝트명 미반복 | Unit |
| MK-007 | cmd_edit | id=1 메세지 소유 | `/archive edit 1 새제목` | 응답: `제목을 수정했습니다. (ID: 1)\n*변경:* 기존제목 → 새제목`. 들여쓰기 없음. `*변경:*` 볼드 레이블 | Unit |
| MK-008 | cmd_remove | id=1 메세지 소유 | `/archive remove 1` | 응답: `삭제했습니다. (ID: 1)\n*제목:* 스프린트 회의록`. 들여쓰기 없음 | Unit |
| MK-009 | cmd_project_list | 시드 데이터 (2개 프로젝트) | `/archive project list` | 헤더: `*프로젝트*`. 각 항목: `{name} — {count}건`. 들여쓰기 없음 | Unit |
| MK-010 | cmd_project_rename | "BE" 프로젝트 소유 | `/archive project rename BE Backend` | 응답: `프로젝트 이름을 변경했습니다.\n*변경:* BE → Backend`. 들여쓰기 없음 | Unit |
| MK-011 | cmd_project_delete | "Backend" 프로젝트에 3건 메세지 | `/archive project delete Backend` | 들여쓰기 없음. `N건의 메세지가 미분류로 변경되었습니다.` 줄에 선행 공백 없음 | Unit |
| MK-012 | cmd_help | 없음 | `/archive help` | 전체 응답에 8칸 들여쓰기 0건. 4칸 들여쓰기 0건. 백틱 0건. `*/archive 사용법*` 볼드 헤더. 명령어에 `*저장*`, `*목록*` 등 볼드 적용 | Unit |
| MK-013 | 전체 | 없음 | 모든 에러 메시지 (사용법, 못 찾음, 중복 등) | 에러 메시지에 들여쓰기 없음, 백틱 없음 (에러 메시지는 이미 plain text이므로 위반 가능성 낮으나 방어적 검증) | Unit |

### NFR-008 자동 검증 테스트 구현 패턴

```python
# tests/test_mrkdwn_compliance.py

import re
import pytest
from openclaw_archiver.plugin import handle_message

# NFR-008 위반 패턴
_RE_LEADING_4SPACE = re.compile(r"^ {4,}", re.MULTILINE)
_RE_BACKTICK = re.compile(r"`")
_RE_BARE_URL = re.compile(r"(?<![<|])https?://\S+(?![>|])")
_RE_SLACK_LINK = re.compile(r"<https?://[^|]+\|[^>]+>")

def assert_mrkdwn_compliant(response: str, contains_link: bool = False) -> None:
    """Assert a response string complies with NFR-008 rules."""
    assert _RE_LEADING_4SPACE.search(response) is None, (
        f"NFR-008 violation: 4+ space indentation found in:\n{response}"
    )
    assert _RE_BACKTICK.search(response) is None, (
        f"NFR-008 violation: backtick found in:\n{response}"
    )
    if contains_link:
        assert _RE_BARE_URL.search(response) is None, (
            f"NFR-008 violation: bare URL found in:\n{response}"
        )
        assert _RE_SLACK_LINK.search(response) is not None, (
            f"NFR-008 violation: no <url|text> Slack link in:\n{response}"
        )
```

---

## Critical Flows (리스크 순)

### Flow 1: NFR-008 mrkdwn 포맷 준수 (Cross-cutting)

- **리스크 레벨**: Critical
- **관련 요구사항**: NFR-008, FR-026, FR-027, FR-028, FR-029, FR-030

이 플로우는 단일 기능이 아니라 **모든 응답**에 적용되는 횡단 관심사이다. mrkdwn 마이그레이션의 핵심 리스크: (1) 변환 누락으로 8칸 들여쓰기가 잔존, (2) bare URL이 Slack에서 코드블럭 내에 표시되어 클릭 불가, (3) 볼드 서식 미적용으로 가독성 저하.

#### 현재 코드 상태 (변경 필요)

| 파일 | 위반 유형 | 구체적 위치 |
|------|-----------|-------------|
| `formatters.py` | 8칸 들여쓰기, bare URL | `format_archive_rows()`: `f"        #{aid}  {title}"`, `f"            {link}"` |
| `cmd_save.py` | 8칸 들여쓰기, 볼드 미적용 | `f"        제목: {title}"`, `f"        프로젝트: {project}"` |
| `cmd_edit.py` | 8칸 들여쓰기, 볼드 미적용 | `f"        {old_title} → {new_title}"` |
| `cmd_remove.py` | 8칸 들여쓰기, 볼드 미적용 | `f"        {title}"` |
| `cmd_list.py` | 8칸 들여쓰기 | `f"        {SEPARATOR}"` |
| `cmd_search.py` | 8칸 들여쓰기 | `f"        {SEPARATOR}"` |
| `cmd_project_list.py` | 8칸 들여쓰기, 볼드 미적용 | `f"        {name}     {count}건"`, `f"        {SEPARATOR}"` |
| `cmd_project_rename.py` | 8칸 들여쓰기, 볼드 미적용 | `f"        {old_name} → {new_name}"` |
| `cmd_project_delete.py` | 8칸 들여쓰기 | `f"        {unlinked}건의 메세지가..."` |
| `cmd_help.py` | 8칸 들여쓰기, 볼드 미적용 | 전체 `_HELP_TEXT` 상수 |

#### Test Cases -- 포맷 변환 정확성

| ID | 핸들러 | 입력 | 기대 응답 (정확한 문자열) | 타입 |
|----|--------|------|--------------------------|------|
| MK-100 | cmd_save | `save 회의록 https://slack.com/a/1` | `저장했습니다. (ID: 1)\n*제목:* 회의록` | Unit |
| MK-101 | cmd_save | `save 회의록 https://slack.com/a/1 /p Backend` | `저장했습니다. (ID: 1)\n*제목:* 회의록\n*프로젝트:* Backend` | Unit |
| MK-102 | cmd_edit | (id=1, old_title="원래") `edit 1 수정됨` | `제목을 수정했습니다. (ID: 1)\n*변경:* 원래 → 수정됨` | Unit |
| MK-103 | cmd_remove | (id=1, title="회의록") `remove 1` | `삭제했습니다. (ID: 1)\n*제목:* 회의록` | Unit |
| MK-104 | cmd_project_rename | (old="BE") `project rename BE Backend` | `프로젝트 이름을 변경했습니다.\n*변경:* BE → Backend` | Unit |
| MK-105 | cmd_project_delete | ("Backend", 3건 영향) | `"Backend" 프로젝트를 삭제했습니다.\n3건의 메세지가 미분류로 변경되었습니다.` | Unit |
| MK-106 | cmd_project_delete | ("Empty", 0건 영향) | `"Empty" 프로젝트를 삭제했습니다.` | Unit |

#### Test Cases -- list/search mrkdwn 출력 구조

| ID | 핸들러 | 조건 | 기대 응답 구조 | 타입 |
|----|--------|------|----------------|------|
| MK-110 | cmd_list (전체) | 1건 메세지, 미분류 | `*저장된 메세지* (1건)\n───\n#1 {title}\n<{link}\|링크> \| 미분류 \| {date}` | Unit |
| MK-111 | cmd_list (전체) | 2건 메세지 | 항목 사이에 빈 줄 1개 (`\n\n`) 구분 | Unit |
| MK-112 | cmd_list (프로젝트) | Backend 프로젝트, 1건 | `*저장된 메세지 — Backend* (1건)\n───\n#1 {title}\n<{link}\|링크> \| {date}` (프로젝트명 미반복) | Unit |
| MK-113 | cmd_search (전체) | "회의록" 2건 매칭 | `*검색 결과: "회의록"* (2건)\n───\n#{id} {title}\n<{link}\|링크> \| {project_or_미분류} \| {date}` | Unit |
| MK-114 | cmd_search (프로젝트) | Backend 내 "회의록" 1건 | `*검색 결과: "회의록" — Backend* (1건)\n───\n...` (프로젝트명 미반복) | Unit |
| MK-115 | cmd_project_list | 2개 프로젝트 | `*프로젝트* (2개)\n───\nBackend — 2건\nFrontend — 1건` | Unit |

#### Test Cases -- help mrkdwn 출력

| ID | 행위 | 기대 응답 | 타입 |
|----|------|-----------|------|
| MK-120 | `/archive help` | 첫 줄: `*/archive 사용법*`. `───` 구분선 포함. `*저장*`, `*목록*`, `*검색*`, `*수정*`, `*삭제*` 볼드 명령어. `*프로젝트 관리*` 볼드 섹션 헤더. 4칸+ 들여쓰기 0건. 백틱 0건 | Unit |
| MK-121 | `/archive help` 응답 전체 | UX spec Section 4.9의 템플릿과 정확히 일치: `*/archive 사용법*\n───\n*저장* /archive save <제목> <링크> [/p <프로젝트>]\n...` | Unit |

---

### Flow 2: 제목에 mrkdwn 특수문자 포함 (R-008 대응)

- **리스크 레벨**: Medium
- **관련 요구사항**: NFR-008, R-008, UX Spec Section 2.4

사용자가 입력한 제목에 `*` 문자가 포함된 경우, 볼드 서식이 레이블에만 적용되어야 하며 사용자 입력은 볼드로 감싸지 않아야 한다. 감쌀 경우 `*v1*beta* 릴리즈*`와 같이 Slack 렌더링이 깨진다.

#### Test Cases

| ID | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|-----------|------|-----------|------|
| MK-200 | DB 비어있음 | `/archive save v1*beta* 릴리즈 https://slack.com/a/1` | 응답: `저장했습니다. (ID: 1)\n*제목:* v1*beta* 릴리즈`. 제목 자체는 `*`로 감싸지 않음. 레이블 `*제목:*`만 볼드 | Unit |
| MK-201 | id=1 title="v1*beta*" | `/archive edit 1 v2*release*` | 응답: `제목을 수정했습니다. (ID: 1)\n*변경:* v1*beta* → v2*release*`. old/new title 모두 볼드로 감싸지 않음 | Unit |
| MK-202 | title="v1*beta*" 메세지 존재 | `/archive list` | 항목의 제목 줄: `#1 v1*beta* 릴리즈`. 제목이 볼드로 감싸지 않음 | Unit |
| MK-203 | title에 `~`, `_` 포함 | `/archive save ~strikethrough~ _italic_ https://slack.com/a/1` | 정상 저장. 제목 표시 시 mrkdwn 이스케이프 없이 그대로 출력 (v0에서 허용) | Unit |
| MK-204 | 프로젝트명에 `*` 포함 | `/archive save 제목 https://slack.com/a/1 /p *특수*프로젝트` | 저장 성공. `*프로젝트:*` 레이블만 볼드이고 프로젝트명은 볼드 미적용 | Unit |

---

### Flow 3: 메세지 저장 파싱 및 저장 (기능 회귀)

- **리스크 레벨**: Critical
- **관련 요구사항**: FR-001, FR-002, FR-003, FR-004, FR-005, R-002

포맷팅 변경 후에도 파싱 로직과 DB 저장이 정확히 동일하게 동작하는지 검증한다.

#### Test Cases

| ID | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|-----------|------|-----------|------|
| TC-001 | DB 비어있음 | `/archive save 회의록 https://slack.com/archives/C01/p123` | archives 테이블에 title="회의록", link="https://slack.com/archives/C01/p123", project_id=NULL. 응답에 `(ID: 1)`, `*제목:* 회의록` 포함 | Integration |
| TC-002 | DB 비어있음 | `/archive save 스프린트 회의록 https://slack.com/archives/C01/p123` | title="스프린트 회의록" (공백 포함 제목 정상 처리) | Integration |
| TC-003 | DB 비어있음 | `/archive save 3월 스프린트 회의록 https://slack.com/archives/C01/p123 /p Backend` | title="3월 스프린트 회의록", project="Backend" 자동 생성 후 연결 | Integration |
| TC-004 | "Backend" 프로젝트 존재 | `/archive save 새 메모 https://slack.com/archives/C01/p999 /p Backend` | 기존 Backend 프로젝트에 연결. projects 중복 없음 | Integration |
| TC-005 | DB 비어있음 | `/archive save` (인자 없음) | `사용법: /archive save <제목> <링크> [/p <프로젝트>]` | Unit |
| TC-006 | DB 비어있음 | `/archive save 제목만` (URL 없음) | `사용법: /archive save <제목> <링크> [/p <프로젝트>]` | Unit |
| TC-007 | DB 비어있음 | `/archive save https://slack.com/archives/C01/p123` (제목 없음) | `사용법: /archive save <제목> <링크> [/p <프로젝트>]` | Unit |
| TC-008 | DB 비어있음 | `/archive save a/p 패턴 분석 https://slack.com/archives/C01/p123` | title="a/p 패턴 분석", project=NULL | Unit |
| TC-009 | DB 비어있음 | `/archive save a/p 패턴 분석 https://slack.com/archives/C01/p123 /p Backend` | title="a/p 패턴 분석", project="Backend" | Unit |

---

### Flow 4: 데이터 격리

- **리스크 레벨**: Critical
- **관련 요구사항**: FR-018, FR-019, US-005

격리 실패 = 개인정보 유출. 포맷팅 변경이 격리 로직에 영향을 주지 않는지 확인.

#### Test Cases

| ID | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|-----------|------|-----------|------|
| TC-020 | U_TEST_01이 id=1 메세지 소유 | U_TEST_02가 `/archive list` | U_TEST_01의 메세지 미포함 | Integration |
| TC-021 | U_TEST_01이 id=1 메세지 소유 | U_TEST_02가 `/archive edit 1 새제목` | `해당 메세지를 찾을 수 없습니다. (ID: 1)`. DB에서 title 변경 없음 | Integration |
| TC-022 | U_TEST_01이 id=1 메세지 소유 | U_TEST_02가 `/archive remove 1` | `해당 메세지를 찾을 수 없습니다. (ID: 1)`. 레코드 삭제 없음 | Integration |
| TC-023 | U_TEST_01이 "Backend" 프로젝트 소유 | U_TEST_02가 `/archive project rename Backend NewName` | `"Backend" 프로젝트를 찾을 수 없습니다.` | Integration |
| TC-024 | U_TEST_01이 "Backend" 프로젝트 소유 | U_TEST_02가 `/archive project delete Backend` | `"Backend" 프로젝트를 찾을 수 없습니다.` | Integration |
| TC-025 | U_TEST_01 소유 id=1, id=999 미존재 | U_TEST_02가 edit 1 vs edit 999 | 두 에러 메시지 형식 동일 (존재 여부 유추 불가) | Integration |
| TC-026 | U_TEST_01이 검색 가능 메세지 보유 | U_TEST_02가 `/archive search 회의록` | U_TEST_01 메세지 미포함 | Integration |

---

### Flow 5: 프로젝트 삭제 원자성

- **리스크 레벨**: High
- **관련 요구사항**: FR-016, FR-017, NFR-005

#### Test Cases

| ID | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|-----------|------|-----------|------|
| TC-030 | "Backend" 프로젝트에 3건 메세지 | `/archive project delete Backend` | projects에서 삭제. 3건 project_id=NULL. 응답 포맷 NFR-008 준수 | Integration |
| TC-031 | "Empty" 프로젝트에 0건 메세지 | `/archive project delete Empty` | 삭제됨. `"Empty" 프로젝트를 삭제했습니다.` (미분류 안내 없음) | Integration |
| TC-032 | "Backend" 프로젝트에 5건 메세지 | 프로젝트 삭제 | 삭제 전후 archives 총 수 동일 (메세지 손실 없음) | Integration |

---

### Flow 6: 목록 조회 (기능 + 포맷 통합 검증)

- **리스크 레벨**: Medium
- **관련 요구사항**: FR-006, FR-007, FR-027

#### Test Cases

| ID | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|-----------|------|-----------|------|
| TC-050 | 시드 데이터 (U_TEST_01: 4건) | `/archive list` | 4건 반환. 각 항목에 `<link\|링크>` 형식 link. `*저장된 메세지*` 볼드 헤더. `───` 구분선. created_at 내림차순 | Integration |
| TC-051 | 시드 데이터 | `/archive list /p Backend` | Backend 메세지만 반환. 헤더 `*저장된 메세지 — Backend*`. 항목에 프로젝트명 미반복 | Integration |
| TC-052 | 메세지 없는 사용자 | `/archive list` | `저장된 메세지가 없습니다. /archive save 로 메세지를 저장해보세요.` | Integration |
| TC-053 | "Backend" 프로젝트 존재, 메세지 0건 | `/archive list /p Backend` | `"Backend" 프로젝트에 저장된 메세지가 없습니다.` | Integration |
| TC-054 | "NonExistent" 프로젝트 없음 | `/archive list /p NonExistent` | `"NonExistent" 프로젝트를 찾을 수 없습니다.` | Integration |

---

### Flow 7: 검색

- **리스크 레벨**: Medium
- **관련 요구사항**: FR-008, FR-009, FR-028

#### Test Cases

| ID | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|-----------|------|-----------|------|
| TC-060 | 시드 데이터 | `/archive search 회의록` | 2건 반환. 헤더: `*검색 결과: "회의록"* (2건)`. link가 `<url\|링크>` 형식 | Integration |
| TC-061 | 시드 데이터 | `/archive search 회의록 /p Backend` | Backend 내 1건. 헤더: `*검색 결과: "회의록" — Backend*` | Integration |
| TC-062 | 시드 데이터 | `/archive search 없는키워드` | `"없는키워드"에 대한 검색 결과가 없습니다.` | Integration |
| TC-063 | 없음 | `/archive search` | `사용법: /archive search <키워드> [/p <프로젝트>]` | Unit |
| TC-064 | "NonExistent" 없음 | `/archive search 회의록 /p NonExistent` | `"NonExistent" 프로젝트를 찾을 수 없습니다.` | Integration |

---

### Flow 8: 제목 수정

- **리스크 레벨**: Medium
- **관련 요구사항**: FR-010, FR-011, FR-029

#### Test Cases

| ID | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|-----------|------|-----------|------|
| TC-070 | id=1 소유 (title="스프린트 회의록") | `/archive edit 1 수정된 제목` | DB title 변경. 응답: `제목을 수정했습니다. (ID: 1)\n*변경:* 스프린트 회의록 → 수정된 제목` | Integration |
| TC-072 | id=999 미존재 | `/archive edit 999 새제목` | `해당 메세지를 찾을 수 없습니다. (ID: 999)` | Integration |
| TC-073 | 없음 | `/archive edit abc 새제목` | `ID는 숫자여야 합니다. 사용법: /archive edit <ID> <새 제목>` | Unit |
| TC-074 | 없음 | `/archive edit 1` | `사용법: /archive edit <ID> <새 제목>` | Unit |
| TC-075 | 없음 | `/archive edit` | `사용법: /archive edit <ID> <새 제목>` | Unit |

---

### Flow 9: 메세지 삭제

- **리스크 레벨**: Medium
- **관련 요구사항**: FR-012, FR-013, FR-029

#### Test Cases

| ID | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|-----------|------|-----------|------|
| TC-080 | id=1 소유 (title="스프린트 회의록") | `/archive remove 1` | 레코드 삭제. 응답: `삭제했습니다. (ID: 1)\n*제목:* 스프린트 회의록` | Integration |
| TC-081 | id=999 미존재 | `/archive remove 999` | `해당 메세지를 찾을 수 없습니다. (ID: 999)` | Integration |
| TC-082 | 없음 | `/archive remove abc` | `ID는 숫자여야 합니다. 사용법: /archive remove <ID>` | Unit |
| TC-083 | 없음 | `/archive remove` | `사용법: /archive remove <ID>` | Unit |

---

### Flow 10: 프로젝트 관리

- **리스크 레벨**: Medium
- **관련 요구사항**: FR-014, FR-015, FR-029

#### Test Cases

| ID | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|-----------|------|-----------|------|
| TC-090 | 시드 데이터 (Backend: 2건, Frontend: 1건) | `/archive project list` | 헤더: `*프로젝트* (2개)`. 각 항목: `{name} — {count}건`. 들여쓰기 없음 | Integration |
| TC-091 | 프로젝트 없는 사용자 | `/archive project list` | 빈 상태 메시지 | Integration |
| TC-092 | "BE" 존재, "Backend" 없음 | `/archive project rename BE Backend` | `프로젝트 이름을 변경했습니다.\n*변경:* BE → Backend` | Integration |
| TC-093 | "BE"와 "Backend" 모두 존재 | `/archive project rename BE Backend` | `"Backend" 프로젝트가 이미 존재합니다. 다른 이름을 입력하세요.` | Integration |
| TC-094 | "NonExistent" 없음 | `/archive project rename NonExistent New` | `"NonExistent" 프로젝트를 찾을 수 없습니다.` | Integration |
| TC-095 | 없음 | `/archive project rename` | `사용법: /archive project rename <기존이름> <새이름>` | Unit |
| TC-096 | 없음 | `/archive project delete` | `사용법: /archive project delete <프로젝트이름>` | Unit |

---

### Flow 11: 명령 파싱 및 디스패치

- **리스크 레벨**: High
- **관련 요구사항**: FR-020, FR-021

#### Test Cases

| ID | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|-----------|------|-----------|------|
| TC-040 | 없음 | `/archive help` | 도움말 텍스트 반환 | Unit |
| TC-041 | 없음 | `/archive hello` | `알 수 없는 명령입니다. /archive help 로 사용법을 확인하세요.` | Unit |
| TC-042 | 없음 | `/archive` | `알 수 없는 명령입니다. /archive help 로 사용법을 확인하세요.` | Unit |
| TC-043 | 없음 | `안녕하세요` | handle_message 반환값: None | Unit |
| TC-044 | 없음 | 모든 하위 명령 | 각각 올바른 cmd_* 핸들러로 라우팅 | Unit |

---

### Flow 12: DB 초기화 및 HTTP 브릿지

- **리스크 레벨**: Medium
- **관련 요구사항**: FR-024, FR-025, FR-022, FR-023

#### Test Cases

| ID | 전제 조건 | 행위 | 기대 결과 | 타입 |
|----|-----------|------|-----------|------|
| TC-100 | DB 파일 없음 | get_connection() 호출 | 테이블/인덱스 생성. user_version=1 | Integration |
| TC-103 | DB 연결 | PRAGMA journal_mode 조회 | WAL 모드 활성화 | Integration |
| TC-104 | DB 연결 | PRAGMA foreign_keys 조회 | 값=1 (ON) | Integration |
| TC-105 | HTTP 서버 실행 | POST /message help | 200 OK, JSON response. 응답 내용이 NFR-008 준수 | E2E |
| TC-106 | HTTP 서버 실행 | POST /message 필수 필드 누락 | 400 Bad Request | E2E |
| TC-107 | HTTP 서버 실행 | GET /health | 200 OK, `{"ok": true, "plugin": "archiver"}` | E2E |

---

## Edge Cases & Boundary Tests

### mrkdwn 관련 엣지 케이스

| ID | 설명 | 입력 | 기대 결과 | 타입 |
|----|------|------|-----------|------|
| EC-MK-001 | 제목에 `*` 포함 (볼드 간섭) | `/archive save *굵은글씨* 테스트 https://slack.com/a/1` | 저장 성공. `*제목:*` 레이블만 볼드. 제목 자체 `*굵은글씨*`는 볼드 래핑 없음 | Unit |
| EC-MK-002 | 제목에 `<>` 포함 (Slack 링크 간섭) | `/archive save <test> 메모 https://slack.com/a/1` | 저장 성공. list에서 `<>` 가 Slack 링크로 오인되지 않음 | Unit |
| EC-MK-003 | 제목에 `|` 포함 (pipe 문자) | `/archive save A\|B 메모 https://slack.com/a/1` | 저장 성공. list에서 `<url\|링크>` 형식의 pipe와 혼동 없음 | Unit |
| EC-MK-004 | 매우 긴 제목 (Slack 4000자 근접) | title = "가" * 3900 + 짧은 URL | 저장 성공. 응답이 정상 반환됨 (4000자 제한은 Slack 클라이언트 측 문제) | Unit |
| EC-MK-005 | 유니코드 제목 (CJK, 이모지) | `/archive save 한글テスト https://slack.com/a/1` | 정상 저장 및 list/search에서 정상 표시 | Integration |
| EC-MK-006 | 구분선 문자가 제목에 포함 | `/archive save ─── 구분선 테스트 https://slack.com/a/1` | 저장 성공. 구분선과 제목 구분 가능 | Unit |
| EC-MK-007 | 빈 검색 결과에서 포맷 검증 | `/archive search 없는키워드` | 빈 상태 메시지에 들여쓰기 없음, 백틱 없음 | Unit |
| EC-MK-008 | 프로젝트명에 `*` 포함 | `/archive save 제목 https://slack.com/a/1 /p *test*` | `*프로젝트:*` 레이블만 볼드. 프로젝트명 `*test*`는 볼드 미적용 | Unit |

### 파싱 관련 엣지 케이스

| ID | 설명 | 입력 | 기대 결과 | 타입 |
|----|------|------|-----------|------|
| EC-001 | 빈 제목 (공백만) | `/archive save    https://slack.com/a/1` | 사용법 안내 에러 | Unit |
| EC-002 | 매우 긴 제목 | title = "가" * 1000 + URL | 정상 저장 | Unit |
| EC-003 | URL이 여러 개 | `/archive save 제목 https://a.com https://b.com` | 정의된 동작 확인 (첫 번째 URL 추출) | Unit |
| EC-004 | /p 뒤에 프로젝트명 없음 | `/archive save 제목 https://... /p` | 프로젝트명 빈 문자열 처리 | Unit |
| EC-005 | SQL injection 시도 | `/archive save '; DROP TABLE archives; -- https://...` | 정상 저장 (파라미터 바인딩) | Integration |

### ID 관련 엣지 케이스

| ID | 설명 | 입력 | 기대 결과 | 타입 |
|----|------|------|-----------|------|
| EC-010 | ID = 0 | `/archive edit 0 새제목` | 찾을 수 없음 에러 | Integration |
| EC-011 | ID = 음수 | `/archive edit -1 새제목` | 에러 반환 | Unit |
| EC-012 | ID = 매우 큰 수 | `/archive remove 99999999999` | 찾을 수 없음 에러 | Integration |
| EC-013 | ID = 소수점 | `/archive edit 1.5 새제목` | `ID는 숫자여야 합니다` | Unit |

---

## Test Data & Fixtures

### pytest fixture 설계

```python
# conftest.py 구조

@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """임시 DB 경로 생성 및 환경변수 설정."""
    path = os.path.join(str(tmp_path), "test.sqlite3")
    conn = get_connection(path)
    conn.close()
    monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", path)
    return path

@pytest.fixture
def seeded_db(db_path):
    """data_model.md의 시드 데이터가 로드된 DB.
    2명의 사용자, 3개 프로젝트, 5개 아카이브."""
    conn = get_connection(db_path)
    conn.executescript(SEED_SQL)
    conn.close()
    return db_path

USER_01 = "U_TEST_01"
USER_02 = "U_TEST_02"
```

### 시드 데이터 (data_model.md 기반)

```sql
INSERT OR IGNORE INTO projects (id, user_id, name, created_at) VALUES
    (1, 'U_TEST_01', 'Backend', '2026-02-01 00:00:00'),
    (2, 'U_TEST_01', 'Frontend', '2026-02-05 00:00:00'),
    (3, 'U_TEST_02', 'Backend', '2026-02-10 00:00:00');

INSERT OR IGNORE INTO archives (id, user_id, project_id, title, link, created_at) VALUES
    (1, 'U_TEST_01', 1, '스프린트 회의록', 'https://slack.com/archives/C01/p001', '2026-02-15 00:00:00'),
    (2, 'U_TEST_01', 1, '코드 리뷰 가이드', 'https://slack.com/archives/C01/p002', '2026-02-16 00:00:00'),
    (3, 'U_TEST_01', NULL, '주간 회의록 정리', 'https://slack.com/archives/C02/p003', '2026-02-17 00:00:00'),
    (4, 'U_TEST_01', 2, 'CSS 스타일 가이드', 'https://slack.com/archives/C03/p004', '2026-02-18 00:00:00'),
    (5, 'U_TEST_02', 3, '스프린트 회의록', 'https://slack.com/archives/C04/p005', '2026-02-19 00:00:00');
```

### mrkdwn 엣지 케이스 테스트 데이터

```python
# 특수문자가 포함된 제목 목록 (MK-200~204, EC-MK-001~008용)
MRKDWN_EDGE_TITLES = [
    "v1*beta* 릴리즈 노트",         # 볼드 간섭
    "<script>alert(1)</script>",      # HTML 태그
    "A|B 파이프 테스트",              # pipe 문자
    "~취소선~ 테스트",                # strikethrough
    "_이탤릭_ 테스트",                # italic
    "───구분선 포함───",              # 구분선 문자
    "제목 with  multiple   spaces",   # 다중 공백
    "",                                # 빈 문자열 (에러 케이스)
]
```

### 성능 테스트용 데이터

```python
@pytest.fixture
def large_db(db_path):
    """NFR-002 검증용. 단일 사용자 10,000건 아카이브."""
    conn = get_connection(db_path)
    for i in range(100):
        conn.execute(
            "INSERT INTO projects (user_id, name) VALUES (?, ?)",
            ("U_PERF", f"Project_{i}")
        )
    for i in range(10000):
        conn.execute(
            "INSERT INTO archives (user_id, project_id, title, link) VALUES (?, ?, ?, ?)",
            ("U_PERF", (i % 100) + 1, f"테스트 메세지 {i}", f"https://slack.com/archives/C01/p{i}")
        )
    conn.commit()
    conn.close()
    return db_path
```

### 민감 정보 처리

- 테스트에서 실제 Slack user ID를 사용하지 않는다. `U_TEST_01`, `U_TEST_02`, `U_PERF` 등 테스트용 ID만 사용.
- 테스트 DB는 `tmp_path` fixture로 테스트 종료 시 자동 삭제.

---

## Automation Candidates

### CI (모든 PR)

| 범위 | 명령 | 소요 시간 |
|------|------|-----------|
| 린트 | `uv run ruff check .` | < 5s |
| 포맷 체크 | `uv run black --check .` | < 5s |
| **NFR-008 포맷 검증** | `uv run pytest tests/test_mrkdwn_compliance.py -q` | < 10s |
| Unit 테스트 | `uv run pytest -q -m "not integration and not e2e"` | < 10s |
| Integration 테스트 | `uv run pytest -q -m integration` | < 30s |
| 커버리지 | `uv run pytest --cov=src/openclaw_archiver --cov-report=term-missing` | 포함 |
| Python 매트릭스 | 3.11, 3.12, 3.13에서 전체 테스트 | x3 |

### NFR-008 전용 자동 검증 (매 PR 필수)

```python
# tests/test_mrkdwn_compliance.py -- CI에서 모든 PR 대상으로 실행
#
# 이 파일은 모든 cmd_*.py 핸들러의 응답 문자열을 수집하여
# NFR-008 규칙을 정규식으로 검증한다.
#
# 검증 전략:
# 1. 각 핸들러의 happy path + error path 응답을 생성
# 2. 모든 응답에 대해 assert_mrkdwn_compliant() 호출
# 3. link를 포함하는 응답에 대해 <url|text> 형식 검증
#
# 이 테스트가 실패하면 PR이 merge될 수 없다.
```

### Nightly

| 범위 | 명령 | 소요 시간 |
|------|------|-----------|
| E2E 테스트 | `uv run pytest -q -m e2e` | < 60s |
| 성능 벤치마크 (NFR-001) | `uv run pytest -q -m performance` | < 120s |
| 검색 성능 (NFR-002) | `uv run pytest -q -m search_performance` | < 120s |
| 동시성 (NFR-006) | `uv run pytest -q -m concurrency` | < 60s |

### 수동 검증

| 항목 | 빈도 | 담당 |
|------|------|------|
| Slack DM에서 mrkdwn 렌더링 확인 (볼드, 링크 클릭 가능, 구분선) | 릴리스 전 | QA |
| list 응답에서 link가 클릭 가능한 하이퍼링크인지 확인 | 릴리스 전 | QA |
| help 응답이 코드블럭이 아닌 일반 텍스트로 렌더링되는지 확인 | 릴리스 전 | QA |
| HTTP 브릿지 서버 수동 curl 테스트 | 릴리스 전 | 개발자 |

---

## 기존 테스트 마이그레이션 영향 분석

NFR-008 적용 시 기존 테스트 파일에서 assertion이 실패하는 위치를 사전 식별한다.

### 영향받는 기존 테스트 파일

| 테스트 파일 | 영향받는 assertion | 변경 내용 |
|------------|-------------------|-----------|
| `tests/test_ux_messages.py` | `TestSaveSuccess`: `"제목: 스프린트 회의록"` 검색 | `"*제목:* 스프린트 회의록"`으로 변경 |
| `tests/test_ux_messages.py` | `TestSaveSuccess`: `"프로젝트: Backend"` 검색 | `"*프로젝트:* Backend"`으로 변경 |
| `tests/test_ux_messages.py` | `TestEditSuccess`: `"원래제목 → 수정된제목"` 검색 | `"*변경:* 원래제목 → 수정된제목"`으로 변경 |
| `tests/test_ux_messages.py` | `TestRemoveSuccess`: `"삭제대상"` 검색 | `"*제목:* 삭제대상"`으로 변경 |
| `tests/test_ux_messages.py` | `TestProjectRenameSuccess`: `"BE → Backend"` 검색 | `"*변경:* BE → Backend"`으로 변경 |
| `tests/test_ux_messages.py` | `TestListFormatting`: `"저장된 메세지 (2건)"` 검색 | `"*저장된 메세지* (2건)"`으로 변경 |
| `tests/test_ux_messages.py` | `TestListFormatting.test_list_item_format`: URL bare 검색 | `<url\|링크>` 형식 검증으로 변경 |
| `tests/test_ux_messages.py` | `TestProjectListFormatting`: `"프로젝트 (2개)"` 검색 | `"*프로젝트* (2개)"`으로 변경 |
| `tests/test_ux_messages.py` | `TestHelpMessage`: `"/archive 사용법"` 검색 | `"*/archive 사용법*"`으로 변경 |
| `tests/test_ux_messages.py` | `TestEndToEnd.test_lifecycle_with_project`: `"프로젝트: LifeProj"` | `"*프로젝트:* LifeProj"`으로 변경 |
| `tests/test_cmd_save.py` | `"프로젝트: Backend"` 검색 | `"*프로젝트:* Backend"`으로 변경 |
| `tests/test_cmd_save.py` | `"프로젝트:" not in result` 검색 | `"*프로젝트:*" not in result`로 변경 |

### 마이그레이션 전략

1. `formatters.py`와 `cmd_*.py` 소스 코드를 NFR-008 준수로 변경
2. 기존 테스트의 assertion을 새 포맷에 맞게 일괄 수정
3. `tests/test_mrkdwn_compliance.py`를 신규 추가하여 정규식 기반 자동 검증
4. 모든 변경을 **하나의 작업 단위**로 묶어 커밋 (R-007 대응)

---

## Release Checklist (Smoke)

5분 이내에 수동으로 실행 가능한 핵심 경로 점검 목록이다.

- [ ] `/archive save 스모크 테스트 https://slack.com/archives/C01/p001 /p TestProject` -- 저장 성공, `*제목:*` 볼드 레이블, `*프로젝트:*` 볼드 레이블 확인
- [ ] `/archive list` -- 방금 저장한 메세지 표시. link가 `<url|링크>` 형식으로 **클릭 가능**. 8칸 들여쓰기 없음. `*저장된 메세지*` 볼드 헤더
- [ ] `/archive list /p TestProject` -- 프로젝트 필터 동작. 헤더에 `*저장된 메세지 — TestProject*`
- [ ] `/archive search 스모크` -- 검색 결과 표시. `*검색 결과:*` 볼드. link 클릭 가능
- [ ] `/archive edit {id} 수정된 제목` -- `*변경:*` 볼드 레이블. 화살표 `→` 표시
- [ ] `/archive remove {id}` -- `*제목:*` 볼드 레이블. 삭제 후 list에서 미표시
- [ ] `/archive project list` -- `*프로젝트*` 볼드 헤더. `───` 구분선. 들여쓰기 없음
- [ ] `/archive project delete TestProject` -- 프로젝트 삭제. 미분류 전환 메시지에 들여쓰기 없음
- [ ] `/archive help` -- 도움말에 코드블럭(들여쓰기) 없이 mrkdwn 서식으로 표시. `*저장*`, `*목록*` 등 볼드 명령어
- [ ] `/archive 없는명령` -- "알 수 없는 명령입니다" 응답 (들여쓰기/백틱 없음)
- [ ] 다른 user_id로 `/archive list` -- 이전 사용자 데이터 미노출
- [ ] (Slack에서 확인) list 응답의 URL이 클릭 시 해당 Slack 메시지로 이동하는지 확인
