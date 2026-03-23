# Code Agent

AI 기반 코드 개발 에이전트. Claude Agent SDK를 활용하여 기획 문서를 분석하고, 개발 태스크를 자동으로 생성·실행·검토하는 풀스택 데스크탑 애플리케이션입니다.

## 주요 기능

| 기능 | 상태 | 설명 |
|---|---|---|
| **Design Phase** | ✅ 완성 | 기획 문서(PDF, 이미지, URL, 텍스트) 분석 → 개발 태스크 자동 생성 |
| **Dev Phase** | ✅ 완성 | 코드 작성 → 테스트 → 코드 리뷰 사이클 자동 실행 (최대 3회 재시도) |
| **Legacy Analysis** | ✅ 완성 | 기존 프로젝트 분석, 프레임워크별 가이드맵 생성 |
| **Runtime Error Tracking** | ✅ 완성 | 실행 중 발생한 에러 추적 및 자동 수정 |
| **실시간 로그** | ✅ 완성 | WebSocket 기반 에이전트 실행 로그 스트리밍 (하단 패널) |
| **Git Management** | 🚧 개발 예정 | 백엔드 API·프론트엔드 클라이언트 구현 완료, UI 연동 진행 예정 |
| **대시보드** | 🚧 개발 예정 | 태스크 통계, 에이전트 활동 이력 요약 화면 |
| **콘솔 (직접 실행)** | 🚧 개발 예정 | 에이전트 직접 명령 실행 기능 (로그 확인은 하단 패널 사용) |

## 아키텍처

```
Electron (Desktop Shell)
├── Frontend  — React 19 + TypeScript + Vite + TailwindCSS
│               Zustand 상태 관리, Kanban 보드, Monaco 에디터, Diff Viewer
└── Backend   — FastAPI + Claude Agent SDK
                MySQL 영속성, Redis 메시지 큐, WebSocket 실시간 통신
```

### 에이전트 구성

| 에이전트 | 역할 |
|---|---|
| `design_agent` | 기획 문서 분석 → 태스크 목록 생성 |
| `code_agent` | 태스크 구현 코드 작성 |
| `review_agent` | 인수 조건 기준 코드 검토 및 피드백 |
| `orchestrator` | 태스크 실행 흐름 관리 (동시 실행 최대 3개) |
| `plan_agent` | 개발 계획 수립 |
| `runtime_error_agent` | 런타임 에러 분석 및 수정 |
| `guidemap_agent` | 프로젝트 코딩 가이드라인 생성 |
| `legacy_analysis_agent` | 레거시 코드베이스 분석 |

## 프로젝트 구조

```
code-agent/
├── frontend/                # React + Vite + TypeScript
│   └── src/
│       ├── pages/           # DesignPhase, DevPhase, GitManagement, LegacyAnalysis, ...
│       ├── components/      # Kanban 보드, Diff Viewer, 공통 컴포넌트
│       ├── stores/          # Zustand 상태 관리
│       └── api/             # HTTP 클라이언트
├── backend/                 # Python FastAPI
│   └── app/
│       ├── agents/          # AI 에이전트 및 프롬프트 템플릿
│       ├── api/             # REST API 라우터
│       ├── models/          # SQLAlchemy ORM 모델
│       ├── schemas/         # Pydantic 스키마
│       ├── services/        # 비즈니스 로직
│       ├── repositories/    # 데이터 접근 레이어
│       ├── websocket/       # 실시간 통신
│       └── redis/           # Redis 클라이언트 및 메시지 컨슈머
├── electron/                # Electron 메인 프로세스
├── shared/                  # 공유 타입
├── db_scheme/               # MySQL 스키마 (v1.sql)
└── package.json             # 루트 스크립트
```

## 사전 요구사항

| 항목 | 버전 |
|---|---|
| Node.js | v20+ |
| Python | 3.11+ |
| MySQL | 8.0+ |
| Redis | 7.0+ |
| Git | 2.30+ |

## 시작하기

### 1. 설치

```bash
git clone <your-repo-url>
cd code-agent

# 전체 의존성 설치 (frontend + backend)
npm run install:all
```

### 2. 데이터베이스 초기화

MySQL에서 `db_scheme/v1.sql`을 실행하여 스키마를 생성합니다.

```bash
mysql -u root -p < db_scheme/v1.sql
```

### 3. 환경 변수 설정

```bash
cd backend
cp .env.example .env
# .env 파일을 열어 아래 항목 수정
```

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=code_agent

ANTHROPIC_API_KEY=sk-ant-xxxxxxxx

REDIS_BASE_URL=localhost
REDIS_BASE_PORT=6379
REDIS_DATABASE=0

DEBUG_MODE=false
```

### 4. 개발 서버 실행

```bash
# 루트에서 — Frontend + Backend + Electron 동시 실행
npm run dev
```

개별 실행:

```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npx vite --port 5173

# Electron
npx electron electron/main.js
```

### 5. 확인

| 서비스 | URL |
|---|---|
| Backend 상태 확인 | http://localhost:8000/health |
| Frontend | http://localhost:5173 |
| API 문서 (Swagger) | http://localhost:8000/docs |

## 주요 npm 스크립트

| 명령어 | 설명 |
|---|---|
| `npm run dev` | Frontend + Backend + Electron 동시 실행 |
| `npm run build` | 전체 프로덕션 빌드 |
| `npm run install:all` | 전체 의존성 설치 |
| `npm run lint:frontend` | ESLint 검사 |
| `npm run lint:backend` | Ruff 검사 |
| `npm run test:backend` | pytest 실행 |

## 기술 스택

| 영역 | 기술 |
|---|---|
| AI | Claude Agent SDK (`claude-agent-sdk`), Anthropic API |
| Backend | FastAPI, SQLAlchemy, PyMySQL, Redis, GitPython, Pydantic |
| Frontend | React 19, TypeScript, Vite, TailwindCSS, Zustand, Monaco Editor |
| Desktop | Electron 33, electron-builder |
| Database | MySQL 8.0 |
| 문서 파싱 | PyMuPDF (PDF), python-docx (Word) |
