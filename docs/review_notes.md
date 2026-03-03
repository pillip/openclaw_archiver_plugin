# Code Review: test_isolation.py

**PR**: #32 - ISSUE-016: 데이터 격리 통합 테스트 작성
**Reviewer**: Claude Code
**Date**: 2026-03-03
**Test Status**: All 18 tests PASS

---

## Code Review

### Overall Assessment

**APPROVED with recommendations**

The test suite successfully validates user_id-based data isolation across all commands. Tests are well-structured, organized by command category, and follow consistent patterns. All 18 tests pass.

### Strengths

1. **Comprehensive coverage**: Tests cover all 8 commands mentioned in PRD
   - List (all + by project)
   - Search (all + by project)
   - Edit
   - Remove
   - Project list
   - Project rename
   - Project delete

2. **Security-focused test cases**: Tests verify that error messages for "other user's data" match "non-existent data" errors (preventing information disclosure)

3. **Data integrity tests**: Tests verify that failed cross-user operations don't modify data (edit/remove/rename/delete)

4. **Clean test organization**: Tests grouped by command category in classes with descriptive names

5. **Shared fixture**: `_isolation_db` fixture seeds test data consistently for all tests

6. **Clear naming**: Test method names clearly describe what isolation boundary is being tested

### Issues Found

#### Medium Severity

**M1: Missing `/archive save` cross-user isolation test**

- **What's missing**: No test verifies that User B cannot save messages to User A's projects
- **Why it matters**: The save command with `/p <project>` uses `get_or_create_project()`, which creates projects if they don't exist. However, this is user-scoped, so User B creating a project with the same name as User A's project is actually correct behavior (projects are scoped by `(user_id, name)` pair per PRD).
- **Recommendation**: Add a test to document this behavior explicitly:
  ```python
  def test_user_b_can_create_project_with_same_name_as_user_a(self) -> None:
      """Each user can have their own project with the same name."""
      # User A already has '앨리스프로젝트', User B creates their own with same name
      resp = handle_message("/archive save 밥메모2 https://slack.com/b/2 /p 앨리스프로젝트", _USER_B)
      assert resp is not None and "저장했습니다" in resp

      # Both users should see only their own project
      a_list = handle_message("/archive project list", _USER_A)
      b_list = handle_message("/archive project list", _USER_B)

      # Both have a project named '앨리스프로젝트' but they're different projects
      assert "앨리스프로젝트" in a_list
      assert "앨리스프로젝트" in b_list

      # User A's project has 1 message, User B's has 1 message (different messages)
      a_proj_list = handle_message("/archive list /p 앨리스프로젝트", _USER_A)
      assert "프로젝트메모" in a_proj_list
      assert "밥메모2" not in a_proj_list
  ```
- **Severity**: Medium (not a security issue, but missing test coverage for expected behavior)

**M2: No test for project rename collision with other user's project**

- **What's missing**: No test verifies behavior when User B tries to rename their project to a name already used by User A
- **Why it matters**: This should be ALLOWED since projects are scoped by `(user_id, name)`. The test suite doesn't document this edge case.
- **Recommendation**: Add a test:
  ```python
  def test_user_b_can_rename_project_to_same_name_as_user_a_project(self) -> None:
      """Users can have projects with the same name (scoped by user_id)."""
      # User B renames their project to same name as User A's project
      resp = handle_message("/archive project rename 밥프로젝트 앨리스프로젝트", _USER_B)
      assert resp is not None and "변경했습니다" in resp

      # Both users should have a project with this name
      a_list = handle_message("/archive project list", _USER_A)
      b_list = handle_message("/archive project list", _USER_B)
      assert "앨리스프로젝트" in a_list
      assert "앨리스프로젝트" in b_list
  ```
- **Severity**: Medium (edge case documentation gap)

#### Low Severity

**L1: Helper function `_get_first_id()` lacks error handling context**

- **Line**: 46-56
- **Issue**: `ValueError` message doesn't indicate which test failed or what the response contained
- **Recommendation**: Add test context to error message:
  ```python
  def _get_first_id(list_response: str, context: str = "") -> str:
      """Extract the first numeric ID from a list/search response.

      Args:
          list_response: Response text containing archive IDs
          context: Optional context for error messages (e.g., "test_user_b_edit")
      """
      for line in list_response.splitlines():
          stripped = line.strip()
          if stripped.startswith("#"):
              token = stripped.split()[0]  # "#1"
              return token.lstrip("#")
      ctx = f" in {context}" if context else ""
      raise ValueError(f"No ID found in response{ctx}: {list_response}")
  ```
