# Code Agent

스펙서(기획 문서) 중심의 코드 개발 에이전트. Agentic AI 기반으로 기획 문서를 분석하여 개발 태스크를 자동 생성하고, 코드 작성부터 테스트·리뷰·커밋까지 개발 사이클 전체를 자동으로 실행하는 풀스택 데스크탑 애플리케이션입니다.

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
└── Backend   — FastAPI + Anthropic API (Agentic Loop)
                MySQL 영속성, Redis 메시지 큐, WebSocket 실시간 통신
```

---

## 에이전트 파이프라인

Code Agent의 핵심은 네 개의 에이전트가 순서대로 협력하는 파이프라인입니다.  
각 에이전트는 독립적인 역할을 갖고, 앞 단계의 결과를 다음 단계로 전달합니다.

```
기존 프로젝트인 경우
        │
        ▼
┌───────────────┐
│  guidemap     │  코드베이스를 읽고 "이 프로젝트는 어떻게 작성되어야 하는가"를
│  agent        │  마크다운 가이드로 정리합니다.
└───────┬───────┘
        │ guidemap.md (프로젝트 코딩 규칙 문서)
        ▼
┌───────────────┐
│  design       │  기획 문서(PDF / Word / URL / 텍스트)를 분석하고,
│  agent        │  개발 태스크 목록을 자동 생성합니다.
└───────┬───────┘
        │ Task[] — title, description, acceptance_criteria, implementation_steps
        ▼
┌──────────────────────────────────────────┐
│  Dev Pipeline  (태스크 당 최대 3회 반복)   │
│                                          │
│  ┌─────────────┐      ┌───────────────┐  │
│  │ code agent  │ ───► │ review agent  │  │
│  │             │      │               │  │
│  │ 코드 작성   │      │ pytest 작성   │  │
│  │ 테스트 작성 │      │ + 테스트 실행 │  │
│  └─────────────┘      └──────┬────────┘  │
│          ▲                   │           │
│          │    실패 + 피드백   │           │
│          └───────────────────┘           │
│                  통과                    │
│                   │                      │
└───────────────────┼──────────────────────┘
                    ▼
             git auto-commit
```

---

### 1. Guidemap Agent

**"이 프로젝트는 어떻게 코드를 써야 하는가"를 정리합니다.**

기존 프로젝트를 등록할 때 한 번 실행됩니다.  
코드베이스 전체를 파일 탐색 도구(`read_file`, `glob_files`, `grep_search`)로 읽어  
프레임워크 패턴, 디렉터리 구조, 네이밍 컨벤션, 공통 유틸리티 등을  
마크다운 가이드 파일(`{project}_guidemap.md`)로 저장합니다.

이후 design_agent와 code_agent는 이 파일을 참조하여  
프로젝트의 기존 스타일에 맞게 코드를 생성합니다.

| 항목 | 내용 |
|---|---|
| 입력 | 로컬 저장소 경로 |
| 출력 | `guidemaps/{project_name}_guidemap.md` |
| 사용 도구 | `read_file`, `glob_files`, `grep_search` |
| 최대 턴 | 30 |

---

### 2. Design Agent

**기획 문서를 읽고, 개발 태스크를 자동으로 만듭니다.**

2단계로 동작합니다.

**1단계 — 자유 분석 (claude-sonnet-4-6)**  
기획 문서(PDF, Word, 텍스트 등)와 guidemap을 입력받아  
에이전트가 자유롭게 사고하며 개발 요구사항을 분석합니다.

**2단계 — JSON 포맷팅 (claude-haiku-4-5)**  
1단계 분석 결과를 `create_tasks` 도구 호출로 강제 구조화합니다.  
각 태스크는 제목, 설명, 인수 조건, 구현 단계를 포함합니다.

```
입력: 기획 문서 + guidemap (선택)
출력: Task[]
  ├── title               태스크 제목
  ├── description         구현할 내용 설명
  ├── acceptance_criteria 완료 기준 목록
  └── implementation_steps 구현 단계 목록
