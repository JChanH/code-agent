# 코드 에이전트 시스템 — 개발 계획서

> **문서 버전**: v2.1  
> **작성일**: 2026-03-09  
> **최종 수정**: 2026-03-09 (Git 관리 탭 추가, 자동 커밋 제거, 통신 방식 분석 반영)  
> **목적**: Claude Agent SDK Python 기반 코드 자동 개발/수정 에이전트 시스템의 전체 개발 계획

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2026-03-09 | 초기 계획 수립 |
| v2.0 | 2026-03-09 | Aperant 비교 분석 반영, Git Worktree 전략 확정 (사용자별), 순차 실행 확정, 프로젝트 스택(Python/Java) 보안 전략 추가, QA 자동 수정 루프 후속 단계로 이관, 세션 간 메모리 제외 |
| v2.1 | 2026-03-09 | 자동 커밋 제거 → Git 관리 탭(수동 commit/push/PR) 추가, Aperant IPC vs WebSocket 분석 반영 |

---

## 1. SDK 분석 결과 및 아키텍처 결정사항

### 1.1 Claude Agent SDK Python 핵심 특성

Claude Agent SDK Python은 Claude Code CLI를 내부에 번들링한 Python 래퍼입니다. 단순한 API 클라이언트가 아니라, Claude Code의 전체 에이전트 루프(파일 읽기/쓰기, 명령 실행, 코드 편집)를 프로그래밍 방식으로 제어할 수 있는 SDK입니다.

**주요 API:**

| API | 용도 | 특징 |
|-----|------|------|
| `query()` | 단발성 에이전트 실행 | 간단한 async iterator, 프롬프트 → 결과 |
| `ClaudeSDKClient` | 풀 세션 관리 | Hooks, Custom Tools, 세션 유지, 멀티턴 |

**내장 도구(Built-in Tools):**
Read, Write, Edit, Bash, Glob, Grep, Agent(서브에이전트), WebSearch 등

**핵심 기능:**
- **Hooks**: PreToolUse, PostToolUse, Stop, SubagentStart 등 에이전트 루프의 각 단계에 개입 가능
- **Subagents**: 독립된 컨텍스트의 하위 에이전트 생성 (설계 에이전트, 코딩 에이전트 분리에 활용)
- **Custom Tools**: MCP 서버를 in-process로 실행, Python 함수를 도구로 제공
- **File Checkpointing**: 파일 변경사항의 스냅샷/롤백 지원
- **Structured Outputs**: JSON 스키마 기반 구조화된 응답
- **Permission Mode**: 도구 사용 권한을 세밀하게 제어

### 1.2 Aperant(Auto-Claude) 비교 분석 결과

Aperant는 유사 목적의 오픈소스 프로젝트(13.1k 스타, 1,089 커밋, v2.7.6)입니다. 분석 결과를 바탕으로 우리 프로젝트에 적합한 전략을 선택했습니다.

| 항목 | Aperant 방식 | 우리 프로젝트 결정 | 선택 이유 |
|------|-------------|-------------------|----------|
| **코드 격리** | Task별 git worktree (최대 12개 병렬) | **사용자별 1개 worktree** | Task별 worktree는 관리 불가능한 수준으로 증가 |
| **실행 방식** | 병렬 에이전트 (12개 동시) | **순차 실행** | 단일 worktree에서 병렬 작업 시 충돌 발생 |
| **QA 루프** | QA Reviewer → QA Fixer 자동 루프 (최대 50회) | **후속 단계에서 추가** | 기획 미정, 기본 파이프라인 우선 |
| **데이터 저장** | 파일 시스템 (.auto-claude/) | **MySQL (외부 DB)** | 팀 협업, 데이터 분석, 외부 시스템 연동 |
| **세션 간 메모리** | Graph DB (FalkorDB/Graphiti) | **불필요 (제외)** | Task 단위 실행 + DB 컨텍스트로 충분 |
| **머지** | AI 기반 3단계 자동 머지 | **Git 관리 탭에서 수동 commit/push/PR** | 사용자가 직접 변경사항 확인 후 커밋 |
| **보안** | 3계층 (OS 샌드박스 + 파일제한 + 동적 허용목록) | **2계층 + 프로젝트 스택 프로파일** | Python/Java 프로젝트 특성에 맞춤 |
| **Spec 관리** | 파일 기반 (spec.md, requirements.json 등) | **DB 기반 + Structured Output** | MySQL에서 일관된 관리, 스키마 보장 |

### 1.3 아키텍처 결정

SDK가 Python 기반이므로, 백엔드는 반드시 Python이어야 합니다. Electron(Node.js)과의 통신을 위해 FastAPI를 선택합니다.

```
┌──────────────────────────────────────────────────────────┐
│                    Electron Shell                         │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              React Frontend (Renderer)              │ │
│  │                                                     │ │
│  │  ┌─────────────────┐    ┌────────────────────────┐  │ │
│  │  │  설계 단계        │    │  개발 단계              │  │ │
│  │  │  Kanban Board    │    │  Kanban Board          │  │ │
│  │  │                 │    │  Plan→Code→Review      │  │ │
│  │  └─────────────────┘    └────────────────────────┘  │ │
│  │                                                     │ │
│  │  ┌─────────────────────────────────────────────────┐│ │
│  │  │  공통: Diff Viewer, 실시간 로그, 설정 패널      ││ │
│  │  └─────────────────────────────────────────────────┘│ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │ HTTP / WebSocket               │
│  ┌───────────────────────┴─────────────────────────────┐ │
│  │         Electron Main Process (Node.js)              │ │
│  │   - Python 프로세스 관리 (child_process)              │ │
│  │   - 시스템 다이얼로그, 파일 시스템 접근               │ │
│  │   - API 키 보안 저장 (keytar)                        │ │
│  └───────────────────────┬─────────────────────────────┘ │
└──────────────────────────┼───────────────────────────────┘
                           │ HTTP / WebSocket (localhost)
┌──────────────────────────┴─────────────────────────────┐
│              Python Backend (FastAPI)                    │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │            Agent Orchestrator                     │   │
│  │                                                   │   │
│  │  ┌──────────────┐    ┌─────────────────────────┐ │   │
│  │  │ Design Agent │    │  Development Agent       │ │   │
│  │  │ (query)      │    │  (ClaudeSDKClient)       │ │   │
│  │  │              │    │                          │ │   │
│  │  │ - Spec 분석   │    │  ┌──────┐ ┌──────────┐ │ │   │
│  │  │ - Task 분해   │    │  │Plan  │→│Code      │ │ │   │
│  │  │ - 구조화 출력  │    │  │Agent │ │Agent     │ │ │   │
│  │  └──────────────┘    │  └──────┘ └──────────┘ │ │   │
│  │                       │  (Subagents 활용)       │ │   │
│  │                       └─────────────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────┐  │
│  │ MySQL Client │  │ Worktree Mgr  │  │ WebSocket   │  │
│  │ (SQLAlchemy) │  │ (사용자별 WT) │  │ (실시간 통신)│  │
│  └──────┬───────┘  └───────────────┘  └─────────────┘  │
└─────────┼──────────────────────────────────────────────┘
          │
    ┌─────┴──────┐
    │   MySQL    │
    │ (외부 DB)  │
    └────────────┘
```

### 1.4 Git Worktree 운영 전략

사용자별 1개 worktree를 운영하며, 해당 worktree 안에서 Task를 순차적으로 처리합니다.

