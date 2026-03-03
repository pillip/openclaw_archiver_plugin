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
