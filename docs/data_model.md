# Data Model

> OpenClaw Archiver Plugin 데이터 모델 명세서
> 이 문서는 데이터베이스 스키마, 접근 패턴, 쿼리, 마이그레이션 전략의 단일 출처(Single Source of Truth)이다.

---

## 저장소 전략

### 주 저장소: SQLite 3 (WAL 모드)

- **선택 근거**: NFR-003 (외부 의존성 0개) 제약으로 Python 표준 라이브러리의 `sqlite3` 모듈만 사용한다. 로컬 파일 기반으로 설치/설정이 필요 없고, WAL 모드로 읽기-쓰기 동시성을 확보한다 (NFR-006).
- **파일 경로**: `~/.openclaw/workspace/.archiver/archiver.sqlite3` (환경변수 `OPENCLAW_ARCHIVER_DB_PATH`로 재정의 가능)
- **연결 시 PRAGMA 설정**:
  - `PRAGMA journal_mode=WAL` -- 동시성 확보 (NFR-006)
  - `PRAGMA foreign_keys=ON` -- 외래 키 제약 활성화 (NFR-005)
- **연결 관리**: 요청 단위로 `db.get_connection()` 호출하여 새 연결을 생성한다. 연결 풀 없음. SQLite 파일 연결은 오픈 비용이 낮으므로 풀링은 불필요하다.

### 보조 저장소

- 없음. 캐시, 검색 인덱스, 파일 저장소 등 별도 저장소를 사용하지 않는다.

---

## 접근 패턴

모든 접근 패턴은 `user_id` 필터를 포함한다 (FR-018, 데이터 격리).

| 패턴 | 출처 | 작업 | 빈도 | 지연 목표 |
|------|------|------|------|-----------|
| 메세지 저장 | cmd_save (FR-001~005) | write | 높음 | p95 < 200ms (NFR-001) |
| 프로젝트 자동 생성 | cmd_save (FR-003) | write | 중간 (저장 시 프로젝트 지정 시에만) | p95 < 200ms (NFR-001) |
| 전체 목록 조회 | cmd_list (FR-006) | read | 높음 | p95 < 200ms (NFR-001) |
| 프로젝트별 목록 조회 | cmd_list (FR-007) | read | 중간 | p95 < 200ms (NFR-001) |
| 키워드 검색 | cmd_search (FR-008) | read | 중간 | p95 < 500ms (NFR-002) |
| 키워드+프로젝트 검색 | cmd_search (FR-009) | read | 낮음 | p95 < 500ms (NFR-002) |
| 제목 수정 | cmd_edit (FR-010~011) | read+write | 낮음 | p95 < 200ms (NFR-001) |
| 메세지 삭제 | cmd_remove (FR-012~013) | read+write | 낮음 | p95 < 200ms (NFR-001) |
| 프로젝트 목록 조회 | cmd_project_list (FR-014) | read | 낮음 | p95 < 200ms (NFR-001) |
| 프로젝트 이름 변경 | cmd_project_rename (FR-015) | write | 낮음 | p95 < 200ms (NFR-001) |
| 프로젝트 삭제 | cmd_project_delete (FR-016~017) | write | 낮음 | p95 < 200ms (NFR-001) |
| 프로젝트 존재 확인 | cmd_list, cmd_search (FR-007, FR-009) | read | 중간 | p95 < 200ms (NFR-001) |

---

## 스키마

### Entity Relationship

```
projects 1 --- * archives
   |                |
   +-- id (PK)      +-- id (PK)
   +-- user_id      +-- user_id (denormalized)
   +-- name         +-- project_id (FK, nullable)
   +-- created_at   +-- title
                    +-- link
                    +-- created_at
```

- **projects**: 사용자별 프로젝트. `(user_id, name)` 유니크 제약.
- **archives**: 저장된 메세지 링크. `project_id`가 NULL이면 미분류.
- **관계**: archives.project_id -> projects.id (N:1, nullable). 프로젝트 삭제 시 FK cascade가 아닌 애플리케이션 레벨에서 NULL 갱신 후 삭제 (FR-016, FR-017).
- **user_id 비정규화**: user_id가 두 테이블 모두에 존재한다. 이는 모든 쿼리에서 JOIN 없이 `WHERE user_id = ?` 필터링을 가능하게 하여 데이터 격리(FR-018) 구현을 단순화한다. 약간의 저장소 중복을 감수한 의도적 설계이다.