```
main branch (보호됨, 직접 push 불가)
  │
  ├── worktree/user-A/       ← 사용자 A의 에이전트가 여기서만 작업
  │     ├── Task 1 작업 → commit
  │     ├── Task 2 작업 → commit
  │     └── push → PR 생성 → 코드 리뷰 → main 머지
  │
  ├── worktree/user-B/       ← 사용자 B의 에이전트가 여기서만 작업
  │     ├── Task 3 작업 → commit
  │     └── push → PR 생성 → 코드 리뷰 → main 머지
  │
  └── ...
```

**핵심 원칙:**
- 에이전트는 반드시 해당 사용자의 worktree 경로(cwd)에서만 작업
- Git 작업(commit, push, PR)은 **사용자가 Git 관리 탭에서 직접 수행**
- main branch에 직접 수정하는 것은 차단 (PreToolUse Hook)

### 1.5 대상 프로젝트 스택

에이전트가 주로 작업할 프로젝트 스택이 명확합니다:

| 스택 | 프레임워크 | 특징 |
|------|----------|------|
| **Python** | FastAPI 기반 | 프로젝트 구조가 미리 정의됨, 초기 생성 시 표준 구조 사용 |
| **Java** | 기존 사내 프레임워크 | 이미 운영 중인 프레임워크 위에서 작업 |

이 정보는 보안 프로파일, 에이전트 프롬프트, 허용 명령 목록 결정에 활용됩니다.

### 1.6 기술 스택 최종 확정

| 영역 | 기술 | 이유 |
|------|------|------|
| **Frontend** | React 18 + TypeScript + Vite | 요구사항 충족, 빠른 HMR |
| **UI 라이브러리** | TailwindCSS + shadcn/ui | 빠른 개발, 일관된 디자인 |
| **Kanban 라이브러리** | @dnd-kit/core | 가볍고 확장성 좋음 |
| **상태 관리** | Zustand | 단순하고 React 외부에서도 접근 가능 |
| **Diff Viewer** | Monaco Editor (diff mode) | VS Code 수준의 diff 표시 |
| **Desktop Shell** | Electron 33+ | 요구사항 충족 |
| **Backend** | Python 3.11+ / FastAPI | SDK 호환, 비동기 지원 |
| **Agent SDK** | claude-agent-sdk (Python) | 요구사항 충족 |
| **ORM** | SQLAlchemy 2.0 | MySQL 호환, 마이그레이션 관리 |
| **DB** | MySQL 8.0 (외부) | 요구사항 충족 |
| **실시간 통신** | WebSocket (FastAPI) | 에이전트 진행상황 스트리밍 |
| **빌드/패키징** | electron-builder | 크로스 플랫폼 배포 |

---

## 2. DB 스키마 설계 (MySQL)

```sql
-- ============================================
-- 프로젝트 관리
-- ============================================
CREATE TABLE projects (
    id              VARCHAR(36) PRIMARY KEY,        -- UUID
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    repo_url        VARCHAR(500),                   -- Git 저장소 URL
    main_branch     VARCHAR(100) DEFAULT 'main',    -- 메인 브랜치명
    project_stack   ENUM('python', 'java', 'other') DEFAULT 'python',
    framework       VARCHAR(100),                   -- 'fastapi', 'spring', 등
    status          ENUM('setup', 'designing', 'developing', 'completed') DEFAULT 'setup',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================
-- 사용자 및 Worktree 관리
-- ============================================
CREATE TABLE users (
    id              VARCHAR(36) PRIMARY KEY,
    username        VARCHAR(100) NOT NULL UNIQUE,
    display_name    VARCHAR(255),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_worktrees (
    id              VARCHAR(36) PRIMARY KEY,
    user_id         VARCHAR(36) NOT NULL,
    project_id      VARCHAR(36) NOT NULL,
    worktree_path   VARCHAR(500) NOT NULL,          -- 로컬 worktree 경로
    branch_name     VARCHAR(255) NOT NULL,          -- worktree 브랜치명
    status          ENUM('active', 'inactive', 'archived') DEFAULT 'active',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_project (user_id, project_id)
);

-- ============================================
-- 설계 단계: Spec 입력 관리
-- ============================================
CREATE TABLE specs (
    id              VARCHAR(36) PRIMARY KEY,
    project_id      VARCHAR(36) NOT NULL,
    source_type     ENUM('document', 'image', 'text', 'url') NOT NULL,
    source_path     VARCHAR(500),                   -- 파일 경로 or URL
    raw_content     LONGTEXT,                       -- 원본 텍스트 (추출된)
    analysis_result LONGTEXT,                       -- AI 분석 결과 (JSON)
    status          ENUM('uploaded', 'analyzing', 'analyzed', 'confirmed') DEFAULT 'uploaded',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- ============================================
-- Task 관리 (설계 → 개발 연결점)
-- ============================================
CREATE TABLE tasks (
    id                  VARCHAR(36) PRIMARY KEY,
    project_id          VARCHAR(36) NOT NULL,
    spec_id             VARCHAR(36),                -- 어떤 spec에서 도출되었는지
    assigned_user_id    VARCHAR(36),                -- 담당 사용자 (해당 사용자의 worktree에서 실행)
    title               VARCHAR(500) NOT NULL,
    description         TEXT NOT NULL,
    acceptance_criteria JSON,                       -- ["조건1", "조건2", ...]
    priority            ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    complexity          ENUM('trivial', 'low', 'medium', 'high', 'very_high') DEFAULT 'medium',
    status              ENUM('backlog', 'planning', 'plan_review', 
                             'coding', 'reviewing', 'done', 'failed') DEFAULT 'backlog',
    dependencies        JSON,                       -- [task_id, task_id, ...]
    sort_order          INT DEFAULT 0,
    auto_approve        BOOLEAN DEFAULT FALSE,      -- 자동 승인 여부
    auto_approve_config JSON,                       -- 자동 승인 조건 (lint, test 등)
    git_commit_hash     VARCHAR(40),                -- 완료 시 커밋 해시
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (spec_id) REFERENCES specs(id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================
-- 개발 단계: 각 Step 기록
-- ============================================
CREATE TABLE task_steps (
    id              VARCHAR(36) PRIMARY KEY,
    task_id         VARCHAR(36) NOT NULL,
    step_type       ENUM('plan', 'plan_review', 'code', 'review') NOT NULL,
    status          ENUM('pending', 'in_progress', 'completed', 
                         'rejected', 'skipped') DEFAULT 'pending',
    content         LONGTEXT,                       -- plan 내용 or 코드 변경 요약
    agent_messages  JSON,                           -- 에이전트 메시지 로그 (전체)
    session_id      VARCHAR(255),                   -- Claude Agent SDK 세션 ID
    started_at      TIMESTAMP NULL,
    completed_at    TIMESTAMP NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- ============================================
-- 코드 변경사항 추적
-- ============================================
CREATE TABLE code_changes (
    id              VARCHAR(36) PRIMARY KEY,
    task_step_id    VARCHAR(36) NOT NULL,
    file_path       VARCHAR(500) NOT NULL,
    change_type     ENUM('create', 'modify', 'delete') NOT NULL,
    diff_content    LONGTEXT,                       -- unified diff
    before_content  LONGTEXT,                       -- 변경 전 (롤백용)
    after_content   LONGTEXT,                       -- 변경 후
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_step_id) REFERENCES task_steps(id) ON DELETE CASCADE
);

-- ============================================
-- 리뷰 기록
-- ============================================
CREATE TABLE reviews (
    id              VARCHAR(36) PRIMARY KEY,
    task_step_id    VARCHAR(36) NOT NULL,
    reviewer_type   ENUM('human', 'auto') NOT NULL,
    result          ENUM('approved', 'rejected', 'revision_requested') NOT NULL,
    feedback        TEXT,
    auto_conditions JSON,                           -- 자동 승인 시 검증 결과
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_step_id) REFERENCES task_steps(id) ON DELETE CASCADE
);

-- ============================================
-- 프로젝트 스택 보안 프로파일
-- ============================================
CREATE TABLE security_profiles (
    id              VARCHAR(36) PRIMARY KEY,
    project_id      VARCHAR(36) NOT NULL,
    stack_type      ENUM('python', 'java', 'other') NOT NULL,
    allowed_commands JSON NOT NULL,                  -- ["pip", "pytest", "ruff", ...]
    blocked_commands JSON NOT NULL,                  -- ["rm -rf", "sudo", ...]
    allowed_paths    JSON,                           -- 수정 허용 경로 패턴
    blocked_paths    JSON,                           -- 수정 차단 경로 패턴
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- ============================================
-- 설정 관리
-- ============================================
CREATE TABLE settings (
    id              VARCHAR(36) PRIMARY KEY,
    project_id      VARCHAR(36),                    -- NULL이면 전역 설정
    setting_key     VARCHAR(255) NOT NULL,
    setting_value   TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE KEY unique_setting (project_id, setting_key)
);
```

