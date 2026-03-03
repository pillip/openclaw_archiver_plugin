# Review Notes -- ISSUE-001 Scaffolding PR

**Reviewer:** Senior Code Review Agent
**Date:** 2026-03-03
**Branch:** `issue/ISSUE-001-scaffolding`
**Files changed:** 9 (499 insertions)

---

## Code Review

### Blocking Issues

1. **No test files existed (FIXED)**

   The `tests/` directory contained only `__init__.py` (empty) and `conftest.py` (docstring only). Running `uv run pytest` returned exit code 5 (no tests collected). For a scaffolding PR, at minimum a smoke test should verify that the package is importable and entry points are wired correctly.

   **Fix applied:** Added `tests/test_smoke.py` with 4 tests:
   - `test_version_is_string` -- verifies `__version__` is a string
   - `test_handle_message_returns_none_for_empty_input` -- edge case: empty string input
   - `test_handle_message_returns_none_for_arbitrary_input` -- stub returns `None`
   - `test_run_is_callable` -- verifies `run` function exists and is callable

### Suggestions (non-blocking)

2. **Version duplication between `pyproject.toml` and `__init__.py`**

   `pyproject.toml` declares `version = "0.1.0"` and `src/openclaw_archiver/__init__.py` declares `__version__ = "0.1.0"`. These two values can drift over time. Consider using hatchling's dynamic versioning (`dynamic = ["version"]` with `[tool.hatch.version]`) to derive `__version__` from `pyproject.toml`, or vice versa.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/pyproject.toml` (line 3)
   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/__init__.py` (line 3)

3. **`server.py:run()` has no explicit body statement**

   The function body is just a docstring. While valid Python, this is inconsistent with `plugin.py` which has an explicit `return None`. Adding a `pass` or a placeholder comment (e.g., `# TODO: implement HTTP bridge`) would make the intent clearer.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/server.py` (lines 4-5)

4. **Entry points are correctly configured**

   - `[project.entry-points."openclaw.plugins"]` points to `openclaw_archiver.plugin:handle_message` -- matches spec.
   - `[project.scripts]` defines `openclaw-archiver-server = "openclaw_archiver.server:run"` -- matches spec.

5. **`pyproject.toml` configuration is well-structured**

   - `requires-python = ">=3.11"` aligns with team ground rules.
   - `dependencies = []` matches NFR "zero runtime dependencies."
   - `[tool.pytest.ini_options]` has correct `testpaths`, `minversion`, and `addopts`.
   - Build system uses hatchling, which is appropriate for a src-layout project.

6. **`__main__.py` is correctly wired**

   Imports `run` from `server` and guards with `if __name__ == "__main__"`. The additional `main()` wrapper function is a clean pattern for testability.

### Follow-up Issues

- **ISSUE-FOLLOW-001:** Consolidate version string to a single source of truth (hatchling dynamic version or importlib.metadata).
- **ISSUE-FOLLOW-002:** Add `conftest.py` fixtures for common test setup (e.g., temporary SQLite DB path) once `db.py` is implemented.

---

## Security Findings

### Summary

No security issues found. This is expected for a scaffolding PR with zero runtime dependencies and stub-only code.

### Detailed Assessment

| # | Severity | Category | Finding | Status |
|---|----------|----------|---------|--------|
| S-1 | **Low** | Sensitive data | `.gitignore` correctly covers `.env`, `.env.local`, `*.sqlite3`, `*.sqlite3-wal`, `*.sqlite3-shm`. No secrets in any committed file. | Pass |
| S-2 | **Low** | Dependencies | Zero runtime dependencies. Dev dependencies (`pytest>=7.0`, `pytest-cov>=4.0`, `ruff>=0.4.0`, `black>=24.0`) are well-known, actively maintained packages with no known CVEs at these version floors. | Pass |
| S-3 | **Low** | Misconfiguration | No debug flags, no permissive CORS, no hardcoded ports. Environment variables for configuration are documented in the PRD but not yet implemented (correct for scaffolding). | Pass |
| S-4 | **Info** | Input validation | `handle_message()` currently returns `None` unconditionally. When command parsing is implemented, input validation and SQL parameterization will need review. This is out of scope for this PR. | N/A |

### Notes for Future PRs

- When `db.py` is added: verify all SQL uses parameterized queries (not string formatting). The PRD mentions SQLite with user-provided input (title, project name, search keyword) -- these are injection vectors.
- When `server.py` HTTP bridge is implemented: review for CORS configuration, request size limits, and authentication.
- Ensure `OPENCLAW_ARCHIVER_DB_PATH` default (`~/.openclaw/workspace/.archiver/archiver.sqlite3`) does not create world-readable files. Verify umask or explicit `os.chmod` on DB creation.

---

## Verdict

**Approve with fixes applied.** The one blocking issue (missing smoke tests) has been resolved. The scaffolding correctly matches the architecture spec. Two non-blocking suggestions are noted for follow-up.

---
---

# Review Notes -- ISSUE-002 Schema Migration PR

**Reviewer:** Senior Code Review Agent
**Date:** 2026-03-03
**Branch:** `issue/ISSUE-002-schema-migration`
**Files changed:** 3 (215 insertions)

---

## Code Review

### Spec Compliance

**DDL vs data_model.md**: Verified line-by-line. The DDL in `schema_v1.py` matches the spec in `docs/data_model.md` exactly:
- `projects` table: `id`, `user_id`, `name`, `created_at` with correct types, constraints, and `UNIQUE(user_id, name)`.
- `archives` table: `id`, `user_id`, `project_id` (nullable FK), `title`, `link`, `created_at` with correct types and constraints.
- 3 indexes: `idx_archives_user`, `idx_archives_user_project`, `idx_archives_title` with correct column compositions.
- `PRAGMA user_version = 1` as final statement.

**File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/schema_v1.py`

**Architecture compliance**: `schema_v1` exports `SCHEMA_SQL: str` constant; `migrations` exports `run_migrations(conn)` function with `user_version` tracking. Both match `docs/architecture.md` module specifications.

**File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/migrations.py`

### Blocking Issues

None. All 19 tests pass. Code is correct and matches spec.

### Suggestions (non-blocking)

1. **`executescript` does not provide true transactional atomicity for migrations**

   The docstring on `run_migrations` states "Each migration runs via executescript which handles its own transaction management." However, `executescript` issues an implicit COMMIT of any pending transaction *before* execution, then runs each SQL statement individually. If the script fails mid-way (e.g., after CREATE TABLE but before PRAGMA user_version), the DB is left in a partially-migrated state with no automatic rollback.

   For version 1 this is a **non-issue in practice** because all DDL uses `IF NOT EXISTS`, making reruns safe -- the idempotency test confirms this. However, future migrations using `ALTER TABLE` will not be idempotent, and a partial failure would leave the schema in an inconsistent state that cannot be recovered by rerunning.

   **Recommendation:** When adding migration v2+, wrap each migration in an explicit `BEGIN`/`COMMIT` pair and use `conn.execute()` instead of `conn.executescript()`, or add try/except with rollback logic. Document this limitation in a code comment for now.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/migrations.py` (line 39)

2. **`down` migrations are defined but not callable**

   The `MIGRATIONS` dict includes `"down"` DDL for each version, but there is no `rollback_migration()` or `migrate_down()` function exposed. The `data_model.md` spec describes rollback as a supported strategy. This is acceptable for v1 (manual rollback via DB file restore is the primary strategy per spec), but a follow-up should add the function before v2 ships.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/migrations.py` (lines 12-16)

3. **Missing edge-case tests**

   The test suite is solid for the happy path and core constraints. The following edge cases are not covered:

   - **NOT NULL violation**: Inserting a row with `NULL` for `user_id`, `title`, or `link` should raise `IntegrityError`. Currently only the UNIQUE and FK constraints are tested.
   - **`created_at` default population**: No test verifies that `created_at` is automatically populated by the `DEFAULT (datetime('now'))` expression when omitted from INSERT.
   - **Down migration**: The `"down"` DDL in `MIGRATIONS[1]` is never executed in any test. A test should verify that running the down script drops both tables and resets `user_version` to 0.
   - **Missing migration key**: If `MIGRATIONS` had a gap (e.g., keys 1 and 3 but not 2), `run_migrations` would raise `KeyError`. While not a current problem, a defensive check or test would be good.

   These are non-blocking for this PR but should be addressed before the migration engine is used for v2+.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_schema_migration.py`

4. **Fixture yields but does not need to be a generator**

   The `db` fixture uses `yield conn` followed by `conn.close()`. This is correct and properly handles teardown. No change needed -- just noting it is well-written.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_schema_migration.py` (lines 17-22)