```

| 항목 | 내용 |
|---|---|
| 입력 | 기획 문서 (PDF / DOCX / URL / 텍스트), guidemap |
| 출력 | 태스크 목록 (DB 저장) |
| 사용 도구 | `read_file`, `glob_files`, `grep_search` |
| 최대 턴 | 30 (1단계) |

---

### 3. Code Agent

**태스크를 받아 실제 코드를 작성합니다.**

태스크의 `description`과 `implementation_steps`를 읽고  
코드를 작성하거나 수정하며, 테스트 코드도 함께 작성합니다.

guidemap이 있는 경우 이를 프롬프트에 포함하여  
프로젝트의 기존 코드 스타일을 따르도록 합니다.

review_agent에서 실패 피드백이 전달된 경우(재시도),  
이전 테스트 결과와 피드백을 프롬프트에 주입하여 수정 방향을 안내합니다.

| 항목 | 내용 |
|---|---|
| 입력 | Task (title, description, acceptance_criteria, implementation_steps), guidemap, 이전 리뷰 피드백 (재시도 시) |
| 출력 | 구현 코드 + 테스트 코드 (파일 직접 작성) |
| 사용 도구 | `read_file`, `write_file`, `edit_file`, `glob_files`, `grep_search`, `bash_exec` |
| 최대 턴 | 20 |

---

### 4. Review Agent

**작성된 코드가 인수 조건을 만족하는지 pytest로 검증합니다.**

2단계로 동작합니다.

**1단계 — 테스트 작성 + 실행 (claude-sonnet-4-6)**  
태스크의 `acceptance_criteria`를 기반으로 pytest 테스트를 작성하고  
`bash_exec`로 실행한 뒤 결과를 분석합니다.

**2단계 — 결과 구조화**  
1단계 전체 대화 히스토리를 이어받아  
`submit_review_result` 도구 호출로 결과를 강제 구조화합니다.

```
출력: ReviewResult
  ├── passed            전체 인수 조건 통과 여부 (boolean)
  ├── test_output       pytest stdout/stderr 전체
  └── overall_feedback  실패 시 각 항목별 수정 지시
```

- **통과**: 파이프라인이 auto-commit 후 종료됩니다.
- **실패**: 피드백을 code_agent에 주입하고 재시도합니다. (최대 3회)

| 항목 | 내용 |
|---|---|
| 입력 | Task (acceptance_criteria), 프로젝트 경로 |
| 출력 | ReviewResult (passed, test_output, overall_feedback) |
| 사용 도구 | `read_file`, `write_file`, `glob_files`, `grep_search`, `bash_exec` |
| 최대 턴 | 14 (1단계) |

---

### Dev Pipeline — code → review 사이클

파이프라인은 태스크 하나에 대해 code_agent → review_agent를 최대 3회 반복합니다.

```
attempt 1
  code_agent 실행
  review_agent 실행
    통과 → auto-commit → done
    실패 → 피드백 저장

attempt 2
  code_agent 실행 (attempt 1 피드백 주입)
  review_agent 실행
    통과 → auto-commit → done
    실패 → 피드백 저장

attempt 3
  code_agent 실행 (attempt 2 피드백 주입)
  review_agent 실행
    통과 → auto-commit → done
    실패 → failed (3회 초과)
```

동시에 실행 가능한 태스크 수는 설정(`max_concurrent_tasks`)으로 제한됩니다.

---

### 에이전트 전체 목록

| 에이전트 | 파일 | 역할 |
|---|---|---|
| `guidemap_agent` | `agents/guidemap_agent.py` | 프로젝트 코딩 가이드라인 생성 |
| `design_agent` | `agents/design_agent_v2.py` | 기획 문서 분석 → 태스크 목록 생성 |
| `code_agent` | `agents/code_agent.py` | 태스크 구현 코드 작성 |
| `review_agent` | `agents/review_agent.py` | pytest 기반 인수 조건 검증 |
| `pipeline` | `agents/pipeline.py` | code → review 사이클 실행 (최대 3회) |
| `runtime_error_agent` | `agents/runtime_error_agent.py` | 런타임 에러 분석 및 수정 |
| `legacy_analysis_agent` | `agents/legacy_analysis_agent.py` | 레거시 코드베이스 분석 |

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
| AI | Anthropic API (Agentic Loop 직접 구현), Claude Sonnet / Haiku |
| Backend | FastAPI, SQLAlchemy, PyMySQL, Redis, GitPython, Pydantic |
| Frontend | React 19, TypeScript, Vite, TailwindCSS, Zustand, Monaco Editor |
| Desktop | Electron 33, electron-builder |
| Database | MySQL 8.0 |
| 문서 파싱 | PyMuPDF (PDF), python-docx (Word) |