### 테이블: projects

| 컬럼 | 타입 | 제약 | 기본값 | 설명 |
|------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 자동 생성 | 프로젝트 고유 식별자 |
| user_id | TEXT | NOT NULL | - | Slack 사용자 ID. 데이터 격리 기준 (FR-018) |
| name | TEXT | NOT NULL | - | 프로젝트 이름. 사용자별 유니크 |
| created_at | TEXT | NOT NULL | `datetime('now')` | 생성 시각 (UTC, ISO 8601 형식) |

- **유니크 제약**: `UNIQUE(user_id, name)` -- 동일 사용자 내 프로젝트명 중복 방지 (FR-015)
- **updated_at 미포함 근거**: projects 테이블에서 변경 가능한 필드는 `name`뿐이며, 변경 이력 추적 요구사항이 없다. PRD에 undo/recovery 기능이 없으므로 soft delete도 미적용.

### 테이블: archives

| 컬럼 | 타입 | 제약 | 기본값 | 설명 |
|------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 자동 생성 | 아카이브 고유 식별자 |
| user_id | TEXT | NOT NULL | - | Slack 사용자 ID. 데이터 격리 기준 (FR-018) |
| project_id | INTEGER | FOREIGN KEY -> projects(id), nullable | NULL | 소속 프로젝트. NULL이면 미분류 (FR-002) |
| title | TEXT | NOT NULL | - | 메세지 제목 (FR-001) |
| link | TEXT | NOT NULL | - | Slack 메세지 링크 URL (FR-001) |
| created_at | TEXT | NOT NULL | `datetime('now')` | 생성 시각 (UTC, ISO 8601 형식) |

- **외래 키**: `project_id REFERENCES projects(id)` -- 프로젝트 삭제 시 ON DELETE CASCADE를 사용하지 않는다. 애플리케이션 레벨에서 NULL로 갱신한 후 삭제한다 (FR-016, FR-017).
- **updated_at 미포함 근거**: 변경 가능한 필드는 `title`뿐이며, 수정 이력 추적 요구사항이 없다.
- **soft delete 미적용 근거**: PRD에 undo/recovery 기능이 범위 외이다.
- **project_id nullable 결정 근거**: 미분류 메세지를 표현하기 위해 NULL을 허용한다. 별도의 "미분류" 프로젝트를 만들지 않은 이유는 사용자에게 불필요한 프로젝트 레코드를 노출하지 않기 위함이다.

### DDL (소스 파일: `src/openclaw_archiver/schema_v1.py`)

