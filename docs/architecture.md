# Architecture

## Overview

OpenClaw Archiver Plugin is a **Python monolith** that runs as a single process, either embedded in the OpenClaw framework or as a standalone HTTP bridge server. It provides per-user Slack message link archiving with project-based classification.

**Architecture style**: Modular monolith (single package, module-per-command)

**Justification**: This is a single-purpose Slack plugin with no inter-service communication needs, a single data store (SQLite), and a small surface area (9 commands). A monolith is the only defensible choice. There is nothing here that benefits from service decomposition.

**Key constraints driving the design**:

- Zero runtime dependencies (stdlib only) -- NFR-003
- Must run in two modes: embedded plugin and HTTP bridge -- FR-022, FR-023
- SQLite as the sole data store (WAL mode for concurrency) -- NFR-006
- Deterministic command parsing, no LLM involvement -- NFR-004
- All output formatted as Slack mrkdwn, no code blocks -- NFR-008

---

## Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| Language | Python 3.11+ | Target runtime; required by OpenClaw framework (NFR-007) |
| Runtime dependencies | None (stdlib only) | NFR-003: zero external deps |
| Database | SQLite 3 (WAL mode) | Bundled with Python stdlib; sufficient for single-node, file-based persistence |
| HTTP server | `http.server` (stdlib) | No framework needed for 2 endpoints |
| Build system | hatchling | Lightweight, supports entry points and src layout |
| Package manager | uv | Team standard per claude.md |
| Test framework | pytest + pytest-cov | Team standard |
| Linting | ruff + black | Team standard |

Version pinning is handled via `pyproject.toml` with `requires-python = ">=3.11"` and dev dependency minimum versions. No lock file for runtime deps since there are none.

---

## System Diagram

```
                        Slack Workspace
                              |
                     OpenClaw Framework
                       /             \
              (Python mode)      (JS/TS mode)
                  |                   |
          entry point            HTTP POST
          handle_message()      /message
                  \                 /
                   \               /
                plugin.py (prefix guard)
                       |
                dispatcher.py (route)
                   /   |   \
            cmd_*.py modules
                   \   |   /
               formatters.py (mrkdwn output)
                       |
                    db.py (SQLite ops)
                       |
                  SQLite WAL file
```

---

## Data Flow

Every user interaction follows the same linear pipeline:

```
1. Input arrives     -> plugin.handle_message(message, user_id)
                        or server._Handler.do_POST() -> handle_message()
2. Prefix guard      -> plugin.py checks "/archive" prefix, rejects non-matching
3. Dispatch          -> dispatcher.py splits subcommand, routes to cmd_*.handle()
4. Parse             -> parser.py extracts /p option, URL, title from args
5. Database          -> db.py executes parameterized SQL against SQLite
6. Format response   -> formatters.py + cmd_*.py build Slack mrkdwn string
7. Return            -> string bubbles back up to caller (plugin or HTTP JSON)
```

There are no async operations, no queues, no background work. Every request is synchronous and completes within a single function call stack. SQLite connections are created per-request inside each `cmd_*.handle()` function via `db.get_connection()`.

---

## Modules

### Module: plugin

- **Responsibility**: Entry point guard -- accepts messages starting with `/archive`, rejects everything else
- **Dependencies**: dispatcher
- **Key interfaces**: `handle_message(message: str, user_id: str) -> str | None`
- **Notes**: Returns `None` for non-matching messages (OpenClaw convention for "not my command"). Rejects prefix-collisions like `/archivesave` by checking for whitespace or end-of-string after `/archive`.

### Module: server

- **Responsibility**: HTTP bridge for JS/TS OpenClaw -- exposes `POST /message` and `GET /health`
- **Dependencies**: plugin
- **Key interfaces**: `run()` starts the HTTP server; `POST /message` accepts JSON `{message, user_id}`, returns JSON `{ok, response}`
- **Notes**: Binds to `127.0.0.1` only (security). Uses stdlib `http.server`. Body size capped at 1 MiB. Port configurable via `OPENCLAW_ARCHIVER_PORT` (default 8201).

