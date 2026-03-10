import axios from 'axios';
import type {
  GitFileStatus,
  GitLogEntry,
  Project,
  ProjectCreate,
  Spec,
  Task,
  TaskCreate,
  TaskUpdate,
  User,
  UserWorktree,
} from '../types';

const BASE_URL = 'http://localhost:8000';

// Axios 인스턴스 — 모든 요청의 baseURL과 기본 헤더를 공유
const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ── Projects ──────────────────────────────────────────────────────────────────

export const projectsApi = {
  /** 전체 프로젝트 목록 조회 */
  list: () => api.get<Project[]>('/api/projects').then(r => r.data),

  /** 특정 프로젝트 단건 조회 */
  get: (id: string) => api.get<Project>(`/api/projects/${id}`).then(r => r.data),

  /** 새 프로젝트 생성 */
  create: (body: ProjectCreate) => api.post<Project>('/api/projects', body).then(r => r.data),

  /** 프로젝트 정보 수정 (이름, 상태, repo_url 등) */
  update: (id: string, body: Partial<ProjectCreate & { status: string }>) =>
    api.patch<Project>(`/api/projects/${id}`, body).then(r => r.data),

  /** 프로젝트 삭제 */
  remove: (id: string) => api.delete(`/api/projects/${id}`).then(r => r.data),
};

// ── Users ─────────────────────────────────────────────────────────────────────

export const usersApi = {
  /** 전체 사용자 목록 조회 */
  list: () => api.get<User[]>('/api/users').then(r => r.data),

  /** 특정 사용자 단건 조회 */
  get: (id: string) => api.get<User>(`/api/users/${id}`).then(r => r.data),

  /** 새 사용자 생성 */
  create: (body: { username: string; display_name?: string }) =>
    api.post<User>('/api/users', body).then(r => r.data),
};

// ── Worktrees ─────────────────────────────────────────────────────────────────

export const worktreesApi = {
  /** 프로젝트에 속한 사용자별 worktree 목록 조회 */
  list: (projectId: string) =>
    api.get<UserWorktree[]>(`/api/projects/${projectId}/worktrees`).then(r => r.data),

  /** 특정 사용자의 worktree 생성 (브랜치 분기) */
  create: (projectId: string, body: { user_id: string; branch_name: string }) =>
    api.post<UserWorktree>(`/api/projects/${projectId}/worktrees`, body).then(r => r.data),

  /** worktree 제거 */
  remove: (worktreeId: string) =>
    api.delete(`/api/worktrees/${worktreeId}`).then(r => r.data),
};

// ── Tasks ─────────────────────────────────────────────────────────────────────

export const tasksApi = {
  /** 프로젝트의 전체 Task 목록 조회 */
  list: (projectId: string) =>
    api.get<Task[]>(`/api/projects/${projectId}/tasks`).then(r => r.data),

  /** 특정 Task 단건 조회 */
  get: (taskId: string) => api.get<Task>(`/api/tasks/${taskId}`).then(r => r.data),

  /** 새 Task 생성 */
  create: (projectId: string, body: TaskCreate) =>
    api.post<Task>(`/api/projects/${projectId}/tasks`, body).then(r => r.data),

  /** Task 정보 수정 (상태, 담당자, 우선순위 등) */
  update: (taskId: string, body: TaskUpdate) =>
    api.patch<Task>(`/api/tasks/${taskId}`, body).then(r => r.data),
};

// ── Specs ─────────────────────────────────────────────────────────────────────

export const specsApi = {
  /** 프로젝트의 전체 Spec 목록 조회 */
  list: (projectId: string) =>
    api.get<Spec[]>(`/api/projects/${projectId}/specs`).then(r => r.data),

  /** Spec 파일 업로드 (문서/이미지/텍스트) */
  upload: (projectId: string, formData: FormData) =>
    api
      .post<Spec>(`/api/projects/${projectId}/specs`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then(r => r.data),

  /** Spec 삭제 */
  remove: (specId: string) => api.delete(`/api/specs/${specId}`).then(r => r.data),
};

// ── Git ───────────────────────────────────────────────────────────────────────

export const gitApi = {
  /** 사용자 worktree의 변경 파일 목록 조회 (git status) */
  status: (projectId: string, userId: string) =>
    api
      .get<GitFileStatus[]>(`/api/projects/${projectId}/git/status`, { params: { user_id: userId } })
      .then(r => r.data),

  /** 특정 파일의 변경 내용 조회 (git diff). staged=true이면 staged diff 반환 */
  diff: (projectId: string, userId: string, filePath: string, staged = false) =>
    api
      .get<{ diff: string }>(`/api/projects/${projectId}/git/diff`, {
        params: { user_id: userId, file_path: filePath, staged },
      })
      .then(r => r.data),

  /** 선택한 파일들을 staging area에 추가 (git add) */
  stage: (projectId: string, userId: string, filePaths: string[]) =>
    api
      .post(`/api/projects/${projectId}/git/stage`, { file_paths: filePaths }, { params: { user_id: userId } })
      .then(r => r.data),

  /** staged 파일들을 커밋 (git commit -m) */
  commit: (projectId: string, userId: string, message: string) =>
    api
      .post(`/api/projects/${projectId}/git/commit`, { message }, { params: { user_id: userId } })
      .then(r => r.data),

  /** 원격 브랜치에서 변경사항을 가져옴 (git pull). strategy: rebase | merge */
  pull: (projectId: string, userId: string, strategy: 'rebase' | 'merge' = 'rebase') =>
    api
      .post(`/api/projects/${projectId}/git/pull`, { strategy }, { params: { user_id: userId } })
      .then(r => r.data),

  /** 현재 브랜치를 원격에 push (git push) */
  push: (projectId: string, userId: string) =>
    api
      .post(`/api/projects/${projectId}/git/push`, {}, { params: { user_id: userId } })
      .then(r => r.data),

  /** 커밋 히스토리 조회 (git log). count: 최대 반환 개수 */
  log: (projectId: string, userId: string, count = 20) =>
    api
      .get<GitLogEntry[]>(`/api/projects/${projectId}/git/log`, {
        params: { user_id: userId, count },
      })
      .then(r => r.data),

  /** 특정 파일의 변경사항을 되돌림 (git checkout -- <file>) */
  revert: (projectId: string, userId: string, filePath: string) =>
    api
      .post(`/api/projects/${projectId}/git/revert`, null, {
        params: { user_id: userId, file_path: filePath },
      })
      .then(r => r.data),

  /** 현재 체크아웃된 브랜치 이름 조회 (git branch --show-current) */
  branch: (projectId: string, userId: string) =>
    api
      .get<{ branch: string }>(`/api/projects/${projectId}/git/branch`, {
        params: { user_id: userId },
      })
      .then(r => r.data),
};

export default api;