**v1.0 대비 변경사항:**
- `projects` 테이블에 `repo_url`, `main_branch`, `project_stack`, `framework` 추가
- `users`, `user_worktrees` 테이블 신규 추가
- `tasks` 테이블에 `assigned_user_id`, `git_commit_hash` 추가
- `security_profiles` 테이블 신규 추가 (프로젝트 스택 기반 보안)

---

## 3. 상세 개발 순서

### Phase 0: 프로젝트 초기 설정 (1주)

**목표**: 전체 프로젝트 구조 생성, 빌드 파이프라인 확인, DB 연결 검증

#### 0-1. 모노레포 구조 생성

```
code-agent/
├── frontend/                    # React (Vite + TypeScript)
│   ├── src/
│   │   ├── components/          # 공통 UI 컴포넌트
│   │   │   ├── kanban/          # Kanban Board 컴포넌트
│   │   │   ├── diff-viewer/     # 코드 Diff 뷰어
│   │   │   └── common/          # 버튼, 모달, 로딩 등
│   │   ├── pages/               # 페이지 단위
│   │   │   ├── DesignPhase/     # 설계 단계 페이지
│   │   │   ├── DevPhase/        # 개발 단계 페이지
│   │   │   └── Settings/        # 설정 페이지
│   │   ├── stores/              # Zustand 스토어(상태 관리 모듈)
│   │   ├── hooks/               # 커스텀 React hooks
│   │   ├── services/            # API 통신 레이어
│   │   │   ├── api.ts           # REST API 클라이언트
│   │   │   └── websocket.ts     # WebSocket 클라이언트
│   │   └── types/               # TypeScript 타입 정의
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
│
├── backend/                     # Python (FastAPI)
│   ├── app/
│   │   ├── main.py              # FastAPI 엔트리포인트(+웹소켓)
│   │   ├── config.py            # 환경 설정
│   │   ├── models/              # SQLAlchemy 모델
│   │   ├── schemas/             # Pydantic 스키마 (요청/응답)
│   │   ├── api/                 # API 라우터
│   │   │   ├── projects.py
│   │   │   ├── specs.py
│   │   │   ├── tasks.py
│   │   │   ├── users.py         # [v2.0] 사용자/worktree 관리
│   │   │   ├── git.py           # [v2.1] Git 관리 탭 API
│   │   │   └── agent.py         # 에이전트 실행 API
│   │   ├── agents/              # Agent 로직
│   │   │   ├── orchestrator.py  # 전체 흐름 관리
│   │   │   ├── design_agent.py  # 설계 에이전트
│   │   │   ├── plan_agent.py    # Plan 서브에이전트
│   │   │   ├── code_agent.py    # Code 서브에이전트
│   │   │   ├── review_agent.py  # 자동 리뷰 에이전트
│   │   │   ├── security/        # [v2.0] 보안 프로파일
│   │   │   │   ├── profiles.py  # 스택별 보안 규칙
│   │   │   │   └── hooks.py     # PreToolUse 보안 Hook
│   │   │   └── tools/           # Custom MCP Tools
│   │   │       ├── db_tools.py  # MySQL 조회/저장 도구
│   │   │       └── project_tools.py  # 프로젝트 파일 도구
│   │   ├── services/            # 비즈니스 로직
│   │   │   ├── worktree.py      # [v2.0] Git worktree 관리
│   │   │   └── git.py           # [v2.0] Git 작업 (commit, diff)
│   │   └── websocket/           # WebSocket 핸들러
│   ├── requirements.txt
│   └── pyproject.toml
│
├── electron/                    # Electron Main Process
│   ├── main.ts                  # 메인 프로세스
│   ├── preload.ts               # 프리로드 스크립트
│   ├── python-manager.ts        # Python 백엔드 프로세스 관리
│   └── ipc-handlers.ts          # IPC 핸들러 (파일 다이얼로그 등)
│
├── shared/                      # 프론트/백엔드 공유 타입
│   └── types/
│       ├── project.ts
│       ├── task.ts
│       └── agent.ts
│
├── electron-builder.yml
├── package.json                 # 루트 (워크스페이스 관리)
└── README.md
```

**v1.0 대비 변경**: `agents/security/`, `services/worktree.py`, `services/git.py`, `api/users.py` 추가

#### 0-2. 기술 스택 설치 및 설정

```bash
# Frontend
cd frontend && npm init vite@latest . -- --template react-ts
npm install zustand @dnd-kit/core @dnd-kit/sortable
npm install @monaco-editor/react lucide-react
npm install tailwindcss @tailwindcss/vite

# Backend
cd backend
pip install fastapi uvicorn sqlalchemy pymysql
pip install claude-agent-sdk websockets python-multipart
pip install gitpython                               # [v2.0] Git 조작용

# Electron
npm install electron electron-builder
npm install -D concurrently wait-on
```

#### 0-3. MySQL 연결 및 마이그레이션

- SQLAlchemy 모델 정의 (위 스키마 기반)
- 연결 테스트 스크립트 작성

#### 0-4. [v2.0] Git Worktree 관리 서비스

