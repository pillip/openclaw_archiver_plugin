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