### Module: dispatcher

- **Responsibility**: Route subcommands to handler modules using a static dispatch table
- **Dependencies**: all cmd_* modules
- **Key interfaces**: `dispatch(message: str, user_id: str) -> str`
- **Notes**: Two-level routing for `project` subcommands (`project list`, `project rename`, `project delete`). Unknown commands return a fixed error string. No dynamic loading or plugin discovery.

### Module: parser

- **Responsibility**: Deterministic extraction of URL, `/p <project>` option, and title from command arguments
- **Dependencies**: none (stdlib `re` only)
- **Key interfaces**: `extract_project_option(text)`, `extract_url(text)`, `parse_save(args)`
- **Parsing strategy** (R-002 mitigation):
  1. Extract `/p <project>` from end of string only (avoids false positives with titles containing "/p")
  2. Extract URL via `https?://\S+` regex, stripping Slack angle brackets
  3. Remaining text becomes the title
  4. This order ensures titles with spaces are handled safely

### Module: formatters

- **Responsibility**: Centralized output formatting -- Slack mrkdwn helpers shared across all command handlers
- **Dependencies**: db (lazy import for `require_project`)
- **Key interfaces**:
  - `SEPARATOR` -- Unicode horizontal line `"─────────────────────────────"` used as visual divider between header and body
  - `format_archive_rows(rows, include_project=True)` -- converts DB result tuples into mrkdwn-formatted display lines
  - `format_date(created_at)` -- extracts `YYYY-MM-DD` from ISO timestamp
  - `parse_archive_id(raw, command)` -- validates and converts string to int ID
  - `require_project(conn, user_id, project_name)` -- looks up project or returns error string
- **NFR-008 role**: This is the central formatting layer. See dedicated section below.

### Module: db

- **Responsibility**: All SQLite operations -- connection management, CRUD queries
- **Dependencies**: migrations, schema_v1
- **Key interfaces**: `get_connection()`, `insert_archive()`, `list_archives()`, `search_archives()`, `update_archive_title()`, `delete_archive()`, `list_projects()`, `rename_project()`, `delete_project()`, `get_or_create_project()`, `find_project()`, `get_archive_title()`
- **Notes**: Every query that touches user data includes `WHERE user_id = ?` for data isolation (FR-018). Connection is created per-request via `get_connection()`. WAL mode and foreign keys enabled on every connection. Migrations run on every connection open (idempotent).

### Module: schema_v1

- **Responsibility**: DDL definition for schema version 1
- **Dependencies**: none
- **Key interfaces**: `SCHEMA_SQL` string constant

### Module: migrations

- **Responsibility**: Apply pending schema migrations using `PRAGMA user_version`
- **Dependencies**: schema_v1
- **Key interfaces**: `run_migrations(conn)`
- **Notes**: Runs on every `get_connection()` call. Idempotent via `CREATE TABLE IF NOT EXISTS` and version check. Defines both `up` and `down` SQL per version (down is manual-only).

### Module: cmd_save

- **Responsibility**: Handle `/archive save <title> <link> [/p <project>]`
- **Dependencies**: parser, db, formatters
- **FR mapping**: FR-001 through FR-005

### Module: cmd_list

- **Responsibility**: Handle `/archive list [/p <project>]`
- **Dependencies**: parser, db, formatters
- **FR mapping**: FR-006, FR-007, FR-027

### Module: cmd_search

- **Responsibility**: Handle `/archive search <keyword> [/p <project>]`
- **Dependencies**: parser, db, formatters
- **FR mapping**: FR-008, FR-009, FR-028

### Module: cmd_edit

- **Responsibility**: Handle `/archive edit <id> <new_title>`
- **Dependencies**: db, formatters
- **FR mapping**: FR-010, FR-011, FR-029

### Module: cmd_remove

- **Responsibility**: Handle `/archive remove <id>`
- **Dependencies**: db, formatters
- **FR mapping**: FR-012, FR-013, FR-029

### Module: cmd_project_list