```python
# backend/app/services/worktree.py
import subprocess
from pathlib import Path

class WorktreeManager:
    """사용자별 Git worktree를 관리합니다."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def create_worktree(self, user_id: str, branch_name: str) -> str:
        """사용자용 worktree를 생성합니다."""
        worktree_path = self.repo_path / "worktrees" / user_id
        
        if worktree_path.exists():
            return str(worktree_path)
        
        subprocess.run([
            "git", "worktree", "add",
            str(worktree_path),
            "-b", branch_name
        ], cwd=str(self.repo_path), check=True)
        
        return str(worktree_path)
    
    def get_worktree_path(self, user_id: str) -> str | None:
        """사용자의 worktree 경로를 반환합니다."""
        worktree_path = self.repo_path / "worktrees" / user_id
        return str(worktree_path) if worktree_path.exists() else None


class GitService:
    """[v2.0] Git 관리 탭에서 사용하는 Git 작업 서비스입니다.
    사용자가 직접 commit/push/PR을 수행할 때 호출됩니다."""
    
    def __init__(self, worktree_path: str):
        self.worktree_path = worktree_path
    
    def get_status(self) -> list[dict]:
        """변경된 파일 목록 반환 (git status --porcelain)"""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.worktree_path, capture_output=True, text=True
        )
        files = []
        for line in result.stdout.strip().split("\n"):
            if line:
                status = line[:2].strip()
                path = line[3:]
                files.append({"status": status, "path": path})
        return files
    
    def get_diff(self, file_path: str) -> str:
        """특정 파일의 diff 반환"""
        result = subprocess.run(
            ["git", "diff", file_path],
            cwd=self.worktree_path, capture_output=True, text=True
        )
        return result.stdout
    
    def stage_files(self, file_paths: list[str]):
        """선택된 파일을 staging"""
        subprocess.run(
            ["git", "add"] + file_paths,
            cwd=self.worktree_path, check=True
        )
    
    def commit(self, message: str) -> str:
        """커밋 실행, 커밋 해시 반환"""
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.worktree_path, check=True
        )
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.worktree_path, capture_output=True, text=True
        )
        return result.stdout.strip()
    
    def pull(self, strategy: str = "rebase") -> str:
        """main 변경사항을 worktree로 pull"""
        cmd = ["git", "pull", "origin", "main"]
        if strategy == "rebase":
            cmd.append("--rebase")
        result = subprocess.run(
            cmd, cwd=self.worktree_path, capture_output=True, text=True
        )
        return result.stdout
    
    def push(self) -> str:
        """worktree 브랜치를 원격에 push"""
        result = subprocess.run(
            ["git", "push", "-u", "origin", "HEAD"],
            cwd=self.worktree_path, capture_output=True, text=True
        )
        return result.stdout
    
    def get_log(self, count: int = 20) -> list[dict]:
        """최근 커밋 이력 반환"""
        result = subprocess.run(
            ["git", "log", f"--max-count={count}",
             "--format=%H|%h|%s|%an|%ar"],
            cwd=self.worktree_path, capture_output=True, text=True
        )
        logs = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|", 4)
                logs.append({
                    "hash": parts[0], "short_hash": parts[1],
                    "message": parts[2], "author": parts[3],
                    "relative_date": parts[4]
                })
        return logs
    
    def revert_file(self, file_path: str):
        """특정 파일의 변경사항을 되돌리기"""
        subprocess.run(
            ["git", "checkout", "--", file_path],
            cwd=self.worktree_path, check=True
        )
```

#### 0-5. 개발 환경 통합 실행 스크립트

```json
// package.json (루트)
{
  "scripts": {
    "dev": "concurrently \"npm run dev:backend\" \"npm run dev:frontend\" \"npm run dev:electron\"",
    "dev:frontend": "cd frontend && vite",
    "dev:backend": "cd backend && uvicorn app.main:app --reload --port 8000",
    "dev:electron": "wait-on http://localhost:5173 http://localhost:8000 && electron ."
  }
}
```

#### 0-6. 검증 기준
- [ ] `npm run dev` 로 Electron 앱이 뜨고, React 화면 표시
- [ ] FastAPI `/health` 엔드포인트 응답 확인
- [ ] MySQL 테이블 생성 확인
- [ ] Claude Agent SDK `query("Hello")` 테스트 통과
- [ ] [v2.0] Git worktree 생성/삭제 테스트 통과

---

### Phase 1: 핵심 UI 프레임워크 (1.5주)

**목표**: Kanban Board 공통 컴포넌트 및 두 단계(설계/개발) 화면 프레임 완성

#### 1-1. 앱 레이아웃 구현

```
┌──────────────────────────────────────────────────────┐
│  [로고]  프로젝트명 ▼     사용자: Kim ▼  [설정] [알림] │
├──────────┬───────────────────────────────────────────┤
│          │                                           │
│ 프로젝트  │   [설계]  [개발]  [Git 관리]  ← 탭 전환   │
│ 목록     │                                           │
│          │   ┌─────────────────────────────────────┐ │
│ > Proj A │   │                                     │ │
│   Proj B │   │         Kanban Board Area           │ │
│   Proj C │   │     (설계/개발 탭 선택 시 표시)        │ │
│          │   │                                     │ │
│ [+ 새    │   │         Git Management Area         │ │
│  프로젝트]│   │       (Git 관리 탭 선택 시 표시)      │ │
│          │   └─────────────────────────────────────┘ │
│          │   ┌─────────────────────────────────────┐ │
│          │   │  하단 패널: 로그 / 상세 정보          │ │
│          │   └─────────────────────────────────────┘ │
└──────────┴───────────────────────────────────────────┘
```

**v1.0 대비 변경**: 상단에 사용자 선택 드롭다운 추가, **[Git 관리] 탭 추가**

#### [v2.0] Git 관리 탭 화면 설계

```
┌─────────────────────────────────────────────────────────────┐
│  Git 관리                              worktree/user-Kim    │
├──────────────────┬──────────────────────────────────────────┤
│                  │                                          │
│  변경된 파일 (5)  │  파일 Diff 미리보기                       │
│                  │  ┌──────────────────────────────────────┐ │
│  ✅ app/api/     │  │  [Monaco Diff Editor]                │ │
│     auth.py      │  │                                      │ │
│  ✅ app/models/  │  │  - old line                          │ │
│     user.py      │  │  + new line                          │ │
│  ☐ app/tests/   │  │                                      │ │
│     test_auth.py │  └──────────────────────────────────────┘ │
│  ☐ requirements │                                          │
│     .txt         │  커밋 메시지:                              │
│                  │  ┌──────────────────────────────────────┐ │
│                  │  │ feat: 사용자 인증 API 구현             │ │
│                  │  └──────────────────────────────────────┘ │
│                  │                                          │
├──────────────────┤  [Stage Selected] [Stage All]            │
│  커밋 이력 (최근) │  [Commit]                                 │
│                  │                                          │
│  abc1234 feat:.. │  ──────────────────────────────────────── │
│  def5678 fix:..  │                                          │
│  ghi9012 refac.. │  [Pull (main → worktree)]                │
│                  │  [Push]                                   │
│                  │  [PR 생성]                                │
│                  │                                          │
└──────────────────┴──────────────────────────────────────────┘
```

**Git 관리 탭 기능:**

| 기능 | 설명 |
|------|------|
| **변경 파일 목록** | 에이전트가 수정한 파일 + 수동 수정 파일 전체 표시 (git status) |
| **파일별 Diff 보기** | 변경된 파일 클릭 시 Monaco Diff Editor로 before/after 비교 |
| **선택적 Stage** | 파일 단위로 staging (체크박스), Stage All 버튼 |
| **Commit** | 커밋 메시지 입력 → 수동 커밋 |
| **Pull** | main 브랜치의 최신 변경사항을 worktree로 pull (rebase/merge 선택) |
| **Push** | worktree 브랜치를 원격에 push |
| **PR 생성** | push 후 PR 생성 (향후 GitHub/GitLab 연동 시 자동화) |
| **커밋 이력** | 해당 worktree의 최근 커밋 로그 표시 |
| **Revert** | 특정 파일 또는 커밋을 되돌리기 |

#### 1-2. Kanban Board 공통 컴포넌트

핵심 추상화 구조:

```typescript
// 공통 Kanban 인터페이스
interface KanbanColumn<T> {
  id: string;
  title: string;
  status: string;
  color: string;
  items: T[];
  allowDrop: boolean;
  actions?: ColumnAction[];
}

interface KanbanCard {
  id: string;
  title: string;
  subtitle?: string;
  status: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  tags?: string[];
  progress?: number;
  isRunning?: boolean;
  assignedUser?: string;        // [v2.0] 담당 사용자
}
```

기능 요구사항:
- 드래그 앤 드롭 (dnd-kit)
- 컬럼 간 카드 이동 시 상태 자동 변경
- 카드 클릭 시 상세 패널 열림
- 실시간 진행률 표시 (WebSocket 연동)
- 컬럼별 카드 수 뱃지

#### 1-3. 설계 단계 Kanban