5. **Test imports private function `_get_user_version`**

   Tests import `_get_user_version` (underscore-prefixed, indicating private). This is acceptable for unit testing internal behavior, but if the function is needed externally (e.g., by `db.py` for diagnostics), consider removing the underscore prefix.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_schema_migration.py` (line 10)

### Follow-up Issues

- **ISSUE-FOLLOW-003:** Add `rollback_migration()` function to `migrations.py` before migration v2 is introduced.
- **ISSUE-FOLLOW-004:** Replace `executescript` with explicit transaction management (`BEGIN`/`COMMIT`/`ROLLBACK`) for non-idempotent future migrations.
- **ISSUE-FOLLOW-005:** Add edge-case tests for NOT NULL violations, `created_at` default, down migration execution, and missing migration key defense.

---

## Security Findings

### Summary

No Critical or High severity issues found. The schema and migration code follows secure practices.

### Detailed Assessment

| # | Severity | Category | Finding | Status |
|---|----------|----------|---------|--------|
| S-1 | **Pass** | SQL Injection | All SQL in `schema_v1.py` is static DDL with no user input interpolation. All SQL in test code uses parameterized queries (`?` placeholders). No string formatting anywhere. | Pass |
| S-2 | **Pass** | Constraints | All NOT NULL, UNIQUE, and FOREIGN KEY constraints from `data_model.md` are present. `FOREIGN KEY (project_id) REFERENCES projects(id)` is correctly defined. Test fixture enables `PRAGMA foreign_keys = ON` and the FK violation test confirms enforcement. | Pass |
| S-3 | **Pass** | Sensitive data | No hardcoded secrets, API keys, credentials, or file paths. DB path is not referenced in these modules (will be in `db.py`). | Pass |
| S-4 | **Low** | Misconfiguration | `executescript` issues an implicit COMMIT, which means `foreign_keys` PRAGMA could theoretically be affected. However, `foreign_keys` is a connection-level setting that persists across `executescript` calls in CPython's sqlite3 module. The FK violation test at line 142-149 confirms this. No action needed. | Pass |
| S-5 | **Low** | Input validation | `run_migrations` does not validate that `conn` is a valid open connection before operating. A closed or `None` connection would raise an `AttributeError` or `ProgrammingError`. This is acceptable -- the caller (`db.py`, not yet implemented) is responsible for providing a valid connection. | Pass |

### Notes for Future PRs

- When `db.py` is implemented, ensure that `PRAGMA foreign_keys = ON` is set on every new connection *before* calling `run_migrations()`. The migration script itself does not enable foreign keys -- this is by design (connection-level concern), but the integration must be verified.
- The `down` migration script concatenates multiple statements with semicolons in a single Python string. When a `rollback_migration()` function is added, it should also use `executescript` (not `execute`, which only runs one statement).

---

## Verdict

**Approve.** No blocking issues. The DDL matches the data model spec exactly. The migration engine is correct and idempotent for v1. Tests are comprehensive for the current scope. Five non-blocking suggestions are documented, with three follow-up issues proposed for pre-v2 hardening.

---

# Review Notes -- ISSUE-003 DB Connection Manager PR

**Reviewer:** Senior Code Review Agent
**Date:** 2026-03-03
**Branch:** `issue/ISSUE-003-db-connection`
**Files changed:** 2 (121 insertions)

---

## Code Review

### Blocking Issues

None.

### Minor Fixes Applied

1. **Unused import `sqlite3` in test_db.py (FIXED)** — Removed unused `import sqlite3` from test file.

### Findings

1. **`db.py` is clean and minimal** — 40 lines, single responsibility. Path resolution priority (`db_path` arg > env var > default) is correct. `os.makedirs(exist_ok=True)` handles the directory creation safely.

2. **PRAGMA execution order is correct** — WAL and FK PRAGMAs are set before `run_migrations()`, which is important because migrations need FK enforcement active.

3. **No connection pooling** — Each call to `get_connection()` creates a new connection. This is appropriate for the CLI plugin use case (request-response per DM).

4. **`tmp_path` type hints use `object`** — Pytest's `tmp_path` fixture returns `pathlib.Path`, but the hint doesn't affect behavior. Non-blocking.

### Follow-ups

- Consider adding `conn.row_factory = sqlite3.Row` in `get_connection()` when cmd_* handlers need dict-like row access.

---

## Security Findings

### Summary

No security issues found.

| # | Severity | Category | Finding | Status |
|---|----------|----------|---------|--------|
| S-1 | **Pass** | File permissions | `os.makedirs` uses default umask. On Unix, this creates directories with 0o777 minus umask (typically 0o022 = 0o755). Acceptable for local CLI tool. | Pass |
| S-2 | **Pass** | Path traversal | DB path comes from env var or explicit arg, both controlled by the user. No user input from Slack reaches this function. | Pass |
| S-3 | **Pass** | Sensitive data | No secrets. Default path uses `~/.openclaw/` which is standard. | Pass |

---

## Verdict

**Approve with minor fix applied.** Removed unused import. No blocking issues. The connection manager correctly implements WAL, FK, directory creation, env var override, and schema initialization.

---
---

# Review Notes -- ISSUE-004 Input Parser PR

**Reviewer:** Senior Code Review Agent
**Date:** 2026-03-03
**Branch:** `issue/ISSUE-004-input-parser`
**Files changed:** 2 (parser.py: 55 lines, test_parser.py: 165 lines)

---

## Code Review

### Spec Compliance

**Architecture alignment**: The parsing strategy matches `docs/architecture.md` R-002:
1. Extract `/p <project>` from end of string -- implemented correctly.
2. Extract URL via `https?://` regex -- implemented correctly.
3. Remaining text = title -- implemented correctly.
4. Parsing order `/p` then URL then title -- matches spec.

**File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/parser.py`

**Acceptance Criteria verification**:
- `extract_project_option("text /p Backend")` returns `("text", "Backend")` -- covered by `test_basic_project_extraction` (line 10).
- `extract_project_option("text without project")` returns `("text without project", None)` -- covered by `test_no_project_option` (line 14).
- `extract_url("..." + URL)` returns `(remaining, URL)` -- covered by `test_basic_url_extraction` (line 54).
- `parse_save(full_args)` returns `(title, link, project)` -- covered by `test_full_save_with_title_url_project` (line 108).
- Empty/whitespace inputs return None -- covered by `test_empty_string` and `test_whitespace_only` across all three test classes.
- Parsing order `/p` then URL then title -- verified by reading `parse_save()` implementation (lines 51-54).

All acceptance criteria are met.

### Blocking Issues

None. All 25 tests pass.

### Suggestions (non-blocking)

1. **Function name diverges from architecture spec**

   The architecture document (`docs/architecture.md`, line 86) specifies `parse_project_option(args)` but the implementation uses `extract_project_option(text)`. While `extract_` is arguably a better name (it describes the operation more precisely), the inconsistency with the spec could cause confusion when implementing `dispatcher.py` (ISSUE-005) which will import this function.

   Additionally, the spec defines `parse_save` as returning `ParsedSave` (a named type), but the implementation returns a bare `tuple[str | None, str | None, str | None]`. A `NamedTuple` or `dataclass` would improve readability at call sites (e.g., `result.title` vs `result[0]`).

   **Recommendation:** Either update `architecture.md` to match the implementation names, or rename the function. If keeping tuples, consider adding a `ParsedSave = NamedTuple(...)` for the `parse_save` return type to match spec and improve usability.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/parser.py` (lines 15, 40)

2. **`extract_url` leaves double spaces when URL is in the middle of text**

   When a URL appears between two words, the concatenation `text[:m.start()] + text[m.end():]` produces a double space. For example, `extract_url("before https://example.com after")` returns `("before  after", ...)`. The test at line 79 explicitly asserts this double-space behavior. While `.strip()` is applied to the outer result, internal double spaces are preserved.

   This is non-blocking because `title` is used for display/storage and double spaces are cosmetically minor. However, if titles are used for search (LIKE matching), double spaces could cause unexpected mismatches.

   **Recommendation:** Replace the concatenation with a regex sub or normalize internal whitespace: `" ".join(remaining.split())`.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/parser.py` (line 35)

3. **Missing test: URL containing `/p` as a path segment**

   The input `"title https://slack.com/p/something /p Backend"` is a plausible real-world case (Slack URLs often have short path segments). While the current regex correctly handles this (the `\s+` before `/p` prevents matching inside URLs), there is no test documenting this behavior. Adding an explicit test would prevent future regressions if the regex is modified.

   **Recommended test:**
   ```python
   def test_url_with_p_in_path(self) -> None:
       title, link, project = parse_save(
           "title https://slack.com/p/something /p Backend"
       )
       assert title == "title"
       assert link == "https://slack.com/p/something"
       assert project == "Backend"
   ```

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_parser.py`

4. **Missing test: `/p` with multiple words after it (not matched)**

   The regex `(\S+)` captures only one non-whitespace token after `/p`. Input like `"title /p Backend Extra"` would NOT match the project pattern (because `\S+` captures `Backend` but then `Extra` is not `\s*$`). This means the entire string is treated as title. This is correct behavior per spec, but no test documents it.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_parser.py`

5. **Missing test: `parse_save` with title only (no URL, no project)**

   There is no test for `parse_save("just a title")`. This is a valid user input scenario and should return `("just a title", None, None)`.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_parser.py`

6. **Code quality is high overall**

   - Zero runtime dependencies, stdlib only -- matches NFR-003.
   - Compiled regexes at module level (not inside functions) -- good for performance.
   - Docstrings are clear and explain return semantics.
   - Type hints are complete and use modern `str | None` syntax with `from __future__ import annotations`.
   - Functions are pure (no side effects, no state) -- matches architecture spec "순수 함수".
   - Module is 55 lines total -- well within maintainability bounds.

### Follow-up Issues

- **ISSUE-FOLLOW-006:** Align function naming between `architecture.md` and `parser.py` (either rename `extract_project_option` to `parse_project_option` or update the spec).
- **ISSUE-FOLLOW-007:** Consider introducing `ParsedSave` NamedTuple for `parse_save` return type to match architecture spec and improve call-site readability.
- **ISSUE-FOLLOW-008:** Normalize internal whitespace in `extract_url` remaining text (collapse double spaces).

---

## Security Findings

### Summary

No Critical or High severity issues found. The parser module handles untrusted input (Slack message text) safely.

### Detailed Assessment

| # | Severity | Category | Finding | Status |
|---|----------|----------|---------|--------|
| S-1 | **Pass** | ReDoS | Both regexes (`_URL_RE` = `https?://\S+`, `_PROJECT_RE` = `\s+/p\s+(\S+)\s*$`) were tested with 100,000-word inputs. Execution time: URL regex <0.1ms, project regex <2ms. No catastrophic backtracking patterns. Both patterns use non-overlapping character classes (`\S+`, `\s+`) with no nested quantifiers. | Pass |
| S-2 | **Pass** | Injection | Parser output (title, link, project) will be passed to SQL queries in cmd_save (ISSUE-006+). The parser itself does not sanitize or escape -- this is correct because SQL parameterization is the responsibility of the DB layer. No injection risk in the parser module itself. | Pass |
| S-3 | **Pass** | Input validation | Empty strings and whitespace-only inputs are handled correctly, returning None/empty values. No exceptions are raised on any input type. | Pass |
| S-4 | **Low** | URL validation | The URL regex `https?://\S+` is intentionally permissive -- it matches anything starting with `http://` or `https://` followed by non-whitespace. This means `https://not-a-real-url!!!` would be accepted. This is acceptable because URL validation is not the parser's responsibility (the URL will be stored as-is for user reference), but downstream consumers should be aware that `link` values are not validated URLs. | Informational |
| S-5 | **Pass** | Sensitive data | No hardcoded secrets, API keys, or credentials. No file I/O. No network calls. | Pass |

