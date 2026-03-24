import type { GitFileStatus, GitLogEntry, Project, Task, User } from '../types';

// ── Projects ──────────────────────────────────────────────────────────────────

export const MOCK_PROJECTS: Project[] = [
  {
    id: 'p1',
    name: 'Proj A',
    description: '사용자 인증 시스템',
    repo_url: null,
    main_branch: 'main',
    project_stack: 'python',
    framework: 'fastapi',
    status: 'developing',
    created_at: '2026-03-01T09:00:00Z',
    updated_at: '2026-03-11T14:00:00Z',
  },
  {
    id: 'p2',
    name: 'Proj B',
    description: '대시보드 UI',
    repo_url: null,
    main_branch: 'main',
    project_stack: 'python',
    framework: null,
    status: 'designing',
    created_at: '2026-03-05T09:00:00Z',
    updated_at: '2026-03-10T10:00:00Z',
  },
  {
    id: 'p3',
    name: 'Proj C',
    description: 'Java 마이크로서비스',
    repo_url: null,
    main_branch: 'main',
    project_stack: 'java',
    framework: 'spring',
    status: 'setup',
    created_at: '2026-03-09T09:00:00Z',
    updated_at: '2026-03-09T09:00:00Z',
  },
];

// ── Users ─────────────────────────────────────────────────────────────────────

export const MOCK_USERS: User[] = [
  { id: 'u1', username: 'kim', display_name: 'Kim', created_at: '2026-03-01T00:00:00Z' },
  { id: 'u2', username: 'lee', display_name: 'Lee', created_at: '2026-03-01T00:00:00Z' },
];

// ── Tasks ─────────────────────────────────────────────────────────────────────
// 상태 흐름:
//   설계 칸반: backlog(Spec 입력) → planning(AI 분석중) → plan_review(Task 분해됨) → coding(확정됨)
//   개발 칸반: backlog(Backlog) → planning(Planning) → coding(Coding) → reviewing(Review) → done(Done)

export const MOCK_TASKS: Task[] = [
  // ── 설계 단계 작업 ──
  {
    id: 'd1',
    project_id: 'p1',
    spec_id: null,
    assigned_user_id: 'u1',
    title: '사용자 인증 Spec',
    description: '로그인/회원가입/OAuth 플로우 정의',
    acceptance_criteria: null,
    status: 'backlog',
    git_commit_hash: null,
    created_at: '2026-03-10T09:00:00Z',
    updated_at: '2026-03-10T09:00:00Z',
  },
  {
    id: 'd2',
    project_id: 'p1',
    spec_id: null,
    assigned_user_id: 'u2',
    title: 'API 설계 문서',
    description: 'REST API 엔드포인트 명세',
    acceptance_criteria: null,
    status: 'planning',
    git_commit_hash: null,
    created_at: '2026-03-10T10:00:00Z',
    updated_at: '2026-03-11T09:00:00Z',
  },
  {
    id: 'd3',
    project_id: 'p1',
    spec_id: null,
    assigned_user_id: 'u1',
    title: 'DB 스키마 정의',
    description: '사용자/세션 테이블 설계',
    acceptance_criteria: null,
    status: 'plan_review',
    git_commit_hash: null,
    created_at: '2026-03-10T11:00:00Z',
    updated_at: '2026-03-11T10:00:00Z',
  },
  {
    id: 'd4',
    project_id: 'p1',
    spec_id: null,
    assigned_user_id: 'u2',
    title: 'UI/UX 가이드라인',
    description: '컴포넌트 디자인 시스템 정의',
    acceptance_criteria: null,
    status: 'plan_review',
    git_commit_hash: null,
    created_at: '2026-03-10T12:00:00Z',
    updated_at: '2026-03-11T11:00:00Z',
  },

  // ── 개발 단계 작업 ──
  {
    id: 'v1',
    project_id: 'p1',
    spec_id: null,
    assigned_user_id: 'u1',
    title: '로그인 API 구현',
    description: 'POST /auth/login 엔드포인트',
    acceptance_criteria: null,
    status: 'backlog',
    git_commit_hash: null,
    created_at: '2026-03-11T09:00:00Z',
    updated_at: '2026-03-11T09:00:00Z',
  },
  {
    id: 'v2',
    project_id: 'p1',
    spec_id: null,
    assigned_user_id: 'u1',
    title: '회원가입 플로우',
    description: '이메일 검증 포함 회원가입',
    acceptance_criteria: null,
    status: 'planning',
    git_commit_hash: null,
    created_at: '2026-03-11T09:30:00Z',
    updated_at: '2026-03-11T13:00:00Z',
  },
  {
    id: 'v3',
    project_id: 'p1',
    spec_id: null,
    assigned_user_id: 'u2',
    title: '프로필 수정 기능',
    description: 'PATCH /users/{id} 엔드포인트',
    acceptance_criteria: null,
    status: 'coding',
    git_commit_hash: null,
    created_at: '2026-03-11T10:00:00Z',
    updated_at: '2026-03-11T14:00:00Z',
  },
  {
    id: 'v4',
    project_id: 'p1',
    spec_id: null,
    assigned_user_id: 'u2',
    title: '이메일 인증 모듈',
    description: '인증 링크 발송 및 토큰 검증',
    acceptance_criteria: null,
    status: 'reviewing',
    git_commit_hash: null,
    created_at: '2026-03-11T08:00:00Z',
    updated_at: '2026-03-11T12:30:00Z',
  },
  {
    id: 'v5',
    project_id: 'p1',
    spec_id: null,
    assigned_user_id: 'u1',
    title: 'JWT 토큰 서비스',
    description: 'Access/Refresh 토큰 발급 및 검증',
    acceptance_criteria: null,
    status: 'done',
    git_commit_hash: 'abc1234',
    created_at: '2026-03-10T14:00:00Z',
    updated_at: '2026-03-11T11:00:00Z',
  },
  {
    id: 'v6',
    project_id: 'p1',
    spec_id: null,
    assigned_user_id: 'u2',
    title: '비밀번호 재설정',
    description: '이메일 기반 비밀번호 초기화',
    acceptance_criteria: null,
    status: 'done',
    git_commit_hash: 'def5678',
    created_at: '2026-03-10T16:00:00Z',
    updated_at: '2026-03-11T10:00:00Z',
  },
];