- **Responsibility**: Handle `/archive project list`
- **Dependencies**: db, formatters
- **FR mapping**: FR-014, FR-029

### Module: cmd_project_rename

- **Responsibility**: Handle `/archive project rename <old> <new>`
- **Dependencies**: db, formatters
- **FR mapping**: FR-015, FR-029

### Module: cmd_project_delete

- **Responsibility**: Handle `/archive project delete <name>`
- **Dependencies**: db, formatters
- **FR mapping**: FR-016, FR-017, FR-029

### Module: cmd_help

- **Responsibility**: Return static help text formatted as Slack mrkdwn
- **Dependencies**: none
- **FR mapping**: FR-030

---

## Data Model

### Entity Relationship

```
projects 1──────0..N archives
   |                    |
   user_id              user_id (denormalized)
   name (unique/user)   project_id (nullable FK)
                        title
                        link
                        created_at
```

A user has many projects. A project has many archives. An archive may belong to zero or one project (`NULL` = unclassified). When a project is deleted, its archives are set to `project_id = NULL` (not cascade-deleted), preserving the data (FR-017).

`user_id` is denormalized on both tables. This enables simple `WHERE user_id = ?` on every query without requiring joins for isolation checks.

### Tables

**projects**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | TEXT NOT NULL | Slack user ID |
| name | TEXT NOT NULL | Project display name |
| created_at | TEXT NOT NULL | DEFAULT datetime('now') |
| | | UNIQUE(user_id, name) |

**archives**

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | TEXT NOT NULL | Slack user ID |
| project_id | INTEGER | NULLABLE FK -> projects(id) |
| title | TEXT NOT NULL | User-provided description |
| link | TEXT NOT NULL | Slack message URL |
| created_at | TEXT NOT NULL | DEFAULT datetime('now') |

### Indexes

| Index | Columns | Purpose |
|---|---|---|
| idx_archives_user | (user_id) | Fast per-user listing |
| idx_archives_user_project | (user_id, project_id) | Fast project-filtered listing |
| idx_archives_title | (user_id, title) | Supports title search (note: LIKE with leading wildcard cannot use B-tree efficiently) |
| UNIQUE(user_id, name) | projects | Prevent duplicate project names per user |

### Storage

- Single SQLite file at `~/.openclaw/workspace/.archiver/archiver.sqlite3` (configurable via `OPENCLAW_ARCHIVER_DB_PATH`)
- WAL journal mode for concurrent reader/writer access
- Foreign keys enforced via `PRAGMA foreign_keys=ON`

### Migration Strategy

- Version tracked via `PRAGMA user_version`
- Migrations defined in `migrations.py` as a dict of `{version: {up: SQL, down: SQL}}`
- `run_migrations()` is called on every connection open -- idempotent
- Currently at version 1 (initial schema)
- Rollback: `down` SQL is defined but not exposed via any command; manual rollback only

---

## API Design

### Plugin Interface (Python OpenClaw)

The plugin exposes a single function registered via entry point:

```python
def handle_message(message: str, user_id: str) -> str | None
```

- **Input**: Full message text (e.g. `/archive save ...`), Slack user ID
- **Output**: Response string (Slack mrkdwn) if handled, `None` if message is not for this plugin
- **Registration**: `[project.entry-points."openclaw.plugins"] archiver = "openclaw_archiver.plugin:handle_message"`

### HTTP Bridge API (JS/TS OpenClaw)

Base URL: `http://127.0.0.1:{port}` (default port 8201)

#### GET /health

Health check endpoint.

**Response** (200):
```json
{"ok": true, "plugin": "archiver", "version": "0.1.0"}
```

#### POST /message

Process a command message.

**Request**:
```json
{
  "message": "/archive save 회의록 https://slack.com/archives/C01/p123",
  "user_id": "U01234567"
}
```

**Response** (200):
```json
{
  "ok": true,
  "response": "저장했습니다. (ID: 7)\n*제목:* 회의록"
}
```

**Error responses**:

| Status | Condition | Body |
|---|---|---|
| 400 | Missing message or user_id | `{"ok": false, "error": "message and user_id are required"}` |
| 400 | Invalid JSON | `{"ok": false, "error": "invalid JSON body"}` |
| 400 | Invalid Content-Length | `{"ok": false, "error": "invalid Content-Length"}` |
| 413 | Body > 1 MiB | `{"ok": false, "error": "body too large (max 1048576 bytes)"}` |
| 404 | Unknown path | `{"ok": false, "error": "not found"}` |
| 500 | Unhandled exception | `{"ok": false, "error": "internal server error"}` |

**Authentication**: None. The HTTP bridge trusts `user_id` from the request body. Security relies on localhost-only binding (see Security section).

**Rate limiting**: None implemented. SQLite serialization provides natural backpressure.

**Pagination**: Not implemented (out of scope per PRD). Large result sets may hit Slack's 4,000 character message limit.

### Command Handler Interface (Internal)

Each `cmd_*.py` module exports:

```python
def handle(args: str, user_id: str) -> str
```

- **args**: Everything after the subcommand (e.g. for `/archive save foo bar`, args is `"foo bar"`)
- **user_id**: Slack user ID
- **Returns**: Always a string (never None). Formatted as Slack mrkdwn per NFR-008.

---

## NFR-008: Formatting Layer Design

### Problem

The original implementation used 8-space indentation for visual formatting. Slack renders lines starting with 4+ spaces as preformatted text (monospace, no link rendering). This broke clickable links and produced inconsistent visual output across Slack clients.

### Solution: Centralized mrkdwn Formatting

The formatting system operates at two layers:

**Layer 1 -- formatters.py (shared formatting)**

`formatters.py` is the single point of control for list/search output. All `cmd_list.py` and `cmd_search.py` output goes through `format_archive_rows()`.

- `SEPARATOR`: Unicode horizontal line `───` (U+2500 characters) for visual dividers between headers and content
- `format_archive_rows(rows, include_project=True)`: Produces mrkdwn lines per archive item:
  - Line 1: `#{id} {title}` -- no indentation, ID prefix for identification
  - Line 2: `<{link}|링크> | {project_or_미분류} | {date}` -- Slack clickable link format
  - Items separated by blank lines for visual breathing room
  - When `include_project=False` (project-filtered view), project name is omitted from each item since the header already shows it
- `format_date()`: Extracts `YYYY-MM-DD` from ISO timestamp (unchanged)

**Layer 2 -- cmd_*.py (per-command response strings)**

Each command handler builds its response using Slack mrkdwn directly:
- Success messages use `*label:*` bold for labels (e.g. `*제목:*`, `*프로젝트:*`, `*변경:*`)
- User-supplied text (titles, project names) is NOT wrapped in bold to avoid breakage from `*` in user input (R-008)
- List/search headers use bold: `*저장된 메세지* (3건)`, `*검색 결과: "keyword"* (2건)`
- Change indicators use arrow: `*변경:* old → new`

### Formatting Rules (enforced by CI tests)

| Rule | Regex validation | Expected matches |
|---|---|---|
| No 4+ space indentation | `^ {4,}` per line | 0 |
| No backticks | `` ` `` in output | 0 |
| No bare URLs (in link-containing responses) | `(?<![\|<])https?://\S+(?![\|>])` | 0 |
| Slack link format present | `<https?://[^\|]+\|[^>]+>` | 1+ per link response |

### Design Decision: Labels-only Bold

Bold (`*text*`) is applied only to controlled labels, never to user-supplied text. This prevents rendering breakage when user input contains `*` characters. Example:

- Correct: `*제목:* 스프린트 회의록`
- Incorrect: `제목: *스프린트 회의록*` -- would break if title contains `*`

### Allowed mrkdwn Elements

| Element | Syntax | Usage |
|---|---|---|
| Bold | `*text*` | Labels, headers, command names |
| Link | `<url\|text>` | Archived message links |
| Line break | `\n` | Between items, between sections |
| Separator | `───` (U+2500) | Between header and body |
| Arrow | `→` (U+2192) | Before/after in rename/edit |
| Plain text | (no formatting) | Descriptions, user input, metadata |