```
[Spec 입력]           [AI 분석중]         [Task 분해됨]        [확정됨]
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ + 파일 업로드 │    │ ◌ Spec #1   │    │ ✎ Task 1    │    │ ✓ Task A    │
│ + 이미지      │    │   분석 45%   │    │ ✎ Task 2    │    │ ✓ Task B    │
│ + 텍스트 입력 │    │             │    │ ✎ Task 3    │    │ ✓ Task C    │
│              │    │             │    │ [전체 확정→] │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

#### 1-4. 개발 단계 Kanban

```
[Backlog]     [Planning]      [Coding]       [Review]        [Done]
┌──────────┐ ┌──────────┐  ┌──────────┐  ┌──────────┐   ┌──────────┐
│ Task A   │ │ Task D   │  │ Task E   │  │ Task F   │   │ Task G ✓ │
│  @Kim    │ │  🤖 계획  │  │  🤖 코딩  │  │ 👤 대기   │   │ Task H ✓ │
│ Task B   │ │  수립중   │  │  진행중   │  │ [승인]    │   │          │
│  @Kim    │ │          │  │  67%     │  │ [거절]    │   │          │
│ [▶ 실행] │ │          │  │          │  │ [자동승인] │   │          │
└──────────┘ └──────────┘  └──────────┘  └──────────┘   └──────────┘
```

**v1.0 대비 변경**: 카드에 담당 사용자(@Kim) 표시 추가

#### 1-5. API 통신 레이어 및 상태 관리

```typescript
// stores/taskStore.ts (Zustand)
interface TaskStore {
  tasks: Task[];
  selectedTask: Task | null;
  currentUser: User | null;          // [v2.0]
  
  // CRUD
  fetchTasks: (projectId: string) => Promise<void>;
  updateTaskStatus: (taskId: string, status: TaskStatus) => Promise<void>;
  
  // Agent 실행 (사용자의 worktree에서)
  runTask: (taskId: string) => Promise<void>;
  
  // WebSocket 기반 실시간 업데이트
  subscribeToUpdates: (projectId: string) => void;
}
```

#### 1-6. [v2.0] Git 관리 탭 구현

Git 관리 탭의 API 엔드포인트:

```python
# backend/app/api/git.py

@router.get("/projects/{project_id}/git/status")
async def get_git_status(project_id: str, user_id: str):
    """사용자 worktree의 변경 파일 목록"""

@router.get("/projects/{project_id}/git/diff")
async def get_file_diff(project_id: str, user_id: str, file_path: str):
    """특정 파일의 diff"""

@router.post("/projects/{project_id}/git/stage")
async def stage_files(project_id: str, user_id: str, file_paths: list[str]):
    """선택된 파일을 staging"""

@router.post("/projects/{project_id}/git/commit")
async def commit(project_id: str, user_id: str, message: str):
    """커밋 실행"""

@router.post("/projects/{project_id}/git/pull")
async def pull(project_id: str, user_id: str, strategy: str = "rebase"):
    """main 변경사항 pull"""

@router.post("/projects/{project_id}/git/push")
async def push(project_id: str, user_id: str):
    """원격에 push"""

@router.get("/projects/{project_id}/git/log")
async def get_log(project_id: str, user_id: str, count: int = 20):
    """커밋 이력"""

@router.post("/projects/{project_id}/git/revert")
async def revert_file(project_id: str, user_id: str, file_path: str):
    """파일 변경사항 되돌리기"""
```

#### 1-7. 검증 기준
- [ ] Kanban 보드에서 카드 드래그 앤 드롭 동작
- [ ] 설계/개발/Git 관리 탭 전환 시 각각의 화면 렌더링
- [ ] 프로젝트 목록 CRUD (API ↔ MySQL 연동)
- [ ] WebSocket 연결 및 테스트 메시지 수신
- [ ] [v2.0] 사용자 선택 시 해당 사용자의 Task만 필터링
- [ ] [v2.0] Git 관리 탭에서 변경 파일 목록, diff 보기, stage/commit 동작

---

### Phase 2: 설계 에이전트 구현 (2주)

**목표**: Spec 입력 → AI 분석 → Task 분해 → 사용자 확인 → DB 저장 파이프라인 완성

#### 2-1. Spec 입력 처리기

지원 포맷 및 처리 방식:

| 입력 유형 | 처리 방법 |
|----------|----------|
| PDF/DOCX | 텍스트 추출 (pymupdf / python-docx) |
| 이미지 | Claude Vision 활용 (base64 인코딩 후 프롬프트에 포함) |
| 마크다운/텍스트 | 직접 전달 |
| URL | requests로 페이지 내용 크롤링 |

#### 2-2. Design Agent 구현

Claude Agent SDK의 `query()` + Structured Output을 활용합니다:

```python
# backend/app/agents/design_agent.py
from claude_agent_sdk import query, ClaudeAgentOptions

async def analyze_spec_and_create_tasks(
    spec_content: str,
    project: Project,              # [v2.0] 프로젝트 스택 정보 포함
    worktree_path: str,            # [v2.0] 코드 분석을 위한 worktree 경로
    websocket_callback
):
    task_schema = {
        "type": "object",
        "properties": {
            "analysis_summary": {"type": "string"},
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "acceptance_criteria": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"]
                        },
                        "complexity": {
                            "type": "string",
                            "enum": ["trivial", "low", "medium", "high", "very_high"]
                        },
                        "dependencies": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "suggested_approach": {"type": "string"}
                    },
                    "required": ["title", "description", "acceptance_criteria",
                                 "priority", "complexity"]
                }
            }
        },
        "required": ["analysis_summary", "tasks"]
    }
    
    # [v2.0] 프로젝트 스택에 맞는 프롬프트 생성
    stack_context = get_stack_context(project)
    
    prompt = f"""
    당신은 소프트웨어 설계 전문가입니다.
    아래 스펙 문서를 분석하여 개발 Task 목록으로 분해해주세요.
    
    ## 프로젝트 컨텍스트
    - 이름: {project.name}
    - 스택: {project.project_stack} / {project.framework}
    {stack_context}
    
    ## Spec 내용
    {spec_content}
    
    ## 규칙
    1. 각 Task는 1-4시간 내 완료 가능한 단위로 분해
    2. Task 간 의존성을 명확히 기술
    3. acceptance_criteria는 검증 가능한 구체적 조건
    4. 기존 코드베이스 구조를 먼저 파악한 후 Task 설계
    5. {project.framework} 프레임워크 규칙을 따를 것
    """
    
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep"],
        permission_mode="bypassPermissions",
        max_turns=30,
        cwd=worktree_path,                          # [v2.0] 사용자 worktree에서 실행
        output_format={"type": "json_schema", "schema": task_schema}
    )
    
    async for message in query(prompt=prompt, options=options):
        await websocket_callback(message)
    
    return parse_task_result(message)


def get_stack_context(project: Project) -> str:
    """[v2.0] 프로젝트 스택에 맞는 추가 컨텍스트를 생성합니다."""
    if project.project_stack == "python" and project.framework == "fastapi":
        return """
    - FastAPI 프로젝트 구조를 따릅니다
    - 라우터는 app/api/ 하위에 배치
    - 모델은 app/models/, 스키마는 app/schemas/
    - 비즈니스 로직은 app/services/
    - 테스트는 tests/ 하위에 pytest로 작성
        """
    elif project.project_stack == "java":
        return """
    - 기존 사내 프레임워크 위에서 작업합니다
    - 기존 패키지 구조와 명명 규칙을 따르세요
    - 먼저 프로젝트 구조를 파악한 후 Task를 설계하세요
        """
    return ""