- **Severity**: Low (test maintainability improvement)

**L2: Test fixture doesn't clean up database path from environment**

- **Line**: 16-22
- **Issue**: `monkeypatch.setenv()` persists for the entire test session due to `autouse=True`
- **Impact**: Minimal (pytest's monkeypatch automatically restores env vars after fixture scope)
- **Status**: Not an issue (monkeypatch handles cleanup automatically)

**L3: No test for empty string as user_id**

- **Issue**: Tests don't verify behavior when `user_id=""` is passed
- **Why it matters**: SQLite will treat empty string differently from other user_ids, potentially allowing cross-user data access
- **Recommendation**: Add a negative test:
  ```python
  def test_empty_user_id_does_not_see_data(self) -> None:
      """Empty user_id should not bypass isolation."""
      resp = handle_message("/archive list", "")
      assert resp is not None
      assert "앨리스메모" not in resp
      assert "밥메모" not in resp
  ```
- **Severity**: Low (unlikely real-world scenario, but good defensive test)

**L4: Test class docstrings could be more specific**

- **Issue**: Class docstrings repeat test names without adding context
- **Example**: `"""User B cannot see User A's messages via /archive list."""` could specify what isolation mechanism prevents this (user_id filtering in SQL WHERE clause)
- **Recommendation**: Enhance docstrings:
  ```python
  class TestListIsolation:
      """Verify that list command filters archives by user_id in SQL queries.

      All list_archives() and list_archives_by_project() queries in db.py
      include WHERE user_id = ? to enforce isolation.
      """
  ```
- **Severity**: Low (documentation improvement)

### Test Coverage Analysis

**Commands tested for isolation**:
- [x] `/archive list` (all + by project)
- [x] `/archive search` (all + by project)
- [x] `/archive edit`
- [x] `/archive remove`
- [x] `/archive project list`
- [x] `/archive project rename`
- [x] `/archive project delete`
- [ ] `/archive save` (partial - no explicit cross-user project test)

**Isolation vectors tested**:
- [x] Cross-user message visibility (list/search)
- [x] Cross-user message modification (edit)
- [x] Cross-user message deletion (remove)
- [x] Cross-user project visibility (project list)
- [x] Cross-user project modification (project rename)
- [x] Cross-user project deletion (project delete)
- [x] Error message consistency (no information disclosure)
- [x] Data integrity after failed operations
- [ ] Same-name project coexistence (User A and User B can have projects with same name)

### Recommendations

1. **Add missing tests** (M1, M2): Document that project names can collide across users
2. **Improve helper function** (L1): Add context parameter to `_get_first_id()`
3. **Add edge case test** (L3): Test empty user_id behavior
4. **Enhance documentation** (L4): Add implementation details to class docstrings

### Non-blocking suggestions

1. Consider adding a test that verifies the actual SQL queries (mock/spy on db calls) to ensure WHERE user_id clauses are present
2. Consider parametrized tests to reduce duplication between User A and User B test pairs
3. Consider adding a test that seeds 100+ messages to verify performance doesn't degrade

---

## Security Findings

### Summary

**Overall security posture: STRONG**

All critical isolation boundaries are properly tested. No vulnerabilities found in test coverage. Tests successfully verify that the implementation prevents unauthorized cross-user access.

### Security Test Coverage

#### High-Value Security Tests (Present)

**S1: Information disclosure prevention** ✓
- **Lines**: 127-145, 179-190
- **What's tested**: Error messages for "other user's ID" are identical to "non-existent ID"
- **Why it matters**: Prevents user enumeration attacks (User B can't discover which archive IDs belong to User A)
- **Status**: PASS - `test_edit_error_same_for_nonexistent_and_other_user` and `test_remove_error_same_for_nonexistent_and_other_user` verify this

**S2: Data modification prevention** ✓
- **Lines**: 146-160, 192-202
- **What's tested**: Failed cross-user operations don't modify data
- **Why it matters**: Ensures TOCTTOU (time-of-check-time-of-use) bugs don't exist
- **Status**: PASS - Tests verify data integrity after failed edit/remove/rename/delete

**S3: Project namespace isolation** ✓
- **Lines**: 78-82, 102-106
- **What's tested**: User B cannot list/search in User A's projects
- **Why it matters**: Projects are a secondary authorization boundary
- **Status**: PASS - Tests verify "찾을 수 없습니다" errors when accessing other user's projects

**S4: Read access isolation** ✓
- **Lines**: 67-77, 92-101
- **What's tested**: List and search commands filter by user_id
- **Why it matters**: Primary confidentiality control
- **Status**: PASS - No cross-user data leakage in list/search results

**S5: Write access isolation** ✓
- **Lines**: 116-126, 170-178, 231-237, 255-259
- **What's tested**: Edit, remove, rename, delete commands enforce user_id
- **Why it matters**: Primary integrity control
- **Status**: PASS - Cross-user modifications fail with "찾을 수 없습니다" error

### Security Gaps (Low Severity)

**SG1: No SQL injection test**

- **Impact**: Low (tests don't inject SQL, but implementation should be reviewed separately)
- **What's missing**: No test verifies that user-provided project names with SQL metacharacters don't break isolation
- **Recommendation**: Add a test:
  ```python
  def test_sql_injection_in_project_name_does_not_bypass_isolation(self) -> None:
      """Project names with SQL metacharacters should not break isolation."""
      # User B tries to inject SQL in project name
      malicious_name = "앨리스프로젝트' OR user_id='U_ISO_ALICE' --"
      resp = handle_message(f"/archive save 공격 https://evil.com /p {malicious_name}", _USER_B)
      assert resp is not None and "저장했습니다" in resp

      # User B should only see their own project (with escaped name)
      resp = handle_message("/archive project list", _USER_B)
      assert "앨리스프로젝트" not in resp or malicious_name in resp

      # User A's data should be unaffected
      a_list = handle_message("/archive list", _USER_A)
      assert "공격" not in a_list
  ```
- **Note**: The implementation uses parameterized queries (db.py uses `?` placeholders), so this is likely safe, but a test would document this protection
- **Severity**: Low (implementation appears safe, test would provide defense-in-depth verification)

**SG2: No test for concurrent operations**

- **Impact**: Low (WAL mode should handle this, but no test verifies it)
- **What's missing**: No test verifies that User A and User B can modify their own data concurrently without isolation failures
- **Recommendation**: Consider adding a concurrency test (out of scope for this PR, but document in follow-up issue)
- **Severity**: Low (SQLite WAL mode should handle this, but untested)

**SG3: No test for NULL or invalid user_id types**

- **Impact**: Low (implementation should validate this at plugin boundary)
- **What's missing**: No test verifies behavior when `user_id=None` or `user_id=123` (integer instead of string)
- **Recommendation**: Add a defensive test:
  ```python
  def test_none_user_id_does_not_bypass_isolation(self) -> None:
      """None user_id should not allow access to all users' data."""
      resp = handle_message("/archive list", None)  # type: ignore[arg-type]
      # Should either error or return empty list, but NOT return other users' data
      assert resp is not None
      assert "앨리스메모" not in resp
      assert "밥메모" not in resp
  ```
- **Severity**: Low (edge case, likely caught by type system)

### Security Best Practices (Already followed)

1. **Parameterized queries**: All db.py functions use `?` placeholders (verified in db.py review)
2. **Consistent error messages**: Tests verify no information disclosure via error messages
3. **Defense in depth**: Both primary key (archive_id) AND user_id checked in WHERE clauses
4. **Positive and negative tests**: Tests verify both "what should work" and "what should fail"

### Security Approval

**APPROVED**

The test suite provides strong evidence that the implementation correctly enforces user_id-based isolation. All critical isolation boundaries are tested. The identified security gaps (SG1-SG3) are low-severity defensive tests that would strengthen the suite but are not blockers.

---

## Action Items

### Blocking (must fix before merge)

None. All tests pass and core isolation is verified.

### Recommended (should add in this PR or follow-up)

1. **Add test M1**: Document that users can create projects with same names (scoped by user_id)
2. **Add test M2**: Document that project renames can collide across users
3. **Add test SG1**: Verify SQL injection in project names doesn't bypass isolation
4. **Add test L3**: Verify empty user_id doesn't bypass isolation

### Nice-to-have (follow-up issues)

1. **L1**: Add context parameter to `_get_first_id()` for better error messages
2. **L4**: Enhance class docstrings with implementation details
3. **SG2**: Add concurrency tests for WAL mode
4. **SG3**: Add tests for invalid user_id types (None, int, etc.)
5. Consider parametrizing duplicate test pairs (User A/User B symmetry)
6. Consider adding performance tests for large datasets

---

## Conclusion

The test suite is well-designed and provides strong confidence that the data isolation implementation is correct. All 18 tests pass. The identified gaps are primarily documentation and edge-case coverage improvements, not security vulnerabilities.

The test suite successfully validates the core security requirement from PRD section 7 (Data Isolation): "All queries include user_id conditions and there is no path to access other users' data."

**Overall Grade**: A- (Excellent core coverage, minor documentation and edge-case gaps)
