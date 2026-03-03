# STATUS: OpenClaw Archiver Plugin

## Current Milestone

Slack 메세지 링크를 개인별로 격리하여 저장·관리하는 OpenClaw 플러그인 v0.1.0 개발

## Issue Summary

| 구분 | 수량 |
|------|------|
| 전체 이슈 | 17 |
| P0 (Must) | 8 |
| P1 (Should) | 9 |
| 총 견적 | 13.5d |

### Track별 분포

| Track | 이슈 수 |
|-------|---------|
| Foundation (스캐폴딩, 스키마, DB) | 3 |
| Infrastructure (파서, 디스패처) | 2 |
| Core Commands | 9 |
| Integration (HTTP 브릿지) | 1 |
| Quality (격리 테스트, UX 검증) | 2 |

## Key Risks

| Risk | 영향 | 대응 |
|------|------|------|
| R-002: title 공백 파싱 | 높음 | URL 먼저 추출 → /p 분리 → 나머지 = title |
| R-001: /p 옵션 파싱 충돌 | 중간 | /p를 문자열 끝에서만 인식 |
| R-005: HTTP 브릿지 user_id 위조 | 중간 | localhost 바인딩 |

## Completed

- **ISSUE-001** (P0): 프로젝트 스캐폴딩 — [PR #2](https://github.com/pillip/openclaw_archiver_plugin/pull/2)
- **ISSUE-002** (P0): DB 스키마/마이그레이션 — [PR #4](https://github.com/pillip/openclaw_archiver_plugin/pull/4)
- **ISSUE-003** (P0): DB 연결 관리 — [PR #6](https://github.com/pillip/openclaw_archiver_plugin/pull/6)
- **ISSUE-004** (P0): 입력 파서 모듈 — [PR #8](https://github.com/pillip/openclaw_archiver_plugin/pull/8)
- **ISSUE-005** (P0): 디스패처 및 플러그인 진입점 — [PR #10](https://github.com/pillip/openclaw_archiver_plugin/pull/10)
- **ISSUE-006** (P0): save 명령 핸들러 — [PR #12](https://github.com/pillip/openclaw_archiver_plugin/pull/12)
- **ISSUE-007** (P0): list 명령 핸들러 — [PR #14](https://github.com/pillip/openclaw_archiver_plugin/pull/14)
- **ISSUE-008** (P1): search 명령 핸들러 — [PR #16](https://github.com/pillip/openclaw_archiver_plugin/pull/16)
- **ISSUE-009** (P1): edit 명령 핸들러 — [PR #18](https://github.com/pillip/openclaw_archiver_plugin/pull/18)
- **ISSUE-010** (P0): remove 명령 핸들러 — [PR #20](https://github.com/pillip/openclaw_archiver_plugin/pull/20)
- **ISSUE-011** (P1): project list 명령 핸들러 — [PR #22](https://github.com/pillip/openclaw_archiver_plugin/pull/22)
- **ISSUE-012** (P1): project rename 명령 핸들러 — [PR #24](https://github.com/pillip/openclaw_archiver_plugin/pull/24)
- **ISSUE-013** (P1): project delete 명령 핸들러 — [PR #26](https://github.com/pillip/openclaw_archiver_plugin/pull/26)
- **ISSUE-014** (P1): help 명령 핸들러 — [PR #28](https://github.com/pillip/openclaw_archiver_plugin/pull/28)
- **ISSUE-015** (P1): HTTP 브릿지 서버 구현 — [PR #30](https://github.com/pillip/openclaw_archiver_plugin/pull/30)
- **ISSUE-016** (P0): 데이터 격리 통합 테스트 작성 — [PR #32](https://github.com/pillip/openclaw_archiver_plugin/pull/32)
- **ISSUE-017** (P1): UX 메시지 템플릿 일치 검증 — [PR #34](https://github.com/pillip/openclaw_archiver_plugin/pull/34)

## Next Issues to Implement

All issues completed!

## Recent Activity

- **PR #36**: refactor — 공유 포맷터 추출, 상수/ID 파싱/프로젝트 검증 통합
- **PR #38**: devops — JS/TS 브릿지 패키지, systemd 배포, pyproject.toml 보강

## Documents

| 문서 | 경로 | 설명 |
|------|------|------|
| PRD | `prd.md` | 제품 요구사항 |
| Requirements | `docs/requirements.md` | 25 FRs, 7 NFRs |
| UX Spec | `docs/ux_spec.md` | 메시지 템플릿, 흐름, 용어 사전 |
| Architecture | `docs/architecture.md` | 모듈 구조, API 설계, 트레이드오프 |
| Data Model | `docs/data_model.md` | 스키마, 쿼리 패턴, 마이그레이션 |
| Test Plan | `docs/test_plan.md` | 리스크 매트릭스, 70+ 테스트 케이스 |
| Issues | `issues.md` | 17개 구현 이슈 |
