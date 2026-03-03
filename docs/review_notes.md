# PR #30 Review -- ISSUE-015: HTTP Bridge Server

**Reviewer**: Claude Opus 4.6 (automated)
**Date**: 2026-03-03
**Files reviewed**:
- `src/openclaw_archiver/server.py` (NEW)
- `src/openclaw_archiver/__main__.py` (NEW)
- `tests/test_server.py` (NEW)

**Test status**: 10/10 passing after applied fixes.

---

## Code Review

### Overall Assessment

The implementation is clean, minimal, and well-structured. It uses only stdlib
(`http.server`, `json`, `os`), which aligns with the project's zero-dependency
constraint. The handler class is private (`_Handler`), routing is explicit, and
error responses are consistent. The test suite covers the happy path, validation
errors, invalid JSON, and 404 routes.

### Findings

#### CR-1: Bare `except Exception` swallows errors silently (Blocking)

**File**: `src/openclaw_archiver/server.py`, lines 79-83

```python
except Exception:
    self._send_json(500, {
        "ok": False,
        "error": "internal server error",
    })
```

Combined with `log_message` being suppressed (line 93), exceptions from
`handle_message` vanish entirely. In production this makes debugging impossible.

**Recommendation**: At minimum, log the traceback to stderr via `logging` or
`traceback.print_exc()`. The suppressed `log_message` only affects the HTTP
access log lines from `BaseHTTPRequestHandler`, so adding a separate `logging`
call is compatible.

**Proposed follow-up**: Add `import logging` and `logger.exception(...)` inside
the except block.

---

#### CR-2: `log_message` override suppresses all access logging (Suggestion)

**File**: `src/openclaw_archiver/server.py`, line 93

The no-op override is fine for tests, but in production there is no visibility
into what requests hit the server. Consider making this configurable via an
environment variable (e.g., `OPENCLAW_ARCHIVER_LOG_LEVEL`) or using Python's
`logging` module with a configurable level instead of suppressing unconditionally.

**Proposed follow-up issue**: Make server logging configurable.

---

#### CR-3: Truthiness check on `message` rejects empty strings but also `0` (Suggestion)

**File**: `src/openclaw_archiver/server.py`, line 66

```python
if not message or not user_id:
```

Since both fields are expected to be strings, this is fine in practice. However,
if someone sends `{"message": "", "user_id": "U1"}`, the error says "message and
user_id are required" rather than "message must not be empty." This is a minor
UX issue with the error message, not a bug.

---

#### CR-4: Port parsing has no error handling (Suggestion)

**File**: `src/openclaw_archiver/server.py`, line 99

```python
port = int(os.environ.get("OPENCLAW_ARCHIVER_PORT", _DEFAULT_PORT))
```

If `OPENCLAW_ARCHIVER_PORT` is set to a non-numeric value, `int()` raises a bare
`ValueError` with no user-friendly message. Consider wrapping with a try/except
that prints a clear error.

---

#### CR-5: Test version assertion is hardcoded (Suggestion)

**File**: `tests/test_server.py`, line 72

```python
assert data["version"] == "0.1.0"
```

This will break on every version bump. Better to import `__version__` and
compare against it:

```python
from openclaw_archiver import __version__
assert data["version"] == __version__
```

---

#### CR-6: Missing test for the 413 body-size limit (Suggestion)

After the applied fix adding `_MAX_BODY_BYTES`, there is no test exercising the
413 path. A test should send a body larger than 1 MiB (or monkeypatch the
constant to a small value) and assert 413 status.

---

#### CR-7: Missing test for `__main__.py` (Suggestion)

The `__main__.py` module is trivial but has no test coverage. A minimal test
confirming `main` is callable and that the module can be imported would prevent
regressions.

---

#### CR-8: No HTTP method restriction beyond GET and POST (Info)

