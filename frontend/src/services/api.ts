/* ──────────────────────────────────────
   REST API client for FastAPI backend
   ────────────────────────────────────── */

const BASE_URL = '/api';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Projects ─────────────────────────
export const projectsApi = {
  list: () => request<any[]>('/projects'),
  get: (id: string) => request<any>(`/projects/${id}`),
  create: (data: any) => request<any>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any) => request<any>(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) => request<void>(`/projects/${id}`, { method: 'DELETE' }),
};

// ── Users ────────────────────────────
export const usersApi = {
  list: () => request<any[]>('/users'),
  get: (id: string) => request<any>(`/users/${id}`),
  create: (data: any) => request<any>('/users', { method: 'POST', body: JSON.stringify(data) }),
};

// ── Tasks ────────────────────────────
export const tasksApi = {
  list: (params?: { project_id?: string; assigned_user_id?: string; status?: string }) => {
    const qs = new URLSearchParams(Object.entries(params || {}).filter(([_, v]) => v)).toString();
    return request<any[]>(`/tasks${qs ? `?${qs}` : ''}`);
  },
  get: (id: string) => request<any>(`/tasks/${id}`),
  create: (data: any) => request<any>('/tasks', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any) => request<any>(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) => request<void>(`/tasks/${id}`, { method: 'DELETE' }),
};

// ── Specs ────────────────────────────
export const specsApi = {
  list: (projectId?: string) => {
    const qs = projectId ? `?project_id=${projectId}` : '';
    return request<any[]>(`/specs${qs}`);
  },
  create: (data: any) => request<any>('/specs', { method: 'POST', body: JSON.stringify(data) }),
};

// ── Worktrees ────────────────────────
export const worktreesApi = {
  list: (params?: { project_id?: string; user_id?: string }) => {
    const qs = new URLSearchParams(Object.entries(params || {}).filter(([_, v]) => v)).toString();
    return request<any[]>(`/worktrees${qs ? `?${qs}` : ''}`);
  },
  create: (data: any) => request<any>('/worktrees', { method: 'POST', body: JSON.stringify(data) }),
};

// ── Git Management ───────────────────
export const gitApi = {
  status: (projectId: string, userId: string) =>
    request<any[]>(`/projects/${projectId}/git/status?user_id=${userId}`),
  diff: (projectId: string, userId: string, filePath: string, staged = false) =>
    request<{ diff: string }>(`/projects/${projectId}/git/diff?user_id=${userId}&file_path=${encodeURIComponent(filePath)}&staged=${staged}`),
  stage: (projectId: string, userId: string, filePaths: string[]) =>
    request<any>(`/projects/${projectId}/git/stage?user_id=${userId}`, { method: 'POST', body: JSON.stringify({ file_paths: filePaths }) }),
  commit: (projectId: string, userId: string, message: string) =>
    request<any>(`/projects/${projectId}/git/commit?user_id=${userId}`, { method: 'POST', body: JSON.stringify({ message }) }),
  pull: (projectId: string, userId: string, strategy = 'rebase') =>
    request<any>(`/projects/${projectId}/git/pull?user_id=${userId}`, { method: 'POST', body: JSON.stringify({ strategy }) }),
  push: (projectId: string, userId: string) =>
    request<any>(`/projects/${projectId}/git/push?user_id=${userId}`, { method: 'POST' }),
  log: (projectId: string, userId: string, count = 20) =>
    request<any[]>(`/projects/${projectId}/git/log?user_id=${userId}&count=${count}`),
  revert: (projectId: string, userId: string, filePath: string) =>
    request<any>(`/projects/${projectId}/git/revert?user_id=${userId}&file_path=${encodeURIComponent(filePath)}`, { method: 'POST' }),
  branch: (projectId: string, userId: string) =>
    request<{ branch: string }>(`/projects/${projectId}/git/branch?user_id=${userId}`),
};

// ── Agent ────────────────────────────
export const agentApi = {
  run: (taskId: string) => request<any>(`/agent/run/${taskId}`, { method: 'POST' }),
};