```

#### 2-3. 이미지 기반 Spec 분석

(v1.0과 동일 — 생략)

#### 2-4. Task 편집 UI

분해된 Task를 사용자가 확인하고 편집하는 화면:

- Task 목록 카드 형태로 표시
- 각 Task 클릭 시 상세 편집 패널
  - 제목, 설명, 수용 조건 편집
  - 우선순위, 복잡도 변경
  - 의존성 연결 (다른 Task 드래그로 연결)
  - [v2.0] 담당 사용자 배정
- Task 병합 / 분리 기능
- "전체 확정" 버튼 → 확정된 Task를 개발 단계 Backlog으로 이동

#### 2-5. 검증 기준
- [ ] PDF/이미지 업로드 → 텍스트 추출 완료
- [ ] AI가 Spec을 분석하여 5개 이상의 Task로 분해
- [ ] 분해된 Task가 Kanban "Task 분해됨" 컬럼에 표시
- [ ] Task 편집 (제목, 설명, 우선순위 변경) 및 DB 반영
- [ ] "확정" 시 개발 단계 Backlog으로 이동
- [ ] [v2.0] 에이전트가 사용자 worktree에서 코드 구조를 분석하여 스택에 맞는 Task 생성

---

### Phase 3: 개발 에이전트 구현 (2.5주) ⭐ 핵심 단계

**목표**: Plan → Code → Review 파이프라인의 자동화 (사용자별 worktree 내 순차 실행)

#### 3-1. Agent Orchestrator 구현

```python
# backend/app/agents/orchestrator.py

class DevOrchestrator:
    """
    Task의 Plan → Code → Review 파이프라인을 관리합니다.
    모든 작업은 사용자의 worktree 내에서 순차적으로 실행됩니다.
    """
    
    def __init__(self, task: Task, project: Project, user_worktree: UserWorktree, db_session):
        self.task = task
        self.project = project
        self.worktree = user_worktree               # [v2.0] 사용자 worktree
        self.db = db_session
        self.ws_manager = WebSocketManager()
        self.security_profile = load_security_profile(project)  # [v2.0]
    
    async def execute(self):
        """전체 파이프라인 실행 (사용자 worktree 내에서)"""
        try:
            # Step 1: Plan
            plan_result = await self._execute_plan()
            
            # Step 1.5: Plan Review (선택사항)
            if not self.task.auto_approve:
                approved = await self._wait_for_plan_approval(plan_result)
                if not approved:
                    return
            
            # Step 2: Code
            code_result = await self._execute_code(plan_result)
            
            # Step 3: Review
            review_result = await self._execute_review(code_result)
            
            # Step 4: 완료 처리
            if review_result.approved:
                self.task.status = "done"
                await self.db.commit()
                # Git commit/push는 사용자가 Git 관리 탭에서 수동 수행
                await self.ws_manager.broadcast({
                    "type": "task_completed",
                    "task_id": self.task.id,
                    "message": "Task 완료. Git 관리 탭에서 변경사항을 확인하고 커밋하세요."
                })
            
        except Exception as e:
            await self._handle_failure(e)
```

#### 3-2. [v2.0] 프로젝트 스택 기반 보안 프로파일

```python
# backend/app/agents/security/profiles.py

# 기본 보안 프로파일 (스택별)
DEFAULT_PROFILES = {
    "python": {
        "allowed_commands": [
            "pip install", "pip list",
            "pytest", "python -m pytest",
            "ruff check", "ruff format",
            "mypy", "black",
            "uvicorn",
            "python -c",
        ],
        "blocked_commands": [
            "rm -rf /", "sudo", "chmod 777",
            "curl | bash", "wget | sh",
            "pip install --user",  # 시스템 패키지 변경 방지
        ],
        "allowed_path_patterns": [
            "app/**", "tests/**",
            "requirements.txt", "pyproject.toml",
        ],
        "blocked_path_patterns": [
            ".env", "*.pem", "*.key",           # 시크릿 파일
            ".git/**",                           # git 내부 파일
            "venv/**", ".venv/**",               # 가상환경
        ],
    },
    "java": {
        "allowed_commands": [
            "mvn", "gradle",
            "java", "javac",
            "mvn test", "gradle test",
            "mvn compile", "gradle build",
        ],
        "blocked_commands": [
            "rm -rf /", "sudo", "chmod 777",
            "curl | bash",
        ],
        "allowed_path_patterns": [
            "src/**", "test/**", "tests/**",
            "pom.xml", "build.gradle",
        ],
        "blocked_path_patterns": [
            ".env", "*.pem", "*.key",
            ".git/**",
            "target/**", "build/**",            # 빌드 산출물
        ],
    },
}
```

```python
# backend/app/agents/security/hooks.py
from claude_agent_sdk import HookMatcher
import fnmatch

class SecurityHookFactory:
    """[v2.0] 프로젝트 스택에 따른 보안 Hook을 생성합니다."""
    
    def __init__(self, profile: dict, worktree_path: str):
        self.profile = profile
        self.worktree_path = worktree_path
    
    async def validate_tool_use(self, input_data, tool_use_id, context):
        """PreToolUse Hook: 보안 프로파일에 따라 도구 사용을 검증합니다."""
        tool_name = input_data["tool_name"]
        tool_input = input_data["tool_input"]
        
        # Bash 명령 검증
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            return self._validate_command(command)
        
        # 파일 쓰기/수정 경로 검증
        if tool_name in ("Write", "Edit"):
            file_path = tool_input.get("file_path", "")
            return self._validate_file_path(file_path)
        
        return {}
    
    def _validate_command(self, command: str) -> dict:
        """명령어가 허용 목록에 있는지 검증"""
        for blocked in self.profile["blocked_commands"]:
            if blocked in command:
                return self._deny(f"차단된 명령어: {blocked}")
        return {}
    
    def _validate_file_path(self, file_path: str) -> dict:
        """파일 경로가 허용 범위 내인지 검증"""
        # worktree 외부 접근 차단
        if not file_path.startswith(self.worktree_path):
            return self._deny(f"worktree 외부 파일 수정 불가: {file_path}")
        
        rel_path = os.path.relpath(file_path, self.worktree_path)
        
        # 차단 경로 확인
        for pattern in self.profile.get("blocked_path_patterns", []):
            if fnmatch.fnmatch(rel_path, pattern):
                return self._deny(f"보호된 경로: {rel_path}")
        
        return {}
    
    def _deny(self, reason: str) -> dict:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    
    def get_hooks(self) -> dict:
        """ClaudeAgentOptions에 전달할 hooks 딕셔너리를 반환합니다."""
        return {
            "PreToolUse": [
                HookMatcher(
                    matcher="Bash|Write|Edit",
                    hooks=[self.validate_tool_use]
                ),
            ],
        }
```

#### 3-3. Plan Agent 구현

```python
# backend/app/agents/plan_agent.py

async def create_development_plan(
    task: Task,
    project: Project,
    worktree_path: str,            # [v2.0] 사용자 worktree 경로
    completed_tasks: list[Task]    # 이미 완료된 관련 Task 참고
) -> PlanResult:
    
    completed_context = format_completed_tasks(completed_tasks)
    stack_context = get_stack_context(project)
    
    prompt = f"""
    당신은 시니어 개발자입니다. 아래 Task에 대한 구체적 개발 계획을 수립하세요.
    
    ## Task 정보
    - 제목: {task.title}
    - 설명: {task.description}
    - 수용 조건: {json.dumps(task.acceptance_criteria, ensure_ascii=False)}
    
    ## 프로젝트 스택
    - 언어: {project.project_stack}
    - 프레임워크: {project.framework}
    {stack_context}
    
    ## 이미 완료된 관련 작업
    {completed_context}
    
    ## 규칙
    1. 프로젝트 구조를 먼저 파악하세요 (파일 구조, 기존 패턴)
    2. 각 단계는 구체적인 파일 경로와 변경 내용을 포함
    3. 테스트 코드도 계획에 포함
    4. 기존 코드 스타일과 패턴을 따르세요
    5. {project.framework} 프레임워크 규칙을 따르세요
    """
    
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep"],  # 읽기 전용
        permission_mode="bypassPermissions",
        max_turns=40,
        cwd=worktree_path,                        # [v2.0] 사용자 worktree
        output_format={"type": "json_schema", "schema": plan_schema}
    )
    
    result = None
    async for message in query(prompt=prompt, options=options):
        await broadcast_progress("planning", message)
        result = message
    
    return parse_plan_result(result)