`BaseHTTPRequestHandler` will return a 501 for unsupported methods (PUT, DELETE,
PATCH, etc.) by default, which is acceptable behavior for this use case. No
action needed.

---

## Security Findings

### HIGH -- S-1: No request body size limit (DoS) -- FIXED

**File**: `src/openclaw_archiver/server.py`, original lines 37-38
**Impact**: A malicious client (or misconfigured caller) could send a request
with `Content-Length: 9999999999`. The server would call `self.rfile.read(length)`
and attempt to allocate that much memory, causing out-of-memory / process crash.
Even though the server binds to localhost only, any process on the same machine
(or any machine that can reach localhost via forwarding) could trigger this.

**Fix applied**: Added `_MAX_BODY_BYTES = 1_048_576` (1 MiB) constant and a
guard that returns HTTP 413 if `Content-Length` exceeds the limit. The
`Content-Length` parsing was also separated into its own try/except for clarity.

**Verification**: All 10 existing tests pass after the fix.

---

### MEDIUM -- S-2: Bare `except Exception` hides security-relevant errors

**File**: `src/openclaw_archiver/server.py`, lines 79-83
**Impact**: If `handle_message` raises an exception due to SQL injection
attempts, path traversal in arguments, or other malicious input, the error is
silently swallowed. This makes it impossible to detect attacks via log analysis
or monitoring. The 500 response is correct, but the lack of logging is the
concern.

**Remediation**: Add `logging.exception("handle_message failed")` inside the
except block. Do NOT expose the exception message in the HTTP response (the
current "internal server error" response text is correct).

---

### MEDIUM -- S-3: No rate limiting on the HTTP endpoint

**Impact**: The `http.server` module creates a new thread per request (or
handles them sequentially depending on configuration). A local attacker could
flood the server with rapid requests to exhaust threads or starve the event
loop.

**Mitigation**: This is localhost-only, so the attack surface is limited to
processes already running on the host. For a plugin bridge this is acceptable
risk. If the server is ever exposed beyond localhost, rate limiting would be
required.

**Remediation**: Document that this server MUST NOT be exposed to a network
interface. No code change needed at this time.

---

### LOW -- S-4: `self.path` may contain query strings or fragments

**File**: `src/openclaw_archiver/server.py`, lines 20, 30
**Impact**: A request to `/health?foo=bar` or `/message?x=1` would not match
the exact string comparison and would return 404. This is actually safe
(fail-closed), but it could be confusing. If query parameter support is ever
needed, `urllib.parse.urlparse` should be used.

**Remediation**: No action needed unless query parameter support is required.

---

### LOW -- S-5: `OPENCLAW_ARCHIVER_PORT` environment variable is not validated

**File**: `src/openclaw_archiver/server.py`, line 99
**Impact**: Setting the env var to a privileged port (e.g., `80`) or an invalid
value could cause confusing errors. Setting it to `0` would bind to a random
port, which may be unintended.

**Remediation**: Add validation: port must be an integer in range 1024-65535
(or 1-65535 if running as root is acceptable). Provide a clear error message on
failure.

---

### INFO -- S-6: Server binds to 127.0.0.1 only (Good)

The server correctly binds to `127.0.0.1` rather than `0.0.0.0`. This limits
the attack surface to localhost. This is the correct default for a plugin bridge.

---

## Summary

| Category | Count | Status |
|----------|-------|--------|
| Blocking code issues | 1 (CR-1) | Needs fix before merge |
| Applied security fixes | 1 (S-1) | Fixed in this review |
| Medium security findings | 2 (S-2, S-3) | Document / follow-up |
| Low security findings | 2 (S-4, S-5) | Acceptable risk |
| Suggestions | 5 (CR-2 to CR-7) | Follow-up issues |

**Verdict**: The PR is in good shape overall. One blocking issue remains
(CR-1 / S-2: bare except with no logging). After that fix, this is ready to
merge. The body-size DoS (S-1) has been fixed in this review pass.