---

## Background Jobs

None. This system has no background processing, scheduled tasks, or async work. Every operation is a synchronous request-response within a single function call.

---

## Observability

### Logging

- **Framework**: Python stdlib `logging`
- **Levels used**:
  - `logger.exception()`: Unhandled errors in HTTP handler
  - `logger.error()`: Configuration errors (invalid port, bind failure)
  - `logger.info()`: Server startup with host/port
- **HTTP access logging**: Suppressed (overridden `log_message` to no-op) to avoid noise
- **Command handlers**: No logging. Failures communicated via error response strings to the user.

### Metrics

No metrics collection is implemented. For a single-process SQLite plugin, the relevant signals are:
- Process uptime (monitored by systemd)
- SQLite file size (monitored by OS)
- Response time (observable from OpenClaw framework logs)

### Alerting

Not applicable for a plugin. The host framework (OpenClaw) and process supervisor (systemd) handle availability monitoring.

---

## Security

### Data Isolation (FR-018, FR-019)

Every SQL query that reads, updates, or deletes data includes `WHERE user_id = ?`. There is no admin endpoint, no bulk query, and no path that accesses data without a user_id filter.

When a user attempts to access another user's data (edit, remove, project operations), the system returns the same error message as "not found" -- preventing enumeration of other users' data (FR-019).

### HTTP Bridge Security

- **Localhost binding**: The server binds to `127.0.0.1` only, not `0.0.0.0`. External network access is blocked at the transport level.
- **No authentication**: The bridge trusts `user_id` from the request body. This is acceptable because the only caller is the OpenClaw framework running on the same machine (A-001).
- **Body size limit**: 1 MiB maximum request body prevents memory exhaustion.
- **Risk (R-005)**: Any process on the same machine can forge requests with arbitrary `user_id`. Mitigation: localhost-only deployment where the OpenClaw framework is the sole consumer.

### Input Validation

- **SQL injection**: All queries use parameterized statements (`?` placeholders). No string interpolation in SQL.
- **Title/link content**: No length or content validation. SQLite TEXT has no practical size limit. User-supplied text stored and displayed as-is (A-007).
- **URL validation**: Not performed (out of scope per PRD). Any string matching `https?://\S+` is accepted as a link.
- **Command parsing**: Deterministic regex-based parsing. No `eval()`, no dynamic code execution.
- **ID validation**: `parse_archive_id()` converts to int; non-numeric values return error message.

### Secrets Management

No secrets. The plugin has no API keys, no tokens, no credentials. Authentication is delegated entirely to the OpenClaw framework and Slack.

### OWASP Top 10 Mitigations

| Risk | Mitigation |
|---|---|
| A01 Broken Access Control | user_id filter on every query; same error for not-found and not-authorized |
| A03 Injection | Parameterized SQL only; no shell commands |
| A05 Security Misconfiguration | Localhost-only HTTP binding; WAL mode for data integrity |
| A06 Vulnerable Components | Zero runtime dependencies eliminates supply chain attack surface |
| A07 Auth Failures | Delegated to Slack/OpenClaw framework |
| A08 Data Integrity | Foreign keys enforced; transactional project deletion |
| A09 Logging Failures | Error logging in HTTP handler; no sensitive data in logs |

---

## Deployment and Rollback

### Deployment Target

Two deployment modes, no containers required:

**Mode 1: Python plugin (embedded)**
- Installed via `pip install` / `uv add` into the OpenClaw Python environment
- Discovered via `openclaw.plugins` entry point
- No separate process to manage

**Mode 2: HTTP bridge (standalone process)**
- Run via `openclaw-archiver-server` script
- Managed by systemd (or equivalent process supervisor)
- Binds to `127.0.0.1:8201` (configurable via `OPENCLAW_ARCHIVER_PORT`)

### CI/CD Pipeline