```

#### 3-4. Code Agent 구현

```python
# backend/app/agents/code_agent.py

class CodeAgent:
    """
    Plan을 기반으로 실제 코드를 생성/수정합니다.
    [v2.0] 사용자 worktree 내에서만 작업하며, 프로젝트 스택 보안 프로파일을 적용합니다.
    """
    
    def __init__(self, task: Task, plan: PlanResult,
                 project: Project, worktree_path: str):
        self.task = task
        self.plan = plan
        self.project = project
        self.worktree_path = worktree_path
        self.code_changes = []
        
        # [v2.0] 보안 프로파일 로드
        security_profile = load_security_profile(project)
        self.security_hooks = SecurityHookFactory(security_profile, worktree_path)
    
    async def track_file_changes(self, input_data, tool_use_id, context):
        """PostToolUse Hook: 파일 변경을 추적합니다."""
        tool_name = input_data["tool_name"]
        if tool_name in ("Write", "Edit"):
            file_path = input_data["tool_input"].get("file_path", "")
            self.code_changes.append({
                "file_path": file_path,
                "tool_name": tool_name,
                "tool_input": input_data["tool_input"],
                "tool_response": input_data.get("tool_response"),
            })
            await self.ws_manager.broadcast({
                "type": "code_change",
                "task_id": self.task.id,
                "file_path": file_path,
                "change_type": "create" if tool_name == "Write" else "modify"
            })
        return {}
    
    async def execute(self) -> CodeResult:
        """코드 생성/수정 실행"""
        
        # [v2.0] 보안 Hook + 변경 추적 Hook 결합
        security_hooks = self.security_hooks.get_hooks()
        combined_hooks = {
            "PreToolUse": security_hooks.get("PreToolUse", []),
            "PostToolUse": [
                HookMatcher(
                    matcher="Write|Edit",
                    hooks=[self.track_file_changes]
                ),
            ],
        }
        
        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            permission_mode="bypassPermissions",
            max_turns=100,
            cwd=self.worktree_path,                # [v2.0] 사용자 worktree
            enable_file_checkpointing=True,
            hooks=combined_hooks,
        )
        
        prompt = f"""
        아래 개발 계획에 따라 코드를 구현하세요.
        
        ## Task
        {self.task.title}: {self.task.description}
        
        ## 프로젝트 스택
        - 언어: {self.project.project_stack}
        - 프레임워크: {self.project.framework}
        
        ## 개발 계획
        {json.dumps(self.plan.to_dict(), ensure_ascii=False)}
        
        ## 수용 조건
        {json.dumps(self.task.acceptance_criteria, ensure_ascii=False)}
        
        ## 규칙
        1. 계획된 순서대로 파일을 생성/수정하세요
        2. 각 파일 수정 후 lint/format 검증
        3. 테스트 코드도 함께 작성
        4. 기존 코드 스타일을 따르세요
        """
        
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            async for message in client.receive_response():
                await self.ws_manager.broadcast({
                    "type": "agent_message",
                    "task_id": self.task.id,
                    "message": serialize_message(message)
                })
        
        return CodeResult(changes=self.code_changes)
```

#### 3-5. Review 시스템 구현

(v1.0과 동일 구조 — Human Review UI + Auto-approve 조건 검증)

**자동 승인 조건:**
```python
interface AutoApprovalConfig:
    lint_pass: bool       # lint 통과 필수 (ruff/checkstyle)
    test_pass: bool       # test 통과 필수 (pytest/junit)
    max_files_changed: int  # 변경 파일 수 제한
    blocked_paths: list[str]  # 수정 금지 경로
```

#### 3-6. 파이프라인 상태 전이 (순차 실행)

```python
# [v2.0] 순차 실행 — Task 의존성 순서를 자동 결정
async def run_task_queue(project_id: str, user_id: str):
    """
    의존성을 고려하여 올바른 순서로 Task를 순차 실행합니다.
    모든 Task는 해당 사용자의 worktree 내에서 실행됩니다.
    """
    tasks = get_pending_tasks(project_id, user_id)
    execution_order = topological_sort(tasks)  # 의존성 기반 위상 정렬
    
    worktree = get_user_worktree(user_id, project_id)
    
    for task in execution_order:
        # 의존성 확인
        if not all_dependencies_completed(task):
            task.status = "failed"
            task.failure_reason = "선행 Task 미완료"
            continue
        
        orchestrator = DevOrchestrator(
            task=task,
            project=project,
            user_worktree=worktree,
            db_session=db
        )
        await orchestrator.execute()
        
        # 순차 실행이므로 다음 Task로 넘어가기 전에 완료 확인
        if task.status != "done":
            break  # 실패 시 중단 (또는 설정에 따라 스킵)
```

#### 3-7. 검증 기준
- [ ] Task를 Backlog에서 "실행" 시 Plan → Code → Review 자동 진행
- [ ] Plan 결과가 UI에 표시되고, 사용자가 승인/거절 가능
- [ ] Code Agent가 **사용자의 worktree 내에서** 파일을 생성/수정
- [ ] [v2.0] 보안 프로파일에 따라 위험 명령/금지 경로가 차단
- [ ] [v2.0] Task 완료 후 Git 관리 탭에서 변경사항 확인 가능
- [ ] Auto-approve 조건 설정 및 자동 승인 동작
- [ ] Human Review에서 승인/거절/수정요청 동작
- [ ] 거절 시 이전 단계로 롤백 (File Checkpointing 활용)
- [ ] [v2.0] 의존성 순서에 따른 순차 실행

---

### Phase 4: 통합 및 고급 기능 (1.5주)

#### 4-1. 설계 → 개발 단계 자동 연결

설계 단계에서 "확정"된 Task가 자동으로 개발 단계 Backlog에 추가되는 흐름.
[v2.0] 확정 시 담당 사용자 배정 UI 포함.

#### 4-2. 실시간 진행 상황 고도화

에이전트 실행 중 Frontend에 표시할 정보:

```typescript
interface AgentProgress {
  taskId: string;
  phase: 'planning' | 'coding' | 'reviewing';
  currentAction: {
    tool: string;
    description: string;
    timestamp: number;
  };
  progress: {
    current: number;
    total: number;
    percentage: number;
  };
  logs: AgentLogEntry[];
  worktreePath: string;          // [v2.0] 어느 worktree에서 작업 중인지
}
```

#### 4-3. Task 의존성 관리 (순차 실행용)

```typescript
// [v2.0] 의존성 기반 실행 순서 결정 (위상 정렬)
// 병렬 실행은 하지 않고, 올바른 순서만 결정
function getExecutionOrder(tasks: Task[]): Task[] {
  // DAG 기반 위상 정렬
  // 반환: [Task1, Task2, Task3, Task4, Task5]
  //        순차적으로 하나씩 실행
}
```

UI에서 의존성 시각화:
- Task 카드에 의존하는 Task 뱃지 표시
- 의존성 미충족 시 실행 버튼 비활성화

#### 4-4. Diff Viewer 고도화

Monaco Editor 기반 Diff Viewer (v1.0과 동일)

#### 4-5. 에러 복구 및 재시도

```python
class RetryStrategy:
    """에이전트 실패 시 재시도 전략"""
    
    async def handle_failure(self, task: Task, error: Exception, step: str):
        if isinstance(error, RateLimitError):
            await asyncio.sleep(60)
            return RetryAction.RETRY_SAME
        
        elif isinstance(error, ToolExecutionError):
            return RetryAction.RETRY_WITH_DIFFERENT_APPROACH
        
        elif isinstance(error, ContextOverflow):
            return RetryAction.SPLIT_TASK
        
        else:
            return RetryAction.REPORT_TO_USER
