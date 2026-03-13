-- ============================================
-- 프로젝트 관리
-- ============================================
CREATE TABLE projects (
    id              VARCHAR(36) PRIMARY KEY,        -- UUID
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    project_type    ENUM('new', 'existing') NOT NULL DEFAULT 'existing',  -- 신규/기존 프로젝트 구분
    repo_url        VARCHAR(500) NOT NULL,           -- Git 저장소 URL
    local_repo_path VARCHAR(1000),                  -- 로컬 코드베이스 경로
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