### Notes for Future PRs

- When `cmd_save` is implemented: ensure that `title`, `link`, and `project` values from `parse_save()` are passed to SQL via parameterized queries (`?` placeholders), never via string formatting. The parser intentionally does not sanitize these values.
- The `link` field should not be rendered as clickable HTML without proper escaping if any web UI is added in the future (XSS prevention). For Slack message responses, Slack handles URL rendering safely.

---

## Verdict

**Approve.** No blocking issues. All 25 tests pass. All acceptance criteria are met. The implementation correctly follows the architecture's parsing strategy (R-002). The code is clean, well-typed, and well-documented at 55 lines. Five non-blocking suggestions are documented, primarily around spec naming alignment, edge-case test coverage, and minor cosmetic whitespace handling. Three follow-up issues proposed.

---
---

# Review Notes -- ISSUE-005 Dispatcher and Plugin Entry Point PR

**Reviewer:** Senior Code Review Agent
**Date:** 2026-03-03
**Branch:** `issue/ISSUE-005-dispatcher`
**Files changed:** 13 (plugin.py, dispatcher.py, 9 cmd_* stubs, test_dispatcher.py, test_smoke.py)

---

## Code Review

### Spec Compliance

**Acceptance Criteria verification:**
- `handle_message("/archive save ...", "U01")` routes to `cmd_save.handle` -- covered by `test_save_routing` (line 40).
- `handle_message("/archive list", "U01")` routes to `cmd_list.handle` -- covered by `test_list_routing` (line 46).
- `handle_message("/archive project list", "U01")` routes to `cmd_project_list.handle` -- covered by `test_project_list_routing` (line 80).
- `handle_message("일반 메시지", "U01")` returns `None` -- covered by `test_non_archive_message_returns_none` (line 14).
- `handle_message("/archive", "U01")` returns unknown command message -- covered by `test_archive_no_subcommand_returns_unknown` (line 23).
- `handle_message("/archive xyz", "U01")` returns unknown command message -- covered by `test_unknown_subcommand_returns_unknown` (line 29).
- All cmd_* modules have `handle(args: str, user_id: str) -> str` stub -- covered by `TestCmdStubs` class (9 tests, lines 104-151).

All acceptance criteria are met.

### Blocking Issues

1. **Prefix matching too permissive -- `/archivesave` treated as `/archive save` (FIXED)**

   `plugin.py` line 20 used `message.startswith("/archive")` which means any message beginning with `/archive` would be dispatched, even without a space delimiter. The string `"/archivesave"` starts with `"/archive"`, so `dispatch()` would strip the prefix leaving `"save"`, which routes to `cmd_save.handle`. Similarly, `"/archiver"` would leave `"r"` and return the unknown command message rather than `None` (LLM bypass).

   This violates the spec: non-`/archive` messages should return `None` so the LLM can process them. `/archiver` or `/archives` are not the `/archive` command.

   **Fix applied:** Added a guard in `plugin.py` that checks the character immediately after the `/archive` prefix. If it is not whitespace or end-of-string, `None` is returned. Added test `test_archive_prefix_without_space_returns_none` covering `/archivesave`, `/archiver`, and `/archives`.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/plugin.py` (line 20-24)
   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_dispatcher.py` (new test)

### Suggestions (non-blocking)

2. **Dispatch table type annotation uses `object` instead of a Protocol**

   `_COMMANDS: dict[str, object]` and `_PROJECT_SUBCOMMANDS: dict[str, object]` use `object` as the value type, then rely on `# type: ignore[union-attr]` to suppress the type error on `.handle()` calls. This loses type safety -- any object could be placed in the dict without a type error.

   **Recommendation:** Define a `Protocol` class:
   ```python
   from typing import Protocol

   class CommandHandler(Protocol):
       def handle(self, args: str, user_id: str) -> str: ...
   ```
   Then type the dicts as `dict[str, CommandHandler]`. This removes the need for `# type: ignore` comments and catches handler signature mismatches at type-check time.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/dispatcher.py` (lines 19, 28)

3. **Commands are case-sensitive**

   `/archive SAVE` or `/archive Save` returns the unknown command message. This is likely correct for a slash-command interface (Slack slash commands are case-sensitive), but the spec does not explicitly state case sensitivity. If case-insensitive matching is desired, a `.lower()` call on `cmd` and `subcmd` would be the fix. Noting this for confirmation with the team.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/dispatcher.py` (line 52)

4. **`test_smoke.py` assertion is weak for routed commands**

   `test_handle_message_routes_archive_command` (line 19) asserts `result is not None`. Since stubs return `""` (empty string), this passes, but the assertion does not verify the result is a string or that routing actually occurred. When stubs are implemented, this test will not catch regressions in routing. The `test_dispatcher.py` tests cover routing thoroughly via mocks, so this is low priority, but the smoke test could be tightened to `assert isinstance(result, str)`.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_smoke.py` (line 19)

5. **Missing edge-case test: `/archive  save` with extra spaces between prefix and subcommand**

   The `split(None, 1)` call in `dispatcher.py` line 51 handles multiple spaces correctly (Python's `str.split(None)` splits on any whitespace run). However, no test explicitly verifies this behavior. Adding a test like `handle_message("/archive  save title link", "U01")` would document the expected behavior and prevent regressions.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_dispatcher.py`

6. **Missing edge-case test: `/archive project  list` with extra spaces in 2nd-level routing**

   Same as above but for the project subcommand level. `_dispatch_project` also uses `split(None, 1)` so it handles this correctly, but there is no test.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_dispatcher.py`

7. **All 9 cmd_* stubs are identical boilerplate**

   Each stub file is 8 lines with the exact same structure. When handlers are implemented (ISSUE-006 through ISSUE-014), each will diverge, so this is acceptable for now. However, if stub generation is needed again, a template or code generator would reduce manual error.

8. **Dispatcher imports all handlers at module level**

   All 9 `cmd_*` modules are imported at the top of `dispatcher.py`. This is fine for a stdlib-only project with lightweight modules, but if any handler gains heavy imports in the future (e.g., external libraries), it could slow down startup. Lazy imports would mitigate this. Non-blocking for now since all modules are trivial stubs.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/dispatcher.py` (lines 5-15)

### Follow-up Issues

- **ISSUE-FOLLOW-009:** Introduce a `CommandHandler` Protocol type for the dispatch table to remove `# type: ignore` comments and gain static type safety.
- **ISSUE-FOLLOW-010:** Add edge-case tests for extra whitespace between prefix and subcommand (both levels).
- **ISSUE-FOLLOW-011:** Confirm case-sensitivity policy for subcommands with the team and document the decision.

---

## Security Findings

### Summary

One Medium severity issue found and fixed (prefix matching bypass). No Critical or High severity issues.

### Detailed Assessment

| # | Severity | Category | Finding | Status |
|---|----------|----------|---------|--------|
| S-1 | **Medium** | Input validation | **Prefix matching bypass (FIXED).** `message.startswith("/archive")` matched messages like `/archivesave`, `/archiver`, `/archives`. While these would not reach a real handler (they would hit the unknown-command path or route to the wrong stub), the issue is that they would NOT return `None`, meaning the LLM bypass would not fire. A user typing `/archiver` expecting LLM processing would get the Korean unknown-command error instead. The fix adds a whitespace/end-of-string check after the prefix. | Fixed |
| S-2 | **Pass** | Command injection | The dispatcher uses a static dictionary lookup (`_COMMANDS.get(cmd)`) to route commands. There is no `eval()`, `exec()`, `getattr()` on user input, or dynamic module loading. User input cannot influence which code is executed beyond the predefined dispatch table. | Pass |
| S-3 | **Pass** | Input validation | `split(None, 1)` safely handles any amount of whitespace. Empty strings and whitespace-only inputs are handled with explicit checks before dictionary lookup. No `IndexError` or `KeyError` is possible. | Pass |
| S-4 | **Pass** | Sensitive data | No hardcoded secrets, API keys, credentials, or file paths in any of the 13 files reviewed. | Pass |
| S-5 | **Pass** | Dependencies | Zero runtime dependencies. No new dev dependencies added. | Pass |
| S-6 | **Low** | Information disclosure | The unknown command message is in Korean: "알 수 없는 명령입니다. /archive help 로 사용법을 확인하세요." This reveals the `/archive help` command to any user, which is acceptable since it is a help command. No internal paths, versions, or stack traces are exposed. | Pass |

### Notes for Future PRs

- When cmd_* handlers are implemented, each handler will receive unsanitized `args` from user input. Every handler must validate and sanitize its `args` parameter before passing values to SQL queries or external systems. The dispatcher intentionally does NOT sanitize -- this is a "pass-through" design that places the validation burden on each handler.
- The `user_id` parameter is passed through from the plugin entry point. When authentication/authorization is added, verify that `user_id` is validated at the plugin boundary (not trusted from the message content).

---

## Verdict

**Approve with fix applied.** One blocking issue (prefix matching bypass) has been resolved. All 80 tests pass (79 existing + 1 new). All acceptance criteria are met. The dispatcher design is clean, extensible, and follows a secure static-dispatch pattern. Seven non-blocking suggestions are documented, with three follow-up issues proposed.

---
---

# Review Notes -- ISSUE-006 Save Command Handler PR

**Reviewer:** Senior Code Review Agent
**Date:** 2026-03-03
**Branch:** `issue/ISSUE-006-cmd-save`
**Files changed:** 3 (cmd_save.py: 36 lines, db.py: +27 lines, test_cmd_save.py: 155 lines)

---

## Code Review

### Spec Compliance