```
push/PR -> ruff check -> black --check -> pytest --cov -> build -> publish
```

1. `uv sync` -- install dev dependencies
2. `uv run ruff check .` -- lint
3. `uv run black --check .` -- format check
4. `uv run pytest -q --cov=src` -- test with coverage (Python 3.11, 3.12, 3.13 matrix per NFR-007)
5. Build: `uv build`
6. Deploy: install wheel on target, restart systemd service

### Rollback Procedure

- **Code rollback**: Install previous wheel version. Restart process. Simple and sufficient for this scale.
- **Database rollback**: Migration `down` SQL is defined but requires manual execution via `sqlite3` CLI. Schema v1 is the initial version, so rollback means dropping all tables (data loss). Back up the SQLite file before deploying.
- **Strategy**: "Deploy the previous version." Blue-green or canary deployments are not warranted for a single-process SQLite plugin.

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `OPENCLAW_ARCHIVER_PORT` | HTTP bridge server port | `8201` |
| `OPENCLAW_ARCHIVER_DB_PATH` | SQLite file path | `~/.openclaw/workspace/.archiver/archiver.sqlite3` |

---

## Tradeoffs

| Decision | Chosen | Rejected | Rationale |
|---|---|---|---|
| Architecture | Monolith (single package) | Microservices, serverless | Single data store, single surface, 9 commands. No benefit from decomposition. |
| Database | SQLite with WAL | PostgreSQL, MySQL | Zero-dep requirement (NFR-003). Bundled with Python. WAL handles team-scale concurrency. |
| HTTP framework | stdlib http.server | Flask, FastAPI | Zero-dep requirement. Only 2 endpoints. |
| Connection management | Per-request creation | Connection pool | SQLite file connections are cheap to open. Pool adds complexity for no measurable gain. |
| Search | LIKE with leading wildcard | SQLite FTS5 | Simpler; meets 500ms target for 10k records. FTS5 availability varies by Python build. Upgrade path exists. |
| Formatting centralization | formatters.py shared layer | Per-command formatting | Single change point for NFR-008 rules. Reduces duplication across cmd_list, cmd_search, and future list-like commands. |
| Bold scope | Labels only (`*label:*`) | Also bold user input | User text may contain `*`, breaking mrkdwn rendering (R-008). Labels are controlled text, safe to bold. |
| HTTP auth | None (localhost only) | Shared secret, JWT | Bridge serves only localhost. Auth adds secret distribution overhead with no real security gain on single machine. |
| Pagination | Not implemented | Cursor/offset | PRD excludes it. Slack 4,000 char limit is the natural boundary (~40 items). Search and /p narrow results. |
| user_id denormalization | user_id on both tables | Only on projects | Enables simple WHERE on every query without joins. Slightly more storage, much simpler security model. |
| Migration tool | PRAGMA user_version | Alembic | Zero-dep requirement. 2-table schema does not warrant a migration framework. |
| `/p` option parsing | End-of-string only | Anywhere in string | Eliminates ambiguity when title contains "/p" (R-001). |
| Error message uniformity | Same message for not-found and not-authorized | Distinct messages | FR-019: prevents data existence enumeration. Trades debugging convenience for security. |

### What Changes at 10x Scale

If usage grows significantly (thousands of users, hundreds of thousands of archives):

1. **SQLite becomes a bottleneck**: WAL helps but SQLite is single-writer. Migrate to PostgreSQL. The SQL is standard and ports with minimal changes.
2. **LIKE search becomes slow**: At 100k+ records, leading-wildcard LIKE scans all rows. Introduce FTS5 or migrate to PostgreSQL with `pg_trgm`.
3. **HTTP bridge needs concurrency**: stdlib `http.server` is single-threaded. Add `ThreadingMixIn` or replace with a WSGI server. Handler code is already stateless.
4. **Pagination becomes necessary**: At 40+ items per user, responses hit Slack's message limit. Add cursor-based pagination.
5. **Connection pooling**: Becomes worthwhile with PostgreSQL. SQLite file connections remain cheap.
