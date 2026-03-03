# OpenClaw Archiver Plugin

Slack DM을 통해 메세지 링크를 개인별로 격리하여 저장·관리하는 OpenClaw 플러그인.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (패키지 관리)

## Setup

```bash
# 프로젝트 클론
git clone <repo-url>
cd openclaw_archiver_plugin

# 의존성 설치
uv sync

# 테스트 실행
uv run pytest -q
```

## Installation

### 1. Python HTTP 서버 설치

```bash
# 프로젝트 클론 및 설치
git clone <repo-url>
cd openclaw_archiver_plugin
pip install .
```

### 2. Python HTTP 서버 실행

```bash
# 직접 실행 (기본 포트: 8201)
openclaw-archiver-server

# 환경변수로 포트 변경
OPENCLAW_ARCHIVER_PORT=9000 openclaw-archiver-server
```

서버가 정상적으로 실행되면 health check로 확인할 수 있습니다:

```bash
curl http://127.0.0.1:8201/health
# {"ok": true, "plugin": "archiver", "version": "0.1.0"}
```

운영 환경에서는 systemd로 관리하는 것을 권장합니다. 아래 [Deployment (systemd)](#deployment-systemd) 섹션을 참고하세요.

### 3. 브릿지 플러그인 설치

```bash
cd bridge/openclaw-archiver
openclaw plugins install .
```

설치 후 OpenClaw 게이트웨이를 재시작하면 `/archive` 명령이 등록됩니다.

### Commands

| 명령 | 설명 |
|------|------|
| `/archive save <제목> <링크> [/p <프로젝트>]` | 메세지 저장 |
| `/archive list [/p <프로젝트>]` | 목록 조회 |
| `/archive search <키워드> [/p <프로젝트>]` | 검색 |
| `/archive edit <ID> <새 제목>` | 제목 수정 |
| `/archive remove <ID>` | 삭제 |
| `/archive project list` | 프로젝트 목록 |
| `/archive project rename <기존> <새이름>` | 프로젝트 이름 변경 |
| `/archive project delete <이름>` | 프로젝트 삭제 |
| `/archive help` | 도움말 |

## Configuration

| 환경변수 | 설명 | 기본값 |
|----------|------|--------|
| `OPENCLAW_ARCHIVER_PORT` | HTTP 브릿지 서버 포트 | `8201` |
| `OPENCLAW_ARCHIVER_DB_PATH` | DB 파일 경로 | `~/.openclaw/workspace/.archiver/archiver.sqlite3` |
| `OPENCLAW_ARCHIVER_URL` | 브릿지에서 Python 서버 접속 URL | `http://127.0.0.1:8201` |

## Deployment (systemd)

`deploy/openclaw-archiver.service` 파일을 사용하여 systemd 서비스로 등록할 수 있습니다.

```bash
# 서비스 파일 복사
sudo cp deploy/openclaw-archiver.service /etc/systemd/system/

# ExecStart 경로를 실제 환경에 맞게 수정
sudo systemctl edit openclaw-archiver.service

# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable --now openclaw-archiver
```

포트 충돌(exit code 78)이 발생하면 systemd가 서비스를 자동 재시작하지 않습니다.
`journalctl -u openclaw-archiver` 로그를 확인한 뒤 아래 "Troubleshooting" 섹션을 참고하세요.

## Troubleshooting

### 포트 충돌 (Port conflict)

Python 서버가 시작할 때 기본 포트(8201)가 이미 사용 중이면 다음과 같은 에러가 발생합니다:

```
Cannot bind to 127.0.0.1:8201 — [Errno 48] Address already in use
```

#### 1. 원인 확인

```bash
# 포트를 점유 중인 프로세스 확인
lsof -i :8201

# 또는
ss -tlnp | grep 8201
```

#### 2. Python 서버 포트 변경

```bash
# 환경변수로 다른 포트 지정
export OPENCLAW_ARCHIVER_PORT=9001
uv run openclaw-archiver-server

# systemd 사용 시
sudo systemctl edit openclaw-archiver
# [Service] 섹션에 추가:
# Environment=OPENCLAW_ARCHIVER_PORT=9001
sudo systemctl restart openclaw-archiver
```

#### 3. JS/TS 브릿지도 함께 변경

Python 서버 포트를 변경했다면, 브릿지도 동일한 주소를 가리키도록 설정해야 합니다.

**방법 A — 환경변수:**

```bash
export OPENCLAW_ARCHIVER_URL=http://127.0.0.1:9001
```

**방법 B — 플러그인 설정 (openclaw.plugin.json):**

```json
{
  "serverUrl": "http://127.0.0.1:9001"
}
```

> Python 서버와 브릿지의 포트가 일치하지 않으면 브릿지에서
> "Could not reach the Archiver server. Is it running?" 에러가 발생합니다.

## Test

```bash
# 전체 테스트
uv run pytest -q

# 커버리지 포함
uv run pytest --cov=src/openclaw_archiver --cov-report=term-missing
```

## Development

```bash
# 린트
uv run ruff check .

# 포맷
uv run black .

# 빌드
uv build
```