**Acceptance Criteria verification:**
- Title+link creates archive record, success message with ID/title -- covered by `test_save_title_and_link` (line 25) and `test_save_response_contains_id` (line 109).
- With project, auto-create if needed, response includes project name -- covered by `test_save_with_project` (line 36), `test_save_creates_project_automatically` (line 48), `test_save_uses_existing_project` (line 63).
- No project results in `project_id=NULL` -- covered by `test_save_without_project_stores_null` (line 83).
- Missing title/link returns usage message -- covered by `test_missing_title_and_link` (line 139), `test_missing_link` (line 143), `test_missing_title` (line 148), `test_whitespace_only` (line 152).
- `user_id` recorded in `archives.user_id` -- covered by `test_save_records_user_id` (line 96).
- SQL parameterized queries only -- verified by code inspection (see Security Findings).

All acceptance criteria are met.

**UX Spec response format (Section 3.1):** Verified. `cmd_save.py` lines 26-31 produce the exact format with 8-space indentation for title and project lines, joined by newline. Matches spec.

**Data Model query patterns:** Verified. `get_or_create_project` uses `INSERT OR IGNORE INTO projects (user_id, name) VALUES (?, ?)` then `SELECT id FROM projects WHERE user_id = ? AND name = ?`. `insert_archive` uses `INSERT INTO archives (user_id, project_id, title, link) VALUES (?, ?, ?, ?)`. All match the spec patterns exactly.

### Blocking Issues

None. All 12 tests pass.

### Findings

1. **Transaction atomicity is correct by design**

   `get_or_create_project()` performs an `INSERT OR IGNORE` without committing. `insert_archive()` performs an `INSERT` and then calls `conn.commit()`. Because SQLite's Python binding uses `isolation_level = ''` (deferred transactions), the first DML statement auto-begins a transaction. The single `conn.commit()` in `insert_archive` commits both the project creation and archive insertion atomically. If an exception occurs between the two calls, neither write is persisted. This is the correct behavior.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` (lines 43-69)

2. **Connection management is correct**

   `cmd_save.handle()` uses `try/finally` to ensure `conn.close()` is always called, even on exception. The connection is opened after input validation, so the error path (missing title/link) does not create a connection at all. This is efficient and correct.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_save.py` (lines 18-35)

3. **`get_or_create_project` has an unguarded `row[0]` access**

   At line 53, `row[0]` is accessed without a `None` check on `row`. In theory, after `INSERT OR IGNORE` the subsequent `SELECT` should always find a row (either newly inserted or previously existing). However, a concurrent `DELETE` between the INSERT and SELECT, or a schema mismatch, could cause `row` to be `None`, resulting in a `TypeError: 'NoneType' object is not subscriptable`.

   This is extremely unlikely in the current single-connection, single-process architecture. The `# type: ignore[index]` comment acknowledges this. Non-blocking, but a defensive `if row is None: raise RuntimeError(...)` would improve debuggability.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` (line 53)

4. **`insert_archive` returns `cur.lastrowid` which could theoretically be `None`**

   `cursor.lastrowid` is `None` if no INSERT has been executed or if the table does not have a `ROWID` column. For the `archives` table with an `INTEGER PRIMARY KEY`, `lastrowid` will always be set after a successful INSERT. The `# type: ignore[return-value]` comment acknowledges this. Non-blocking.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` (line 69)

### Suggestions (non-blocking)

5. **Missing test: exception during DB operation does not leak connection**

   No test verifies that the `finally: conn.close()` block works correctly when an exception is raised during `get_or_create_project` or `insert_archive`. A test that monkeypatches one of these functions to raise an exception, then verifies the connection is closed (or at least that the handler propagates the exception cleanly), would improve confidence.

   **Recommended test:**
   ```python
   def test_save_closes_connection_on_db_error(self, tmp_path, monkeypatch):
       db_path = _make_db(tmp_path)
       monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)

       def boom(*args, **kwargs):
           raise RuntimeError("simulated DB failure")

       monkeypatch.setattr("openclaw_archiver.cmd_save.insert_archive", boom)

       with pytest.raises(RuntimeError, match="simulated DB failure"):
           handle("title https://example.com", _USER)
   ```

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_save.py`

6. **Missing test: Unicode titles and project names**

   The test suite includes Korean text in titles (good), but does not test emoji, CJK characters beyond Korean, or other multi-byte Unicode in project names. While SQLite handles Unicode natively, a test with `"title https://example.com /p \\ud83d\\ude80Rocket"` would document the behavior.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_save.py`

7. **Missing test: very long title or link**

   No test verifies behavior with extremely long strings (e.g., 10,000-character titles). SQLite has a default maximum string length of 1 billion bytes, so this is unlikely to fail, but a regression test would document the expected behavior and could catch future column constraints.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_save.py`

8. **Test helper `_make_db` opens and closes a connection just to run migrations**

   This is correct -- it ensures the schema is created before the test. However, every call to `handle()` also calls `get_connection()` which calls `run_migrations()` again. Since migrations are idempotent (using `IF NOT EXISTS`), this is safe but does redundant work. Non-blocking.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_save.py` (lines 14-19)

9. **`_USAGE` is duplicated between `cmd_save.py` and `test_cmd_save.py`**

   The usage string `"사용법: /archive save <제목> <링크> [/p <프로젝트>]"` is defined in both files. If the message changes in one file, the test could silently pass or fail depending on which file is updated. Consider importing the constant from `cmd_save` in the test, or using `assert result.startswith("사용법:")` for a looser match.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_save.py` (line 10)
   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_save.py` (line 8)

10. **`tmp_path` type hint uses `object` instead of `pathlib.Path`**

    Pytest's `tmp_path` fixture returns `pathlib.Path`. Using `object` as the type hint works but loses IDE support and type safety. This is consistent with the test style in ISSUE-003 (noted in that review as well). Non-blocking.

    **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_save.py` (multiple test methods)

### Follow-up Issues

- **ISSUE-FOLLOW-012:** Add defensive `None` check in `get_or_create_project` for the `row` variable, with a descriptive `RuntimeError` for debuggability.
- **ISSUE-FOLLOW-013:** Add edge-case tests for exception handling (connection cleanup), Unicode edge cases, and very long inputs.
- **ISSUE-FOLLOW-014:** Consider importing `_USAGE` from `cmd_save` in tests (or using a shared constant) to avoid string duplication and drift.

---

## Security Findings

### Summary

No Critical or High severity issues found. All SQL queries use parameterized binding. Transaction semantics are correct. Connection cleanup is handled properly.

### Detailed Assessment

| # | Severity | Category | Finding | Status |
|---|----------|----------|---------|--------|
| S-1 | **Pass** | SQL Injection | All six SQL statements across `get_or_create_project` and `insert_archive` use `?` parameterized placeholders. No string formatting, f-strings, or concatenation is used to construct SQL. User-supplied `title`, `link`, `project`, and `user_id` values are all bound via parameter tuples. Verified in `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` lines 45-67. | Pass |
| S-2 | **Pass** | Input validation | Missing title or link returns usage message without creating a DB connection. The `if not title or not link` guard at `cmd_save.py` line 15 prevents empty/None values from reaching the database layer. | Pass |
| S-3 | **Pass** | Connection management | `try/finally` pattern in `cmd_save.py` lines 19-35 ensures the connection is always closed, even on exception. No connection leak is possible. | Pass |
| S-4 | **Pass** | Transaction safety | `get_or_create_project` INSERT and `insert_archive` INSERT are committed together by the single `conn.commit()` at `db.py` line 68. If any step fails, neither write is persisted. This provides atomicity for the save-with-project path. | Pass |
| S-5 | **Low** | Denial of service | No input length limits are enforced on `title`, `link`, or `project` before they are stored in SQLite. An attacker could send extremely long strings (megabytes) via Slack to bloat the database. In practice, Slack message length is limited to ~40,000 characters, which bounds the maximum input size. This is a theoretical concern. | Informational |
| S-6 | **Pass** | Sensitive data | No hardcoded secrets, API keys, credentials, or file paths in any of the three files. | Pass |
| S-7 | **Pass** | XSS | The response is a plain text string returned to the Slack API. Slack renders messages safely and does not execute embedded scripts. No HTML is generated. User-supplied `title` and `project` values are included in the response via f-strings, but this is safe for Slack's text rendering context. | Pass |

### Notes for Future PRs

- The `commit()` call is inside `insert_archive`. If future code needs to perform multiple inserts in a single transaction (e.g., batch save), the commit location would need to be refactored. Consider whether `commit()` should be the caller's responsibility rather than buried inside a utility function. This is a design decision, not a bug.
- When implementing `cmd_delete` or `cmd_edit`, ensure that authorization checks verify the `user_id` matches the archive's owner before modifying records. The current save command only creates records, so ownership checks are not yet needed.

---

## Verdict

**Approve.** No blocking issues. All 12 tests pass. All acceptance criteria are met. SQL safety is confirmed -- every query uses parameterized binding. Transaction atomicity is correct by design. Connection cleanup is properly handled with `try/finally`. The code is clean, minimal (36 lines for the handler, 27 new lines in db.py), and follows existing project patterns. Five non-blocking suggestions are documented, primarily around missing edge-case tests and minor code quality improvements. Three follow-up issues proposed.

---
---

# Review Notes -- ISSUE-007 List Command Handler PR

**Reviewer:** Senior Code Review Agent
**Date:** 2026-03-03
**Branch:** `issue/ISSUE-007-cmd-list`
**Files changed:** 3 (cmd_list.py: 83 lines, db.py: +34 lines, test_cmd_list.py: 146 lines)

---

## Code Review

### Spec Compliance