```sql
CREATE TABLE IF NOT EXISTS projects (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL,
    name       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, name)
);

CREATE TABLE IF NOT EXISTS archives (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT NOT NULL,
    project_id INTEGER,
    title      TEXT NOT NULL,
    link       TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

---

## 인덱스

| 테이블 | 인덱스 | 컬럼 | 타입 | 근거 |
|--------|--------|------|------|------|
| archives | `idx_archives_user` | `(user_id)` | btree | 전체 목록 조회 (FR-006), 모든 user_id 기반 필터링의 기본 인덱스. NFR-001 대응. |
| archives | `idx_archives_user_project` | `(user_id, project_id)` | btree (복합) | 프로젝트별 목록 조회 (FR-007), 프로젝트 삭제 시 소속 메세지 갱신 (FR-016), 프로젝트 목록의 COUNT 조인. NFR-001 대응. |
| archives | `idx_archives_title` | `(user_id, title)` | btree (복합) | 키워드 검색 시 user_id 필터링 보조 (FR-008). `LIKE '%keyword%'` 패턴에서는 인덱스 범위 스캔이 불가하므로, 이 인덱스의 실질적 역할은 user_id 필터링 후 title 컬럼 접근 최적화 (covering index)이다. NFR-002 대응. |
| projects | `UNIQUE(user_id, name)` | `(user_id, name)` | btree (유니크) | 프로젝트 존재 확인 (FR-003, FR-007, FR-009), 프로젝트명 중복 방지 (FR-015), INSERT OR IGNORE 충돌 감지. 유니크 제약이 암묵적으로 인덱스를 생성한다. |

### 인덱스 DDL

```sql
CREATE INDEX IF NOT EXISTS idx_archives_user ON archives(user_id);
CREATE INDEX IF NOT EXISTS idx_archives_user_project ON archives(user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_archives_title ON archives(user_id, title);
```

### 인덱스 설계 참고사항

- **idx_archives_title과 LIKE 패턴**: `LIKE '%keyword%'` (중간 일치) 패턴에서 인덱스 범위 스캔을 활용하지 못한다. 이 인덱스의 주 역할은 `user_id` 컬럼의 equality 필터링이며, `idx_archives_user`와 중복되는 면이 있다. 그러나 `(user_id, title)` 복합 인덱스를 통해 covering index로 동작할 수 있어 테이블 접근 없이 title 스캔이 가능하다. 단, 현재 search 쿼리가 `link`, `created_at`, `p.name` 등 추가 컬럼을 SELECT하므로 covering 효과는 제한적이다.
- **NFR-002 (1만 건 500ms) 목표**는 SQLite의 인메모리 스캔 성능으로 충분할 것으로 판단하나, 벤치마크를 통해 검증 필요 (R-003). 성능 미달 시 FTS5 도입을 검토한다.
- **idx_archives_user의 중복성**: `idx_archives_user_project`의 첫 번째 컬럼이 `user_id`이므로, `user_id` 단독 필터링에도 활용 가능하다. 따라서 `idx_archives_user`는 이론적으로 중복이다. 그러나 삭제하지 않은 이유는 SQLite 쿼리 옵티마이저가 단일 컬럼 인덱스를 선호하는 경향이 있고, 전체 목록 조회(가장 빈번한 read 패턴)에 대한 명시적 최적화를 유지하기 위함이다.
- 별도의 "만약을 위한" 인덱스는 추가하지 않았다. 모든 인덱스는 위 접근 패턴에서 도출되었다.

---

## 마이그레이션

### 전략

- **도구**: `PRAGMA user_version` 기반 자체 구현 (NFR-003, 외부 의존성 0개 제약). Alembic 등 외부 마이그레이션 도구를 사용하지 않는다.
- **버전 추적**: SQLite의 `user_version` PRAGMA를 스키마 버전 번호로 사용
- **실행 시점**: `db.get_connection()` 호출마다 `run_migrations()` 실행. `CREATE TABLE IF NOT EXISTS`와 버전 체크로 멱등성 보장.
- **원자성**: `conn.executescript()`를 사용하여 각 마이그레이션의 전체 DDL을 실행. executescript는 내부적으로 트랜잭션을 관리한다.
- **소스 파일**: `src/openclaw_archiver/migrations.py`, `src/openclaw_archiver/schema_v1.py`

### Version 1: 초기 스키마 (현재)

```sql
-- 테이블 생성
CREATE TABLE IF NOT EXISTS projects (...);
CREATE TABLE IF NOT EXISTS archives (...);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_archives_user ON archives(user_id);
CREATE INDEX IF NOT EXISTS idx_archives_user_project ON archives(user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_archives_title ON archives(user_id, title);

-- 버전 설정
PRAGMA user_version = 1;
```

### 마이그레이션 레지스트리 (migrations.py)

```python
MIGRATIONS: dict[int, dict[str, str]] = {
    1: {
        "up": SCHEMA_SQL,  # schema_v1.py의 전체 DDL
        "down": (
            "DROP TABLE IF EXISTS archives;"
            " DROP TABLE IF EXISTS projects;"
            " PRAGMA user_version = 0;"
        ),
    },
}

TARGET_VERSION = max(MIGRATIONS)  # 현재: 1
```

### 롤백 접근

- **DB 파일 백업**: 마이그레이션 실행 전 SQLite 파일을 복사하여 백업한다. 파일 단위 복원이 가장 단순하고 확실하다.
- **Down 마이그레이션**: 각 마이그레이션에 대응하는 rollback DDL을 `migrations.py`에 정의한다. 단, down 마이그레이션을 실행하는 명령이나 API는 제공하지 않는다. `sqlite3` CLI로 수동 실행해야 한다.
- Version 1 롤백 (초기화): `DROP TABLE IF EXISTS archives; DROP TABLE IF EXISTS projects; PRAGMA user_version = 0;` -- 데이터 전체 삭제.

### 향후 마이그레이션 패턴

새 버전을 추가할 때 `MIGRATIONS` 딕셔너리에 항목을 추가한다. `run_migrations()`가 현재 `user_version`과 `TARGET_VERSION`을 비교하여 순차적으로 적용한다.

```python
MIGRATIONS = {
    1: {"up": SCHEMA_V1_SQL, "down": "..."},
    # 2: {
    #     "up": "ALTER TABLE archives ADD COLUMN tags TEXT; PRAGMA user_version = 2;",
    #     "down": "... PRAGMA user_version = 1;"
    # },
}
```

---

## 시드 데이터

이 플러그인은 참조 데이터(reference data)나 기본 설정이 필요하지 않다. 프로젝트는 사용자가 `/archive save ... /p <프로젝트>` 명령으로 암묵적으로 생성하며 (FR-003), 사전 정의된 프로젝트/카테고리가 없다.

### 프로덕션 시드 데이터

없음. 빈 데이터베이스로 시작한다.

### 테스트용 시드 데이터

테스트 환경에서 사용하는 시드 데이터이다. 멱등성을 보장하기 위해 `INSERT OR IGNORE`를 사용한다.

| 테이블 | 데이터 | 용도 |
|--------|--------|------|
| projects | user_id="U_TEST_01", name="Backend" | 프로젝트별 조회/검색 테스트 |
| projects | user_id="U_TEST_01", name="Frontend" | 프로젝트 목록/이름 변경/삭제 테스트 |
| projects | user_id="U_TEST_02", name="Backend" | 데이터 격리 테스트 (동일 프로젝트명, 다른 사용자) |
| archives | user_id="U_TEST_01", project_id=1, title="스프린트 회의록" | 기본 CRUD 테스트 |
| archives | user_id="U_TEST_01", project_id=1, title="코드 리뷰 가이드" | 프로젝트별 목록 테스트 |
| archives | user_id="U_TEST_01", project_id=NULL, title="주간 회의록 정리" | 미분류 메세지 테스트 |
| archives | user_id="U_TEST_01", project_id=2, title="CSS 스타일 가이드" | 다중 프로젝트 테스트 |
| archives | user_id="U_TEST_02", project_id=3, title="스프린트 회의록" | 데이터 격리 테스트 (FR-018, FR-019) |

```sql
-- 시드 데이터 SQL (멱등)
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

---

## 쿼리 패턴

### 1. 메세지 저장 (save)

- **사용처**: cmd_save (FR-001~005)
- **db.py 함수**: `get_or_create_project()`, `insert_archive()`
- **쿼리**:

```sql
-- 1a. 프로젝트 자동 생성 (프로젝트 지정 시에만, FR-003)
INSERT OR IGNORE INTO projects (user_id, name) VALUES (?, ?);

-- 1b. 프로젝트 ID 조회 (프로젝트 지정 시에만)
SELECT id FROM projects WHERE user_id = ? AND name = ?;

-- 1c. 메세지 저장
INSERT INTO archives (user_id, project_id, title, link) VALUES (?, ?, ?, ?);
-- project_id는 미지정 시 NULL
```

- **예상 결과 행수**: INSERT 1건, SELECT 0~1건
- **사용 인덱스**: `UNIQUE(user_id, name)` (1a INSERT OR IGNORE 충돌 확인, 1b 조회)
- **성능**: p95 < 200ms (NFR-001). INSERT는 단일 행이므로 데이터 규모와 무관하게 일정.
- **트랜잭션**: 1a + 1b는 `get_or_create_project()` 내에서 실행. 1c는 별도 `conn.commit()`.

### 2. 전체 목록 조회 (list)

- **사용처**: cmd_list (FR-006)
- **db.py 함수**: `list_archives()`
- **쿼리**:

```sql
SELECT a.id, a.title, a.link, p.name, a.created_at
FROM archives a
LEFT JOIN projects p ON a.project_id = p.id
WHERE a.user_id = ?
ORDER BY a.created_at DESC;
```

- **예상 결과 행수**: 0 ~ 수백 건 (단일 사용자)
- **사용 인덱스**: `idx_archives_user` (user_id equality)
- **성능**: p95 < 200ms (NFR-001). LEFT JOIN은 projects.id (PK) 기반이므로 인덱스 룩업.
- **정렬**: `created_at DESC` -- 최신순. 인덱스에 created_at이 포함되지 않으므로 filesort 발생하나, 단일 사용자 데이터 범위에서는 무시 가능.

### 3. 프로젝트별 목록 조회 (list /p)

- **사용처**: cmd_list (FR-007)
- **db.py 함수**: `find_project()` (또는 `formatters.require_project()`), `list_archives_by_project()`
- **쿼리**:

```sql
-- 3a. 프로젝트 존재 확인
SELECT id, name FROM projects WHERE user_id = ? AND name = ?;

-- 3b. 프로젝트별 메세지 조회
SELECT a.id, a.title, a.link, a.created_at
FROM archives a
WHERE a.user_id = ? AND a.project_id = ?
ORDER BY a.created_at DESC;
```

- **예상 결과 행수**: 3a: 0~1건, 3b: 0 ~ 수십 건
- **사용 인덱스**: 3a: `UNIQUE(user_id, name)`, 3b: `idx_archives_user_project`
- **성능**: p95 < 200ms (NFR-001)

### 4. 키워드 검색 (search)

- **사용처**: cmd_search (FR-008)
- **db.py 함수**: `search_archives()`
- **쿼리**:

```sql
SELECT a.id, a.title, a.link, p.name, a.created_at
FROM archives a
LEFT JOIN projects p ON a.project_id = p.id
WHERE a.user_id = ? AND a.title LIKE ? COLLATE NOCASE
ORDER BY a.created_at DESC;
-- LIKE 파라미터: '%' || keyword || '%'
```

- **예상 결과 행수**: 0 ~ 수십 건
- **사용 인덱스**: `idx_archives_title` (user_id equality로 범위 축소 후 title 스캔). LIKE '%...%' 패턴이므로 인덱스 범위 스캔은 불가하나, user_id 필터링은 인덱스로 처리.
- **성능**: p95 < 500ms (NFR-002). 1만 건 기준. COLLATE NOCASE로 대소문자 무시 (A-009).
- **쿼리 플랜 예상**: `SCAN archives USING INDEX idx_archives_user (user_id=?)` 또는 `idx_archives_title (user_id=?)` 후 title LIKE 필터.

### 5. 키워드+프로젝트 검색 (search /p)

- **사용처**: cmd_search (FR-009)
- **db.py 함수**: `find_project()` (또는 `formatters.require_project()`), `search_archives_by_project()`
- **쿼리**:

```sql
-- 5a. 프로젝트 존재 확인 (3a와 동일)
SELECT id, name FROM projects WHERE user_id = ? AND name = ?;

-- 5b. 프로젝트 범위 검색
SELECT a.id, a.title, a.link, a.created_at
FROM archives a
WHERE a.user_id = ? AND a.project_id = ? AND a.title LIKE ? COLLATE NOCASE
ORDER BY a.created_at DESC;
-- LIKE 파라미터: '%' || keyword || '%'
```

- **예상 결과 행수**: 5a: 0~1건, 5b: 0 ~ 수십 건
- **사용 인덱스**: 5a: `UNIQUE(user_id, name)`, 5b: `idx_archives_user_project` (user_id + project_id 필터링)
- **성능**: p95 < 500ms (NFR-002). 프로젝트로 범위가 좁혀지므로 전체 검색보다 빠르다.

### 6. 제목 수정 (edit)

- **사용처**: cmd_edit (FR-010~011)
- **db.py 함수**: `get_archive_title()`, `update_archive_title()`
- **쿼리**:

```sql
-- 6a. 기존 제목 조회 (응답 메시지에 old_title 필요)
SELECT title FROM archives WHERE id = ? AND user_id = ?;

-- 6b. 제목 갱신
UPDATE archives SET title = ? WHERE id = ? AND user_id = ?;
```

- **예상 결과 행수**: 6a: 0~1건, 6b: 영향 0~1건
- **사용 인덱스**: archives PK (id equality) + user_id 필터. PK 룩업 후 user_id 조건 검사.
- **성능**: p95 < 200ms (NFR-001). PK 룩업이므로 O(1).

### 7. 메세지 삭제 (remove)

- **사용처**: cmd_remove (FR-012~013)
- **db.py 함수**: `get_archive_title()`, `delete_archive()`
- **쿼리**:

```sql
-- 7a. 삭제 전 제목 조회 (응답 메시지에 title 필요)
SELECT title FROM archives WHERE id = ? AND user_id = ?;

-- 7b. 삭제
DELETE FROM archives WHERE id = ? AND user_id = ?;
```

- **예상 결과 행수**: 7a: 0~1건, 7b: 영향 0~1건
- **사용 인덱스**: archives PK (id equality) + user_id 필터
- **성능**: p95 < 200ms (NFR-001). PK 룩업이므로 O(1).

### 8. 프로젝트 목록 조회 (project list)

- **사용처**: cmd_project_list (FR-014)
- **db.py 함수**: `list_projects()`
- **쿼리**:

```sql
SELECT p.name, COUNT(a.id) AS archive_count
FROM projects p
LEFT JOIN archives a ON p.id = a.project_id AND a.user_id = ?
WHERE p.user_id = ?
GROUP BY p.id, p.name
ORDER BY p.name;
```

- **예상 결과 행수**: 0 ~ 수십 건 (단일 사용자 프로젝트 수)
- **사용 인덱스**: projects에 대해 `UNIQUE(user_id, name)` 또는 전체 스캔 (사용자별 프로젝트 수가 적으므로 문제 없음), archives에 대해 `idx_archives_user_project`
- **성능**: p95 < 200ms (NFR-001)
- **JOIN 조건 참고**: `a.user_id = ?` 조건이 JOIN절에 포함되어 있다. 이는 archives에서 해당 사용자의 데이터만 카운트하기 위함이다. user_id가 양 테이블에 비정규화되어 있으므로 동일 사용자에 대해서는 `ON p.id = a.project_id`만으로 충분하지만, 방어적 코딩으로 user_id 필터를 명시한다.

### 9. 프로젝트 이름 변경 (project rename)

- **사용처**: cmd_project_rename (FR-015)
- **db.py 함수**: `find_project()`, `rename_project()`
- **쿼리**:

```sql
-- 9a. 기존 프로젝트 존재 확인
SELECT id, name FROM projects WHERE user_id = ? AND name = ?;

-- 9b. 새 이름 중복 확인
SELECT id, name FROM projects WHERE user_id = ? AND name = ?;

-- 9c. 이름 변경
UPDATE projects SET name = ? WHERE user_id = ? AND name = ?;
```

- **예상 결과 행수**: 9a: 0~1건, 9b: 0~1건, 9c: 영향 0~1건
- **사용 인덱스**: `UNIQUE(user_id, name)` (9a, 9b, 9c 모두)
- **성능**: p95 < 200ms (NFR-001)
- **참고**: UNIQUE 제약이 9c에서도 중복을 방지하지만, 9b에서 사전 검사하여 사용자 친화적 에러 메시지를 반환한다.

### 10. 프로젝트 삭제 (project delete)

- **사용처**: cmd_project_delete (FR-016~017)
- **db.py 함수**: `delete_project()`
- **쿼리** (단일 함수 내 실행, 최종 `conn.commit()`으로 원자적 적용):

```sql
-- 10a. 프로젝트 존재 확인 및 ID 조회
SELECT id FROM projects WHERE user_id = ? AND name = ?;

-- 10b. 소속 메세지 미분류 전환
UPDATE archives SET project_id = NULL WHERE project_id = ? AND user_id = ?;
-- 영향받은 행 수(rowcount)를 응답 메시지에 사용

-- 10c. 프로젝트 삭제
DELETE FROM projects WHERE id = ? AND user_id = ?;
```

- **예상 결과 행수**: 10a: 0~1건, 10b: 영향 0~수십 건, 10c: 영향 0~1건
- **사용 인덱스**: 10a: `UNIQUE(user_id, name)`, 10b: `idx_archives_user_project`, 10c: projects PK
- **성능**: p95 < 200ms (NFR-001). 트랜잭션 내 3개 쿼리이지만 모두 인덱스 기반.
- **원자성**: 10a, 10b, 10c는 `delete_project()` 함수 내에서 실행되며, 마지막에 `conn.commit()`으로 한 번에 커밋된다. autocommit이 아닌 Python sqlite3의 기본 트랜잭션 모드 활용.

### 11. 프로젝트 존재 확인 (공용)

- **사용처**: cmd_list (FR-007), cmd_search (FR-009), cmd_project_rename (FR-015)에서 `/p` 옵션 처리 시
- **db.py 함수**: `find_project()`, `formatters.require_project()`
- **쿼리**:

```sql
SELECT id, name FROM projects WHERE user_id = ? AND name = ?;
```

- **예상 결과 행수**: 0~1건
- **사용 인덱스**: `UNIQUE(user_id, name)`
- **성능**: p95 < 200ms. 인덱스 룩업 O(log N).

---

## 제약 조건 및 검증

### 데이터베이스 레벨 제약

| 테이블 | 제약 | 종류 | 설명 |
|--------|------|------|------|
| projects | `id` | PRIMARY KEY AUTOINCREMENT | 고유 식별자 자동 생성 |
| projects | `user_id` | NOT NULL | 소유자 필수 |
| projects | `name` | NOT NULL | 프로젝트명 필수 |
| projects | `(user_id, name)` | UNIQUE | 사용자별 프로젝트명 중복 방지 |
| projects | `created_at` | NOT NULL, DEFAULT | 생성 시각 자동 기록 |
| archives | `id` | PRIMARY KEY AUTOINCREMENT | 고유 식별자 자동 생성 |
| archives | `user_id` | NOT NULL | 소유자 필수 |
| archives | `project_id` | FOREIGN KEY -> projects(id), nullable | 미분류 허용 |
| archives | `title` | NOT NULL | 제목 필수 |
| archives | `link` | NOT NULL | 링크 필수 |
| archives | `created_at` | NOT NULL, DEFAULT | 생성 시각 자동 기록 |

### 애플리케이션 레벨 검증

| 검증 항목 | 검증 위치 | 설명 |
|-----------|-----------|------|
| title 비어있지 않음 | parser.py / cmd_save.py | 빈 문자열 또는 공백만 있는 경우 거부 (FR-004) |
| link 비어있지 않음 | parser.py / cmd_save.py | URL이 추출되지 않으면 거부 (FR-004) |
| link가 URL 형식 | parser.py | `https?://\S+` 정규식 매칭. 유효성 검증은 미수행 (A-006) |
| id가 정수 | formatters.parse_archive_id() | 정수 변환 실패 시 에러 반환 (FR-010, FR-012) |
| new_title 비어있지 않음 | cmd_edit.py | 빈 문자열 거부 (FR-010) |
| keyword 비어있지 않음 | cmd_search.py | 빈 문자열 거부 (FR-008) |
| 모든 쿼리에 user_id 포함 | db.py 전체 함수 | 데이터 격리 (FR-018). `get_connection()`을 제외한 모든 함수가 user_id 파라미터를 받는다. |
| SQL 파라미터 바인딩 | db.py | SQL Injection 방지. `?` 플레이스홀더만 사용. 문자열 포매팅 금지. |

### 의도적으로 미구현한 검증

| 항목 | 이유 |
|------|------|
| title 최대 길이 | PRD에 제한 명시 없음 (A-007). SQLite TEXT는 실질적 제한 없음. |
| link URL 유효성 | Out of Scope 명시 (A-006) |
| link 중복 방지 | PRD에 요구사항 없음. 동일 링크 다른 제목 저장 허용. |
| project_name 최대 길이 | PRD에 제한 명시 없음 |

### 데이터 무결성 규칙

- **프로젝트 삭제 시 메세지 보존**: archives.project_id를 NULL로 갱신한 후 projects 레코드를 삭제한다. 순서가 중요하며 단일 `conn.commit()`으로 원자적 적용을 보장한다 (FR-016, FR-017, NFR-005).
- **프로젝트 자동 생성의 멱등성**: `INSERT OR IGNORE`를 사용하여 이미 존재하는 프로젝트에 대한 중복 INSERT를 무시한다 (FR-003).
- **존재 여부 비노출**: "찾을 수 없음"과 "권한 없음"에 동일한 에러 메시지를 반환한다 (FR-019).

---

## 확장 참고사항

### 현재 설계 처리 용량

- **단일 사용자**: 수만 건의 archives, 수십 개의 projects
- **전체**: 수백 명 사용자, 총 수만~수십만 건 archives
- SQLite WAL 모드로 10명 동시 접속 처리 (NFR-006)
- 페이지네이션 없이 약 40건까지 Slack 4,000자 메시지 제한 내 표시 가능

### 10배 규모 (사용자 100명+, 레코드 10만 건+)

| 변경 필요 영역 | 대응 방안 |
|----------------|-----------|
| 검색 성능 | `LIKE '%keyword%'` -> SQLite FTS5 전환. `CREATE VIRTUAL TABLE archives_fts USING fts5(title, content=archives, content_rowid=id)`. FTS5 가용성이 Python 빌드에 따라 다를 수 있으므로 런타임 체크 필요. |
| 목록 조회 | 페이지네이션 도입 (LIMIT/OFFSET 또는 커서 기반). Slack 메시지 길이 제한(4,000자)이 자연스러운 페이지 크기를 결정한다. |
| HTTP 서버 | `http.server`에 `ThreadingMixIn` 추가 또는 asyncio 기반 서버 전환 |
| 인덱스 | `idx_archives_title`의 효용성 재평가. covering index 전략 재검토. |

### 100배 규모 (사용자 1,000명+, 레코드 100만 건+)

| 변경 필요 영역 | 대응 방안 |
|----------------|-----------|
| 데이터베이스 | SQLite -> PostgreSQL 전환. 현재 SQL이 표준에 가까워 이식 비용 낮음. `datetime('now')` -> `NOW()`, `INSERT OR IGNORE` -> `INSERT ON CONFLICT DO NOTHING`, `PRAGMA` -> PostgreSQL 설정으로 변경. |
| 스키마 변경 | user_id에 별도 users 테이블 도입. user_id 컬럼에 FK 추가. 인덱스 전략 재설계 (partial index 등 PostgreSQL 기능 활용). |
| 검색 | PostgreSQL `pg_trgm` + GIN 인덱스 또는 별도 검색 엔진 |
| 배포 | 단일 프로세스 -> 다중 인스턴스 + 공유 DB. 연결 풀링 필요. |
| 마이그레이션 | PRAGMA user_version -> Alembic 등 전문 마이그레이션 도구 전환 |

현재 v0에서는 이러한 확장을 구현하지 않는다. 위 내용은 향후 판단을 위한 참고 사항이다.

---

## 설계 결정 기록

### D-001: user_id TEXT vs. 별도 users 테이블

- **결정**: user_id를 TEXT로 직접 저장, 별도 users 테이블 없음.
- **근거**: Slack user ID는 외부 시스템(Slack)이 관리하는 식별자이다. 사용자 정보(이름, 이메일 등)를 저장하지 않으므로 별도 테이블의 가치가 없다. 단순한 문자열 필터로 충분하다.
- **재검토 시점**: 사용자 프로필/설정을 저장해야 할 때.

### D-002: created_at TEXT vs. INTEGER (Unix timestamp)

- **결정**: TEXT 타입으로 `datetime('now')` 기본값 사용. ISO 8601 형식.
- **근거**: 사람이 읽을 수 있는 형식 (디버깅 용이). SQLite의 날짜/시간 함수와 호환. 정렬은 TEXT 기반 사전순 비교로도 정확하게 동작한다 (ISO 8601의 장점).
- **트레이드오프**: INTEGER (Unix timestamp)가 저장 효율과 비교 성능에서 약간 우수하지만, 현재 규모에서는 무의미한 차이이다.

### D-003: ON DELETE CASCADE 미사용

- **결정**: FK에 ON DELETE CASCADE를 설정하지 않고, 애플리케이션 코드에서 project_id를 NULL로 갱신한 후 프로젝트를 삭제한다.
- **근거**: FR-017 요구사항. 프로젝트 삭제 시 메세지를 함께 삭제하지 않고 미분류로 전환해야 한다. CASCADE는 메세지까지 삭제하므로 부적합하다. ON DELETE SET NULL이 가능하지만, SQLite에서 외래 키 동작의 디버깅이 어렵고, 영향받은 행 수(rowcount)를 응답에 표시해야 하므로 명시적 UPDATE가 더 적합하다.

### D-004: AUTOINCREMENT 사용

- **결정**: 양 테이블 모두 `INTEGER PRIMARY KEY AUTOINCREMENT` 사용.
- **근거**: AUTOINCREMENT 없이 `INTEGER PRIMARY KEY`만 사용하면 SQLite는 삭제된 ID를 재사용할 수 있다. 사용자에게 노출되는 ID가 재사용되면 혼란을 야기할 수 있다 ("ID: 5를 삭제했는데 새로운 ID: 5가 생겼다"). AUTOINCREMENT는 항상 증가하는 값을 보장한다. 성능 오버헤드는 무시 가능 수준이다.