```

#### 4-6. 검증 기준
- [ ] 설계 확정 → 개발 Backlog 자동 이동
- [ ] 에이전트 실행 중 실시간 로그 스트리밍
- [ ] Diff Viewer에서 변경사항 확인 가능
- [ ] 의존성 있는 Task는 선행 Task 완료 후 실행 가능
- [ ] API Rate Limit 시 자동 재시도

---

### Phase 5: Electron 패키징 및 배포 (1주)

#### 5-1. Python 백엔드 번들링

**Option A: PyInstaller로 단일 실행파일** (권장)

```bash
pyinstaller --onefile --name code-agent-backend app/main.py
```

```typescript
// electron/python-manager.ts
class PythonManager {
  private process: ChildProcess | null = null;
  
  async start() {
    const backendPath = app.isPackaged
      ? path.join(process.resourcesPath, 'backend', 'code-agent-backend')
      : 'uvicorn';
    
    const args = app.isPackaged
      ? ['--port', '8000']
      : ['app.main:app', '--port', '8000'];
    
    this.process = spawn(backendPath, args, {
      cwd: app.isPackaged 
        ? path.join(process.resourcesPath, 'backend')
        : path.join(__dirname, '..', 'backend'),
      env: {
        ...process.env,
        ANTHROPIC_API_KEY: await getApiKey(),
      }
    });
    
    await this.waitForReady();
  }
  
  async stop() {
    this.process?.kill();
  }
}
```

**Option B: 시스템 Python 요구** (대안)
- 사용자 시스템에 Python 설치 필요
- 첫 실행 시 venv 자동 생성 및 의존성 설치

#### 5-2. API 키 보안 저장

```typescript
import keytar from 'keytar';
const SERVICE_NAME = 'code-agent';

export async function saveApiKey(key: string) {
  await keytar.setPassword(SERVICE_NAME, 'anthropic-api-key', key);
}

export async function getApiKey(): Promise<string | null> {
  return keytar.getPassword(SERVICE_NAME, 'anthropic-api-key');
}
```

#### 5-3. Electron Builder 설정

```yaml
appId: com.your-org.code-agent
productName: Code Agent
directories:
  buildResources: build
files:
  - dist/**/*
  - electron/**/*
extraResources:
  - from: backend/dist/
    to: backend/
    filter:
      - "**/*"
mac:
  category: public.app-category.developer-tools
  target: [dmg, zip]
win:
  target: [nsis, portable]
linux:
  target: [AppImage, deb]
```

#### 5-4. 시스템 통합 기능

- 파일 선택 다이얼로그 (프로젝트 폴더 선택)
- 시스템 알림 (Task 완료, Review 대기 등)
- 트레이 아이콘 + 백그라운드 실행
- 자동 업데이트 (electron-updater)

#### 5-5. 검증 기준
- [ ] `npm run build` → 설치 가능한 패키지 생성
- [ ] 설치된 앱에서 Python 백엔드 자동 시작
- [ ] API 키 설정 → 에이전트 실행 정상 동작
- [ ] Windows/Mac 모두에서 동작 확인

---

## 4. 개선 제안 요약 (v2.0 최종)

| # | 원래 요구사항 | 개선/결정 | 이유 |
|---|-------------|----------|------|
| 1 | Plan → Code → Review 3단계 | **Plan → Plan Review(선택) → Code → Review** | 잘못된 계획으로 코드 생성 시 시간 낭비 방지 |
| 2 | 자동 승인 여부만 설정 | **조건부 자동 승인** (lint/test/파일수) | 안전하면서도 유연한 자동화 |
| 3 | 명시 없음 | **File Checkpointing 활용** | SDK 내장 기능으로 롤백 간편 |
| 4 | 명시 없음 | **Subagents 활용** (Plan/Code 분리) | 컨텍스트 격리, 각 단계 최적화 |
| 5 | 명시 없음 | **PreToolUse Hook 보안 + 스택 프로파일** | Python/Java 맞춤 보안 |
| 6 | 명시 없음 | **PostToolUse Hook으로 변경 추적** | 실시간 Diff 표시, DB 기록 |
| 7 | 명시 없음 | **Task 의존성 위상 정렬 (순차 실행)** | 올바른 실행 순서 보장 |
| 8 | 명시 없음 | **에러 복구/재시도 전략** | Rate Limit, 컨텍스트 초과 대응 |
| 9 | 명시 없음 | **사용자별 worktree + Git 관리 탭** | 안전한 코드 격리, 수동 commit/push/PR |

---

## 5. 전체 타임라인

```
Week 1           : Phase 0 — 프로젝트 구조, DB 스키마, Worktree 서비스, 빌드 환경
Week 2 ~ 3 초    : Phase 1 — Kanban UI, Git 관리 탭, 사용자/Worktree 관리, WebSocket
Week 3 중 ~ 5    : Phase 2 — 설계 에이전트 (Spec 분석, Task 분해, 스택별 프롬프트)
Week 5 ~ 7 중    : Phase 3 — 개발 에이전트 (Plan, Code, Review, 보안 프로파일) ⭐
Week 7 중 ~ 9    : Phase 4 — 통합, Diff Viewer, 의존성 순서, 에러 복구
Week 9 ~ 10      : Phase 5 — Electron 패키징, 보안, 배포
──────────────────────────────────────────────────────────────
총 약 10주 (2.5개월)
```

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| Claude API Rate Limit | 개발 에이전트 중단 | 재시도 + 큐 기반 순차 실행 |
| 대규모 프로젝트 컨텍스트 초과 | 에이전트 품질 저하 | 관련 파일만 선별적 포함, Compaction 활용 |
| Python 백엔드 Electron 번들링 | 설치 파일 용량 증가 | PyInstaller 최적화 or Python 사전 설치 요구 |
| Claude Agent SDK 버전 변경 | 호환성 문제 | SDK 버전 고정, CHANGELOG 모니터링 |
| MySQL 외부 연결 불안정 | 데이터 손실 | 연결 풀 + 재시도 + 로컬 캐시 |
| [v2.0] Worktree 상태 불일치 | 에이전트 실행 오류 | worktree 상태 검증 후 실행, git pull 자동화 |
| [v2.0] 보안 프로파일 우회 | 의도치 않은 파일 손상 | Hook 기반 다층 방어, 중요 파일 읽기 전용 설정 |

---

## 7. 향후 확장 (Post-MVP)

아래 기능은 MVP 완료 후 필요에 따라 추가합니다:

| 기능 | 시기 | 설명 |
|------|------|------|
| **QA 자동 수정 루프** | Phase 6 (기획 확정 후) | Code 완료 후 자동 QA → 실패 시 자동 수정 → 재검증 반복 |
| **세션 간 메모리** | 필요 시 | 프로젝트 패턴 학습이 필요해질 때 벡터 DB 검토 |
| **GitHub/GitLab 연동** | Phase 7 | PR 자동 생성, Issue import, 코드 리뷰 연동 |
| **다중 사용자 동시 작업 모니터링** | Phase 7 | 여러 사용자의 에이전트 실행 현황을 대시보드로 표시 |
| **커스텀 프롬프트 템플릿** | Phase 7 | 프로젝트/팀별 에이전트 프롬프트 커스터마이징 |