// ── Git Mock Data ─────────────────────────────────────────────────────────────

export const MOCK_GIT_FILES: GitFileStatus[] = [
  { status: 'M', path: 'app/api/auth.py' },
  { status: 'M', path: 'app/models/user.py' },
  { status: 'A', path: 'app/services/jwt_service.py' },
  { status: '?', path: 'app/tests/test_auth.py' },
  { status: 'M', path: 'requirements.txt' },
];

export const MOCK_GIT_LOG: GitLogEntry[] = [
  { hash: 'abc1234567', short_hash: 'abc1234', message: 'feat: JWT 토큰 서비스 구현', author: 'Kim', relative_date: '2시간 전' },
  { hash: 'def5678901', short_hash: 'def5678', message: 'fix: 비밀번호 재설정 이메일 발송 수정', author: 'Lee', relative_date: '5시간 전' },
  { hash: 'ghi9012345', short_hash: 'ghi9012', message: 'refactor: 서비스 레이어 분리', author: 'Kim', relative_date: '1일 전' },
  { hash: 'jkl3456789', short_hash: 'jkl3456', message: 'chore: 의존성 업데이트', author: 'Lee', relative_date: '2일 전' },
];

export const MOCK_DIFF = `--- a/app/api/auth.py
+++ b/app/api/auth.py
@@ -45,8 +45,12 @@ class AuthService:

     def authenticate(self, username: str, password: str):
-        user = self.db.find_user(username)
-        if not user:
-            raise HTTPException(status_code=401)
+        user = self.user_repo.find_by_username(username)
+        if not user or not user.is_active:
+            raise HTTPException(
+                status_code=401,
+                detail="Invalid credentials"
+            )
         return self._create_token(user)

     def _create_token(self, user: User) -> str:
-        payload = {"sub": user.id}
+        payload = {"sub": user.id, "type": "access"}
         return jwt.encode(payload, self.secret, algorithm="HS256")`;

// ── Console Mock Log ──────────────────────────────────────────────────────────

export const MOCK_LOGS = [
  { time: '14:20:01', level: 'info' as const, msg: '에이전트 시작: Task #v3 프로필 수정 기능' },
  { time: '14:20:04', level: 'success' as const, msg: '[Read] app/models/user.py 읽기 완료 (142줄)' },
  { time: '14:20:06', level: 'success' as const, msg: '[Read] app/api/users.py 읽기 완료 (89줄)' },
  { time: '14:20:10', level: 'success' as const, msg: '[Edit] app/api/users.py 수정 완료 — PATCH /users/{id} 추가' },
  { time: '14:20:14', level: 'success' as const, msg: '[Write] app/schemas/user.py 생성 완료' },
  { time: '14:20:18', level: 'warn' as const, msg: '[Bash] pytest 실행 중 — 3/5 통과' },
  { time: '14:20:20', level: 'error' as const, msg: '[Bash] test_update_profile 실패: AssertionError: 422 != 200' },
  { time: '14:20:22', level: 'info' as const, msg: '오류 분석 중 — 요청 스키마 검토' },
  { time: '14:20:26', level: 'success' as const, msg: '[Edit] app/schemas/user.py 수정 — optional 필드 추가' },
  { time: '14:20:30', level: 'success' as const, msg: '[Bash] pytest 재실행 — 5/5 통과' },
  { time: '14:20:31', level: 'success' as const, msg: '✓ Task #v3 완료 (67% → 100%)' },
];
