-- ============================================
-- 프로젝트 관리
-- ============================================
CREATE TABLE projects (
    id              VARCHAR(36) PRIMARY KEY,        -- UUID
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    project_type    ENUM('new', 'existing') NOT NULL DEFAULT 'existing',
    repo_url        VARCHAR(500),                   -- Git 저장소 URL (nullable)
    local_repo_path VARCHAR(1000) NOT NULL,         -- 로컬 코드베이스 경로
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
    display_name    VARCHAR(255),                   -- 표시 이름
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
    source_type     ENUM('document', 'image', 'text') NOT NULL,
    source_path     VARCHAR(500),                   -- 파일 경로 or URL
    raw_content     TEXT,                           -- 원본 텍스트 (추출된)
    status          ENUM('uploaded', 'analyzing', 'analyzed', 'final_confirmed') DEFAULT 'uploaded',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- ============================================
-- Task 관리 (설계 → 개발 연결점)
-- ============================================
-- test_data.tasks definition

CREATE TABLE `tasks` (
  `id` varchar(36) NOT NULL,
  `project_id` varchar(36) NOT NULL,
  `spec_id` varchar(36) DEFAULT NULL,
  `assigned_user_id` varchar(36) DEFAULT NULL,
  `title` varchar(500) NOT NULL,
  `description` text NOT NULL,
  `status` enum('plan_reviewing','confirmed','coding','reviewing','done','failed') DEFAULT 'plan_reviewing',
  `acceptance_criteria` longtext DEFAULT NULL COMMENT 'task 성공 조건',
  `target_files` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '작업해야하는 파일 경로',
  `implementation_steps` longtext DEFAULT NULL,
  `git_commit_hash` varchar(40) DEFAULT NULL,
  `started_at` datetime DEFAULT NULL COMMENT '시작 시분초',
  `completed_at` datetime DEFAULT NULL COMMENT '완료 시분초',
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `project_id` (`project_id`),
  KEY `spec_id` (`spec_id`),
  KEY `assigned_user_id` (`assigned_user_id`),
  CONSTRAINT `tasks_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
  CONSTRAINT `tasks_ibfk_2` FOREIGN KEY (`spec_id`) REFERENCES `specs` (`id`) ON DELETE SET NULL,
  CONSTRAINT `tasks_ibfk_3` FOREIGN KEY (`assigned_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ============================================
-- 프로젝트 스택 보안 프로파일
-- ============================================
CREATE TABLE security_profiles (
    id              VARCHAR(36) PRIMARY KEY,
    project_id      VARCHAR(36) NOT NULL,
    stack_type      ENUM('python', 'java', 'other') NOT NULL,
    allowed_commands JSON NOT NULL,                 -- ["pip", "pytest", "ruff", ...]
    blocked_commands JSON NOT NULL,                 -- ["rm -rf", "sudo", ...]
    allowed_paths    JSON,                          -- 수정 허용 경로 패턴
    blocked_paths    JSON,                          -- 수정 차단 경로 패턴
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

-- ============================================
-- 런타임 에러 기록
-- ============================================
CREATE TABLE runtime_errors (
    id              VARCHAR(36) PRIMARY KEY,
    error_code      VARCHAR(50) NOT NULL,
    message         TEXT NOT NULL,
    project_id      VARCHAR(255) NOT NULL,          -- 인덱스용 (FK 없음)
    level           ENUM('error', 'warning', 'critical', 'info') NOT NULL DEFAULT 'error',
    error_timestamp TIMESTAMP NULL,
    metadata        JSON,                           -- 추가 메타데이터
    fix_suggestion  TEXT,
    status          ENUM('pending', 'analyzing', 'analyzed', 'resolved', 'ignored') NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_runtime_errors_project_id (project_id)
);