**Acceptance Criteria verification:**
- All list with created_at DESC, #id/title/link/project-or-미분류/date -- covered by `test_list_all_returns_user_archives` (line 36), `test_list_all_shows_project_name` (line 55), `test_list_all_shows_unclassified` (line 63), `test_list_all_contains_id_title_link_date` (line 71).
- Project list with project header, items without project label -- covered by `test_list_by_project` (line 96) and `test_list_by_project_excludes_project_label` (line 107).
- Empty list returns proper empty message -- covered by `test_list_all_empty` (line 82).
- Nonexistent project returns error message -- covered by `test_list_nonexistent_project` (line 116).
- Project exists but no archives returns empty-project message -- covered by `test_list_project_exists_but_empty` (line 124).
- Data isolation (other users' archives not shown) -- covered by `test_list_all_excludes_other_user` (line 47) and `test_list_by_project_other_user_not_visible` (line 136).

All acceptance criteria are met.

**UX Spec response format:** Verified line-by-line against the UX spec provided in the PR context.
- All-list header: `저장된 메세지 ({count}건)` -- matches spec.
- Project-list header: `저장된 메세지 -- {project_name} ({count}건)` -- matches spec.
- Separator: 8-space indent + `---...---` -- matches spec.
- Item lines: `#id  title` at 8-space indent, link at 12-space indent, metadata at 12-space indent -- matches spec.
- All-list metadata: `프로젝트: {name} | {date}` or `미분류 | {date}` -- matches spec.
- Project-list metadata: `{date}` only (no project label) -- matches spec.
- Empty states: all three messages match spec exactly.

**SQL query patterns:** Verified against spec.
- `list_archives`: `LEFT JOIN projects p ON a.project_id = p.id WHERE a.user_id = ? ORDER BY a.created_at DESC` -- matches spec.
- `find_project`: `SELECT id, name FROM projects WHERE user_id = ? AND name = ?` -- matches spec (returns id for use in the second query).
- `list_archives_by_project`: `SELECT ... FROM archives a WHERE a.user_id = ? AND a.project_id = ? ORDER BY a.created_at DESC` -- matches spec.

### Blocking Issues

None. All 103 tests pass (11 new + 92 existing).

### Findings

1. **SQL correctness: LEFT JOIN is appropriate and correct**

   The `list_archives` query uses `LEFT JOIN projects p ON a.project_id = p.id`. This is correct because archives can have `project_id = NULL` (unclassified), and a LEFT JOIN ensures those rows are included with `p.name = NULL`. The `WHERE a.user_id = ?` clause correctly scopes results to the requesting user. There is no cross-user data leak: even though the JOIN is on `p.id` without a `p.user_id` filter, this is safe because archives can only be created with project IDs belonging to the same user (enforced by the save flow in `cmd_save.handle` which calls `get_or_create_project` with the same `user_id`).

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` (lines 85-92)

2. **SQL parameterization: all queries use `?` placeholders**

   All three new DB functions (`find_project`, `list_archives`, `list_archives_by_project`) use parameterized queries with `?` placeholders. No string formatting or concatenation is used. This is consistent with the existing codebase pattern.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` (lines 72-105)

3. **Connection management: try/finally is correct**

   `cmd_list.handle()` uses `try/finally` to ensure `conn.close()` is always called, matching the pattern established in `cmd_save.handle()`. The connection is opened after the `extract_project_option` call, which is efficient because the parser is pure and cannot fail in a way that requires cleanup.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_list.py` (lines 24-30)

4. **`created_at` slicing is defensive**

   The expression `created_at[:10] if created_at else ""` safely handles the (unlikely) case where `created_at` is `None`. Since the schema defines `DEFAULT (datetime('now'))`, this column should always be populated. The guard is appropriate defensive programming.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_list.py` (lines 42, 73)

### Suggestions (non-blocking)

5. **The `" " + args` workaround is a code smell but functionally correct**

   At line 22, `extract_project_option(" " + args if args else args)` prepends a space so the regex `\s+/p\s+(\S+)\s*$` can match when `/p` is at the start of `args`. This is necessary because the dispatcher strips the subcommand and passes only the remaining text (e.g., `/p Backend` instead of ` /p Backend`).

   The workaround is correct and well-commented. However, it reveals a design tension: `extract_project_option` was designed for `parse_save` where `/p` naturally appears after other text. The `\s+` prefix requirement is an implementation detail leaking into the caller.

   **Cleaner alternatives (for follow-up, not this PR):**
   - Add an optional `allow_start=True` parameter to `extract_project_option` that adjusts the regex to `(?:^|\s+)/p\s+(\S+)\s*$`.
   - Create a second regex `_PROJECT_RE_START` that uses `^/p\s+(\S+)\s*$` and try it when the primary regex fails.
   - Modify the primary regex to use `(?:^|\s+)` instead of `\s+`, which would make it work for both `parse_save` and `cmd_list` without the workaround.

   The third option is the simplest and would not break any existing tests (since `parse_save` always passes text where `/p` follows other content or whitespace).

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_list.py` (line 22)

6. **Missing test: ordering verification**

   The AC specifies `created_at DESC` ordering, and the SQL implements it, but no test explicitly verifies that archives appear in newest-first order. The `_seed_db` function inserts archives sequentially (IDs 1, 2, 3), and since `created_at` defaults to `datetime('now')`, all three rows may have the same timestamp (SQLite's `datetime('now')` has 1-second resolution). A test that explicitly verifies ordering would need to either:
   - Insert archives with explicit `created_at` values, or
   - Verify that ID ordering is descending (since IDs increment and timestamps are identical within a test, DESC order by `created_at` with identical timestamps may return any order).

   This is a latent test gap. In practice, the SQL is correct, but the test does not prove it.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_list.py`

7. **Missing test: `handle(None, user_id)` -- None args**

   The handler's type signature declares `args: str`, but if `None` is accidentally passed (e.g., from a dispatcher bug), the expression `" " + args if args else args` would evaluate to `" " + args` (since `None` is falsy... wait, `if args` with `None` is falsy, so it would pass `None` to `extract_project_option`). Actually, looking more carefully: `args = None`, `" " + args if args else args` evaluates to `args` (the else branch), so `extract_project_option(None)` would be called, which would fail on `_PROJECT_RE.search(None)` with `TypeError`. This is acceptable because the type contract says `args: str`, and the dispatcher always passes a string (empty string `""` when no args). But a defensive `args = args or ""` at the top would be more robust.

   This is not a blocking issue because the caller contract is well-defined and correct.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_list.py` (line 22)

8. **`_list_all` and `_list_by_project` share duplicated formatting logic**

   Both functions have identical patterns: build header, add separator, loop over rows appending formatted lines, remove trailing empty line. The only differences are the header format, the per-item metadata line, and the tuple shape. A shared `_format_rows` helper could reduce this duplication. Non-blocking for 83 lines of code, but worth considering if more list-like commands are added.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_list.py` (lines 33-82)

9. **`find_project` returns a tuple but only the first element is used**

   `find_project` returns `(id, name)` but `_list_by_project` only uses `project[0]` (the id). Returning `tuple[int, str] | None` is fine for generality, but the extra `name` fetch is wasted in this context. Non-blocking -- the overhead is negligible.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` (line 74)
   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_list.py` (line 61)

10. **`tmp_path` type hint uses `object` instead of `pathlib.Path`**

    Consistent with previous test files (noted in ISSUE-003 and ISSUE-006 reviews). Non-blocking.

    **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_list.py` (multiple methods)

11. **Test DB seed function creates a new connection per test**

    Each test calls `_seed_db(tmp_path)` which creates a fresh DB file and seeds it. Then `handle()` calls `get_connection()` which opens a second connection to the same file. This is correct (WAL mode supports concurrent readers/writers), but means each test runs migrations twice. Non-blocking since migrations are idempotent and fast.

    **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_list.py` (lines 14-30)

### Follow-up Issues

- **ISSUE-FOLLOW-015:** Refactor `_PROJECT_RE` regex to use `(?:^|\s+)` instead of `\s+` so that `extract_project_option` works when `/p` is at the start of the string, eliminating the `" " + args` workaround in `cmd_list.py`.
- **ISSUE-FOLLOW-016:** Add an ordering verification test for the list command that uses explicit `created_at` values to confirm DESC sorting.
- **ISSUE-FOLLOW-017:** Consider extracting shared formatting logic from `_list_all` and `_list_by_project` into a helper if additional list-style commands are added.

---

## Security Findings

### Summary

No Critical or High severity issues found. All SQL queries use parameterized binding. Connection cleanup is handled properly. Data isolation between users is enforced correctly.

### Detailed Assessment

| # | Severity | Category | Finding | Status |
|---|----------|----------|---------|--------|
| S-1 | **Pass** | SQL Injection | All three new DB functions (`find_project`, `list_archives`, `list_archives_by_project`) use `?` parameterized placeholders for all user-supplied values (`user_id`, `name`, `project_id`). No string formatting or concatenation. Verified in `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` lines 72-105. | Pass |
| S-2 | **Pass** | Authorization | Data isolation is correctly enforced. `list_archives` filters by `a.user_id = ?`. `find_project` filters by `user_id = ? AND name = ?`. `list_archives_by_project` filters by `a.user_id = ? AND a.project_id = ?`. The double filter on both `user_id` and `project_id` in `list_archives_by_project` prevents a user from viewing another user's archives even if they guess a valid `project_id`. Tests `test_list_all_excludes_other_user` and `test_list_by_project_other_user_not_visible` verify this. | Pass |
| S-3 | **Pass** | Connection management | `try/finally` pattern ensures connection is always closed. No connection leak possible. | Pass |
| S-4 | **Pass** | Information disclosure | Error messages reveal only the project name the user typed (e.g., `"Backend" 프로젝트를 찾을 수 없습니다.`). No internal paths, SQL errors, or stack traces are exposed. The project name is user-supplied input echoed back, which is safe in Slack's text rendering context. | Pass |
| S-5 | **Low** | Input validation | The `project_name` extracted from user input is passed directly to `find_project` as a SQL parameter. While parameterization prevents injection, there is no length or character validation on `project_name`. A user could pass an extremely long project name string. This is bounded by Slack's message length limit (~40,000 chars) and results in a simple "not found" response, so the impact is negligible. | Informational |
| S-6 | **Pass** | XSS | All output is plain text returned to Slack. No HTML generation. User-supplied values (`title`, `link`, `project_name`) are included via f-strings in plain text context. Slack handles rendering safely. | Pass |
| S-7 | **Pass** | Sensitive data | No hardcoded secrets, API keys, credentials, or file paths in any of the three files reviewed. | Pass |

---

## Verdict

**Approve.** No blocking issues. All 103 tests pass (11 new + 92 existing). All acceptance criteria are met. SQL queries are correct (LEFT JOIN for nullable project, parameterized binding, DESC ordering). Connection management follows the established `try/finally` pattern. Data isolation between users is enforced and tested. The `" " + args` workaround is functionally correct and well-commented, with a follow-up issue proposed for a cleaner solution. Six non-blocking suggestions are documented, with three follow-up issues proposed.

---
---

# Review Notes -- ISSUE-008 Search Command Handler PR

**Reviewer:** Senior Code Review Agent
**Date:** 2026-03-03
**Branch:** `issue/ISSUE-008-cmd-search`
**Files changed:** 3 (cmd_search.py: 89 lines, db.py: +26 lines, test_cmd_search.py: 131 lines)

---

## Code Review

### Spec Compliance

**Acceptance Criteria verification:**
- Keyword search with `COLLATE NOCASE` -- covered by `test_search_finds_matching` (line 34) and `test_search_case_insensitive` (line 52).
- Project-scoped search -- covered by `test_search_in_project` (line 84).
- Result header with keyword and count -- covered by `test_search_finds_matching` asserts `'검색 결과: "회의록" (2건)'` (line 40), and `test_search_in_project` asserts `'검색 결과: "회의록" — Backend (1건)'` (line 90).
- Missing keyword returns usage -- covered by `test_missing_keyword` (line 123), `test_whitespace_only` (line 127), `test_only_project_option` (line 129).
- No results returns appropriate empty message -- covered by `test_search_no_results` (line 63) and `test_search_in_project_no_results` (line 94).
- Nonexistent project returns error -- covered by `test_search_nonexistent_project` (line 102).
- Data isolation -- covered by `test_search_excludes_other_user` (line 44).

All acceptance criteria are met.

**UX Spec response format:** Verified against the spec provided in the PR context.
- All-search header: `검색 결과: "{keyword}" ({count}건)` -- matches spec.
- Project-search header: `검색 결과: "{keyword}" — {project_name} ({count}건)` -- matches spec.
- Separator: 8-space indent + full-width dashes -- matches spec.
- All-search items: `프로젝트: {name} | {date}` or `미분류 | {date}` -- matches spec.
- Project-search items: `{date}` only (no project label) -- matches spec and verified by `test_search_project_excludes_project_label` (line 110).
- Empty/error states: all four messages match spec exactly.

**SQL query patterns:** Verified against spec.
- `search_archives`: `LEFT JOIN`, `WHERE a.user_id = ? AND a.title LIKE ? COLLATE NOCASE`, `ORDER BY a.created_at DESC` -- matches spec.
- `search_archives_by_project`: `WHERE a.user_id = ? AND a.project_id = ? AND a.title LIKE ? COLLATE NOCASE ORDER BY a.created_at DESC` -- matches spec.

### Blocking Issues

None. All 115 tests pass (12 new + 103 existing).

### Findings

1. **SQL parameterization is correctly applied to LIKE parameters**

   Both `search_archives` and `search_archives_by_project` construct the LIKE pattern as `f"%{keyword}%"` and pass it as a parameterized value via `?` placeholder. The `%` wildcards are embedded in the Python string that is bound as a parameter, not interpolated into the SQL. This is the correct and safe approach -- the parameterized binding ensures that any SQL metacharacters in `keyword` (such as quotes or semicolons) are treated as literal values, not SQL syntax.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` (lines 118, 132)

2. **Connection management follows established pattern**

   `cmd_search.handle()` uses `try/finally` to ensure `conn.close()` is always called, consistent with `cmd_save` and `cmd_list`. The connection is opened after input validation (empty keyword check), so the error path does not create a connection. This is efficient and correct.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_search.py` (lines 29-35)

3. **LEFT JOIN is correct for all-search query**

   The `search_archives` query uses `LEFT JOIN projects p ON a.project_id = p.id` to include archives with `project_id = NULL`. This is consistent with `list_archives` in the same file and correctly supports the `미분류` display path. The project-scoped query does not need the JOIN since the project is already known.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` (lines 112-119, 126-133)

4. **`created_at` slicing is defensive and consistent**

   The expression `created_at[:10] if created_at else ""` matches the pattern used in `cmd_list.py`. Consistent across the codebase.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_search.py` (lines 47, 79)

### Suggestions (non-blocking)

5. **LIKE wildcard characters (`%`, `_`) in user input are not escaped (Low concern)**

   The LIKE pattern `f"%{keyword}%"` does not escape `%` or `_` characters that may appear in the keyword itself. If a user searches for the literal string `"100%_done"`, the `%` and `_` in the keyword would act as LIKE wildcards: `%` matches any sequence of characters, `_` matches any single character. This means the search would be broader than the user intended.

   For example, searching for `%` would match every archive title (since the pattern becomes `%%%` which is equivalent to `%`). Searching for `_` would match titles containing any single character at that position.

   **Impact assessment:** This is **Low** severity. It does not leak data across users (the `user_id = ?` filter is still enforced). It only affects the precision of the search results for the user who typed the wildcard. In practice, users are unlikely to search for `%` or `_` in a Slack archive tool. SQLite supports the `ESCAPE` clause for this purpose:

   ```python
   keyword_escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
   # ... LIKE ? ESCAPE '\\' ...
   (user_id, f"%{keyword_escaped}%")
   ```

   **Recommendation:** Note for follow-up. Not blocking because it does not create a security vulnerability -- it only affects search precision for edge-case inputs.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` (lines 118, 132)

6. **The `" " + args` workaround is repeated from `cmd_list.py`**

   Line 23 uses `extract_project_option(" " + args if args else args)`, identical to `cmd_list.py` line 22. This is the same pattern noted in ISSUE-007 review (suggestion #5). The regex `\s+/p\s+(\S+)\s*$` requires whitespace before `/p`, so a space must be prepended when `/p` may be at the start of `args`.

   This is now duplicated in two command handlers. The follow-up issue ISSUE-FOLLOW-015 (proposed in ISSUE-007 review) to fix the regex with `(?:^|\s+)` would resolve both occurrences. No additional action needed here.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_search.py` (line 23)

7. **Significant code duplication between `cmd_search.py` and `cmd_list.py`**

   The structural patterns are nearly identical between the two modules:
   - `handle()`: extract project option, open connection, branch on project_name, try/finally close.
   - `_search_all` / `_list_all`: query, check empty, build header+separator, loop with identical formatting, strip trailing blank, join.
   - `_search_by_project` / `_list_by_project`: find project, check None, get project_id, query, check empty, build header+separator, loop, strip, join.
   - Per-item formatting: `#{aid}  {title}`, `{link}`, `{proj_label} | {date}` or `{date}`.

   The only differences are:
   - The DB functions called (list vs search).
   - The header text (`저장된 메세지` vs `검색 결과`).
   - The empty-state messages.
   - `_search_all`/`_search_by_project` receive an additional `keyword` parameter.

   This is not blocking for 89 lines of code, but as more commands follow this pattern, the duplication will become a maintenance burden. A shared formatting helper (as proposed in ISSUE-FOLLOW-017 from the ISSUE-007 review) would reduce this.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_search.py` (entire file)
   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_list.py` (entire file)

8. **Missing test: LIKE wildcard injection behavior**

   No test verifies what happens when the keyword contains `%` or `_`. Adding a test that searches for `"%"` and documents the (broad-match) behavior would make the design decision explicit and prevent confusion in the future.

   **Recommended test:**
   ```python
   def test_search_percent_in_keyword(self, tmp_path, monkeypatch):
       db_path = _seed_db(tmp_path)
       monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)
       # '%' in keyword acts as LIKE wildcard, matching all titles.
       result = handle("%", _USER_A)
       assert "(3건)" in result  # matches all 3 archives for USER_A
   ```

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_search.py`

9. **Missing test: ordering verification**

   Same gap as noted in ISSUE-007 review. The SQL specifies `ORDER BY a.created_at DESC` but no test verifies the order of results. Since all seeded rows are inserted within the same second, `created_at` values are identical and SQLite's tiebreaker ordering is not guaranteed by spec (though in practice it follows rowid order).

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_search.py`

10. **`_USAGE` string is duplicated between `cmd_search.py` and `test_cmd_search.py`**

    The usage string `"사용법: /archive search <키워드> [/p <프로젝트>]"` is defined in both files. Same pattern as noted in ISSUE-006 review (suggestion #9). Consider importing from the module or using a looser assertion.

    **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/cmd_search.py` (line 13)
    **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_search.py` (line 12)

11. **Performance: `LIKE '%...%'` cannot use index prefix scans**

    As noted in the PR context, the `LIKE '%keyword%'` pattern with a leading wildcard prevents SQLite from using the `idx_archives_title` index for prefix optimization. This means a full table scan (filtered by `user_id` via `idx_archives_user`) is required for every search query. This is acceptable for the expected data volume (personal Slack archive, likely hundreds to low thousands of rows per user), but should be documented as a known limitation if the tool is ever used at larger scale.

    **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` (lines 116, 130)

12. **`tmp_path` type hint uses `object` instead of `pathlib.Path`**

    Consistent with all previous test files. Non-blocking.

    **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/tests/test_cmd_search.py` (multiple methods)

### Follow-up Issues

- **ISSUE-FOLLOW-018:** Escape LIKE wildcard characters (`%`, `_`) in search keyword using SQLite's `ESCAPE` clause, or document the current broad-match behavior as intentional.
- **ISSUE-FOLLOW-019:** Extract shared formatting logic from `cmd_list.py` and `cmd_search.py` into a common helper module (extends ISSUE-FOLLOW-017).
- **ISSUE-FOLLOW-020:** Add ordering verification tests for search results using explicit `created_at` values (extends ISSUE-FOLLOW-016).

---

## Security Findings

### Summary

No Critical or High severity issues found. All SQL queries use parameterized binding. One Medium-Low finding regarding LIKE wildcard characters in user input, which affects search precision but does not create a data leak or injection vulnerability.

### Detailed Assessment

| # | Severity | Category | Finding | Status |
|---|----------|----------|---------|--------|
| S-1 | **Pass** | SQL Injection | Both `search_archives` and `search_archives_by_project` use `?` parameterized placeholders for all user-supplied values (`user_id`, `project_id`, keyword-based LIKE pattern). The LIKE pattern is constructed as `f"%{keyword}%"` in Python and bound as a parameter -- the `%` wildcards are part of the bound value, not interpolated into SQL text. No string formatting or concatenation in SQL construction. Verified in `/Users/pillip/project/practice/openclaw_archiver_plugin/src/openclaw_archiver/db.py` lines 108-133. | Pass |
| S-2 | **Low** | Input validation | **LIKE wildcard characters not escaped.** User-supplied `%` and `_` characters in the keyword are passed through to the LIKE pattern, causing them to act as SQL wildcards. A search for `%` matches all titles; `_` matches any single character. This does NOT leak data across users (the `user_id = ?` filter is always enforced), so it only affects the searching user's result precision. The fix is to escape these characters using `ESCAPE '\'` clause. Classified as Low because there is no cross-user data exposure, no injection, and the impact is limited to slightly broader search results. | Open |
| S-3 | **Pass** | Authorization | Data isolation is correctly enforced. Both search queries filter by `a.user_id = ?`. The project-scoped query additionally filters by `a.project_id = ?`, and the project itself is resolved via `find_project(conn, user_id, project_name)` which filters by `user_id`. Test `test_search_excludes_other_user` (line 44) verifies that User A cannot see User B's archives. | Pass |
| S-4 | **Pass** | Connection management | `try/finally` pattern ensures connection is always closed. Connection is only opened after input validation. No connection leak possible. | Pass |
| S-5 | **Pass** | Information disclosure | Error messages reveal only the keyword and project name the user typed. No internal paths, SQL errors, or stack traces are exposed. User-supplied values are echoed back in plain text, which is safe in Slack's rendering context. | Pass |
| S-6 | **Pass** | XSS | All output is plain text returned to Slack. No HTML generation. User-supplied `keyword`, `title`, `link`, and `project_name` values are included via f-strings in plain text context. Slack handles rendering safely. | Pass |
| S-7 | **Pass** | Sensitive data | No hardcoded secrets, API keys, credentials, or file paths in any of the three files reviewed. | Pass |
| S-8 | **Pass** | Dependencies | No new runtime or dev dependencies added. | Pass |

---

## Verdict

**Approve.** No blocking issues. All 115 tests pass (12 new + 103 existing). All acceptance criteria are met. SQL queries use parameterized binding correctly. `COLLATE NOCASE` provides case-insensitive search as specified. Connection management follows the established `try/finally` pattern. Data isolation between users is enforced and tested. One Low severity security finding (LIKE wildcard characters not escaped) is documented with a follow-up issue. The code closely mirrors `cmd_list.py` in structure, which is both a strength (consistency) and a weakness (duplication) -- a shared formatting helper is proposed as a follow-up. Three follow-up issues proposed.

---
---

# Review Notes -- ISSUE-010 Remove Command Handler PR

**Reviewer:** Senior Code Review Agent
**Date:** 2026-03-03
**Branch:** `issue/ISSUE-010-cmd-remove`
**Files changed:** 3 (cmd_remove.py: 37 lines, db.py: +10 lines, test_cmd_remove.py: 88 lines)

---

## Code Review

### Spec Compliance

**Acceptance Criteria verification:**
- `/archive remove <ID>` deletes the archive and returns success with ID and title -- covered by `test_remove_success` (line 27) and `test_remove_response_includes_title` (line 49).
- Row is actually deleted from the database -- covered by `test_remove_deletes_from_db` (line 36).
- Attempting to delete another user's archive returns not-found (FR-019 data isolation) -- covered by `test_remove_other_user_message` (line 61).
- Nonexistent ID returns not-found -- covered by `test_remove_nonexistent_id` (line 69).
- Non-numeric ID returns usage error -- covered by `test_remove_non_numeric_id` (line 77).
- Empty/whitespace args returns usage -- covered by `test_remove_empty_args` (line 81) and `test_remove_whitespace_only` (line 85).

All acceptance criteria are met.

**Pattern consistency with cmd_edit.py:** The handler follows the same structure as `cmd_edit.py` -- parse args, validate ID, open connection with `try/finally`, check ownership via `get_archive_title`, perform mutation, return formatted response. The TOCTOU pattern is correctly handled: `delete_archive` returns a boolean, and its return value is checked (line 30-31). This is actually more robust than `cmd_edit.py`, which does NOT check the return value of `update_archive_title`.

**SQL pattern:** `DELETE FROM archives WHERE id = ? AND user_id = ?` uses parameterized queries and includes the `user_id` filter for authorization. Correct.

### Blocking Issues

None. All 132 tests pass (8 new + 124 existing).

### Suggestions (non-blocking)

1. **TOCTOU window between `get_archive_title` and `delete_archive` is mitigated but not eliminated**

   The handler calls `get_archive_title` (line 26) to fetch the title for the success response, then calls `delete_archive` (line 30) which also checks ownership. If the row is deleted by another concurrent request between these two calls, `delete_archive` returns `False` and the not-found message is returned. This is correct and safe.

   However, note that the `get_archive_title` call is redundant from a correctness standpoint -- it exists solely to retrieve the title for the success message. An alternative would be to have `delete_archive` return the deleted row's title (using `RETURNING` clause in SQLite 3.35+ or a SELECT-then-DELETE in a single transaction). This would eliminate one DB round-trip and close the TOCTOU window entirely. Non-blocking since the current approach handles the race correctly.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-010-cmd-remove/src/openclaw_archiver/cmd_remove.py` (lines 26-31)

2. **Missing test: args with leading/trailing spaces around ID like `"  1  "`**

   The handler calls `args.strip()` at line 14 and then `int(stripped)` at line 20. `int("  1  ")` would raise a `ValueError` because `stripped` has already been stripped. Wait -- actually `"  1  ".strip()` produces `"1"`, then `int("1")` succeeds. So this case works correctly. However, `"1 2"` would pass `int("1 2")` which raises `ValueError` and returns the `_BAD_ID` message. This is reasonable behavior (reject malformed input), but no test documents it. A test for `handle("1 2", user)` would clarify that extra tokens after the ID are treated as invalid.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-010-cmd-remove/tests/test_cmd_remove.py`

3. **Missing test: negative ID**

   `handle("-1", user_id)` would parse as `int(-1)` successfully, then query the database for `id = -1` which would not exist, returning the not-found message. This is correct behavior, but a test documenting it would strengthen coverage.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-010-cmd-remove/tests/test_cmd_remove.py`

4. **Missing test: zero ID**

   Similar to negative ID. `handle("0", user_id)` would query for `id = 0`. SQLite autoincrement starts at 1, so this would return not-found. Correct behavior, but untested.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-010-cmd-remove/tests/test_cmd_remove.py`

5. **`_USAGE` string is duplicated between `cmd_remove.py` and `test_cmd_remove.py`**

   Same pattern noted in ISSUE-006 and ISSUE-008 reviews. The usage string `"사용법: /archive remove <ID>"` is defined in both files. Consider importing from the module to prevent drift.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-010-cmd-remove/src/openclaw_archiver/cmd_remove.py` (line 7)
   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-010-cmd-remove/tests/test_cmd_remove.py` (line 12)

6. **`test_remove_response_includes_title` is fully redundant with `test_remove_success`**

   `test_remove_success` (line 27) asserts both `"삭제했습니다. (ID: 1)"` and `"스프린트 회의록 (3월)"` in the result. `test_remove_response_includes_title` (line 49) asserts only the title string. The latter is a strict subset of the former's assertions. Not harmful, but it adds no additional coverage.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-010-cmd-remove/tests/test_cmd_remove.py` (lines 49-55)

7. **`tmp_path` type hint uses `object` instead of `pathlib.Path`**

   Consistent with all previous test files. Non-blocking.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-010-cmd-remove/tests/test_cmd_remove.py` (multiple methods)

### Follow-up Issues

- **ISSUE-FOLLOW-021:** Consider having `delete_archive` return the deleted title (via `RETURNING` or SELECT-before-DELETE) to eliminate the TOCTOU window and extra DB call.
- **ISSUE-FOLLOW-022:** Add edge-case tests for remove command: `"1 2"` (extra tokens), `"-1"` (negative ID), `"0"` (zero ID).
- **ISSUE-FOLLOW-023:** Note that `cmd_edit.py` does NOT check the return value of `update_archive_title` -- unlike this PR which correctly checks `delete_archive`'s return. The edit handler should be updated to check the mutation result for TOCTOU consistency.

---

## Security Findings

### Summary

No Critical or High severity issues found. The handler correctly enforces ownership via `user_id` filtering in both the title lookup and the delete query. The same error message is returned for both "not found" and "not owned" cases, preventing enumeration of other users' archive IDs (FR-019).

### Detailed Assessment

| # | Severity | Category | Finding | Status |
|---|----------|----------|---------|--------|
| S-1 | **Pass** | SQL Injection | `delete_archive` uses `DELETE FROM archives WHERE id = ? AND user_id = ?` with parameterized `?` placeholders. `get_archive_title` uses `SELECT title FROM archives WHERE id = ? AND user_id = ?`. No string formatting or concatenation. Both verified in `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-010-cmd-remove/src/openclaw_archiver/db.py` lines 136-168. | Pass |
| S-2 | **Pass** | Authorization | Data isolation is correctly enforced. Both `get_archive_title` and `delete_archive` filter by `user_id = ?`. A user cannot delete another user's archive. Test `test_remove_other_user_message` (line 61) verifies this. The error message for unauthorized access is identical to the not-found message (`해당 메세지를 찾을 수 없습니다.`), preventing ID enumeration attacks. | Pass |
| S-3 | **Pass** | Connection management | `try/finally` pattern ensures connection is always closed, even if `delete_archive` raises an exception. Connection is opened only after input validation succeeds. No connection leak possible. | Pass |
| S-4 | **Pass** | Information disclosure | Error messages reveal only the ID the user typed. No internal paths, SQL errors, stack traces, or information about whether the ID exists but belongs to another user. | Pass |
| S-5 | **Pass** | Input validation | Non-numeric IDs are rejected before any DB call is made. Empty and whitespace-only inputs return usage message. `int()` parsing prevents injection of non-integer values into the SQL parameter. | Pass |
| S-6 | **Pass** | Sensitive data | No hardcoded secrets, API keys, credentials, or file paths in any of the three files reviewed. | Pass |
| S-7 | **Pass** | Dependencies | No new runtime or dev dependencies added. | Pass |

---

## Verdict

**Approve.** No blocking issues. All 132 tests pass (8 new + 124 existing). All acceptance criteria are met. The handler correctly follows the established `cmd_edit.py` pattern with one improvement: it checks the return value of the mutation function (`delete_archive`) for TOCTOU safety. SQL uses parameterized queries. Authorization is enforced via `user_id` filtering with uniform error messages to prevent enumeration. Connection management is correct with `try/finally`. Seven non-blocking suggestions documented, primarily around missing edge-case tests and minor redundancy. Three follow-up issues proposed.

---
---

# Review Notes -- ISSUE-011 Project List Command Handler PR

**Reviewer:** Senior Code Review Agent
**Date:** 2026-03-03
**Branch:** `issue/ISSUE-011-cmd-project-list`
**Files changed:** 3 (cmd_project_list.py: 31 lines, db.py: +16 lines, test_cmd_project_list.py: 89 lines)

---

## Code Review

### Spec Compliance

**Acceptance Criteria verification:**
- `/archive project list` returns header with project count -- covered by `test_lists_projects_with_counts` (line 42).
- Each project shows name and archive count -- covered by `test_lists_projects_with_counts` (lines 43-46).
- Data isolation: user only sees own projects -- covered by `test_excludes_other_user_projects` (line 55) and `test_user_b_sees_own_projects` (lines 63-65).
- Empty state returns guidance message with `/archive save` example -- covered by `test_empty_projects` (lines 87-88).
- Separator in output -- covered by `test_header_contains_separator` (line 73).

All acceptance criteria are met.

**UX Spec response format (Section 3.6):** Verified against spec.
- Header: `프로젝트 ({count}개)` with no leading indent -- matches spec.
- Separator: 8-space indent + full-width dashes -- matches spec.
- Items: 8-space indent + `{name}     {count}건` -- matches spec format.
- Empty state: message matches spec exactly.

**SQL query pattern:** Verified.
- `SELECT p.name, COUNT(a.id) AS archive_count FROM projects p LEFT JOIN archives a ON p.id = a.project_id AND a.user_id = ? WHERE p.user_id = ? GROUP BY p.id, p.name ORDER BY p.name` -- correct and well-structured.

### Blocking Issues

None. All 137 tests pass (5 new + 132 existing).

### Findings

1. **SQL LEFT JOIN is correct and well-designed**

   The `list_projects` query uses `LEFT JOIN archives a ON p.id = a.project_id AND a.user_id = ?` with the `a.user_id` filter in the JOIN condition rather than the WHERE clause. This is the correct approach: placing `a.user_id = ?` in the JOIN ensures that only the requesting user's archives are counted, while the LEFT JOIN still returns projects that have zero matching archives (with `COUNT(a.id) = 0`). If `a.user_id = ?` were in the WHERE clause instead, projects with no archives would be filtered out entirely because the LEFT JOIN would produce NULL for `a.user_id`, which would fail the equality check.

   The `WHERE p.user_id = ?` correctly restricts the results to the requesting user's projects only.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-011-cmd-project-list/src/openclaw_archiver/db.py` (lines 178-186)

2. **Connection management follows established pattern**

   `cmd_project_list.handle()` uses `try/finally` to ensure `conn.close()` is always called, consistent with `cmd_save`, `cmd_list`, `cmd_search`, `cmd_edit`, and `cmd_remove`. This is the correct pattern.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-011-cmd-project-list/src/openclaw_archiver/cmd_project_list.py` (lines 17-30)

3. **`args` parameter is correctly ignored**

   The `handle` function accepts `args` for interface consistency with other command handlers but does not use it. This is correct -- `project list` takes no arguments per the spec.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-011-cmd-project-list/src/openclaw_archiver/cmd_project_list.py` (line 15)

4. **`GROUP BY p.id, p.name` is correct and defensive**

   Grouping by both `p.id` (primary key) and `p.name` is technically redundant since `p.id` is unique, but it is defensive and compatible with stricter SQL modes. SQLite does not require it, but including both columns documents the intent clearly.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-011-cmd-project-list/src/openclaw_archiver/db.py` (line 183)

### Suggestions (non-blocking)

5. **Missing test: project with zero archives**

   The test suite seeds the database with projects that all have at least one archive. There is no test verifying that a project with zero archives displays `0건` in the output. While the SQL is correct (the LEFT JOIN + COUNT pattern handles this), an explicit test would document this behavior and prevent regressions.

   The `list_projects` SQL would correctly return `(name, 0)` for a project with no archives, but no test verifies this path through the handler's formatting logic (specifically that `f"{name}     {count}건"` renders `"ProjectName     0건"`).

   **Recommended test:**
   ```python
   def test_project_with_zero_archives(self, tmp_path, monkeypatch):
       db_path = os.path.join(str(tmp_path), "test.sqlite3")
       conn = get_connection(db_path)
       get_or_create_project(conn, _USER_A, "EmptyProject")
       conn.close()
       monkeypatch.setenv("OPENCLAW_ARCHIVER_DB_PATH", db_path)
       result = handle("", _USER_A)
       assert "프로젝트 (1개)" in result
       assert "EmptyProject" in result
       assert "0건" in result
   ```

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-011-cmd-project-list/tests/test_cmd_project_list.py`

6. **Sort order is alphabetical by name -- spec is ambiguous**

   The SQL uses `ORDER BY p.name` (alphabetical ascending). The UX spec example shows `Backend / HR / Frontend` which is NOT alphabetical (Frontend would come before HR). This suggests the spec example was not meant to define sort order. Alphabetical is a reasonable default. However, if the spec intended sorting by archive count descending (most active projects first), the SQL would need `ORDER BY archive_count DESC, p.name`. This is a product decision, not a code bug.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-011-cmd-project-list/src/openclaw_archiver/db.py` (line 184)

7. **`test_excludes_other_user_projects` is a weak test**

   `test_excludes_other_user_projects` (line 48) only asserts `"프로젝트 (2개)"` -- the same assertion as `test_lists_projects_with_counts`. It does not verify the *absence* of User B's data. A stronger assertion would be to check that User B's unique archive title (`"B의 메시지"`) does NOT appear in User A's results. However, since User B also has a "Backend" project, the test would need to verify archive counts rather than project names. The current test provides some coverage through the count, but it is partially redundant.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-011-cmd-project-list/tests/test_cmd_project_list.py` (lines 48-55)

8. **`tmp_path` type hint uses `object` instead of `pathlib.Path`**

   Consistent with all previous test files. Non-blocking.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-011-cmd-project-list/tests/test_cmd_project_list.py` (multiple methods)

9. **`_seed_db` type hint uses `object` for `tmp_path` parameter**

   Same as above. The helper function at line 14 declares `tmp_path: object`. Non-blocking.

   **File:** `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-011-cmd-project-list/tests/test_cmd_project_list.py` (line 14)

### Follow-up Issues

- **ISSUE-FOLLOW-024:** Add a test for projects with zero archives to verify the `0건` display path.
- **ISSUE-FOLLOW-025:** Confirm with product whether project list should be sorted alphabetically (`ORDER BY p.name`) or by activity (`ORDER BY archive_count DESC`).
- **ISSUE-FOLLOW-026:** Strengthen `test_excludes_other_user_projects` to assert the absence of cross-user data, not just the count.

---

## Security Findings

### Summary

No Critical or High severity issues found. The SQL query uses parameterized binding for both parameters. Data isolation between users is correctly enforced via `WHERE p.user_id = ?` and the JOIN condition `a.user_id = ?`.

### Detailed Assessment

| # | Severity | Category | Finding | Status |
|---|----------|----------|---------|--------|
| S-1 | **Pass** | SQL Injection | `list_projects` uses `?` parameterized placeholders for both `user_id` bindings. No string formatting or concatenation in SQL construction. Verified in `/Users/pillip/project/practice/openclaw_archiver_plugin/.worktrees/issue-ISSUE-011-cmd-project-list/src/openclaw_archiver/db.py` lines 178-186. | Pass |
| S-2 | **Pass** | Authorization | Data isolation is enforced at two levels: (1) `WHERE p.user_id = ?` restricts projects to the requesting user, (2) `a.user_id = ?` in the JOIN condition restricts archive counts to the requesting user's archives. Even if a project_id is shared across users (it is not, due to `UNIQUE(user_id, name)` constraint), the count would only reflect the requesting user's archives. Tests `test_excludes_other_user_projects` and `test_user_b_sees_own_projects` verify isolation. | Pass |
| S-3 | **Pass** | Connection management | `try/finally` pattern ensures connection is always closed. No connection leak possible. | Pass |
| S-4 | **Pass** | Information disclosure | The empty-state message reveals the `/archive save` command syntax, which is acceptable user guidance. No internal paths, SQL errors, or stack traces are exposed. | Pass |
| S-5 | **Pass** | Input validation | The `args` parameter is unused, so there is no user input to validate beyond `user_id`, which is passed through from the dispatcher (not user-controlled Slack message text). No attack surface via `args`. | Pass |
| S-6 | **Pass** | XSS | All output is plain text returned to Slack. Project names are user-supplied (created via `/archive save ... /p <name>`) and echoed back via f-strings in plain text. Slack handles rendering safely. | Pass |
| S-7 | **Pass** | Sensitive data | No hardcoded secrets, API keys, credentials, or file paths in any of the three files reviewed. | Pass |
| S-8 | **Pass** | Dependencies | No new runtime or dev dependencies added. | Pass |

---

## Verdict

**Approve.** No blocking issues. All 137 tests pass (5 new + 132 existing). All acceptance criteria are met. The SQL query is well-designed: the LEFT JOIN with the `user_id` condition in the JOIN clause correctly counts archives per project while preserving projects with zero archives. Parameterized queries prevent SQL injection. Data isolation is enforced and tested. Connection management follows the established `try/finally` pattern. The handler is minimal at 31 lines and follows existing codebase conventions. Five non-blocking suggestions documented, primarily around missing edge-case test coverage (zero-archive projects) and a weak isolation test. Three follow-up issues proposed.
