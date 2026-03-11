import client from '../client';
import type {
  Project,
  ProjectCreate,
  Task,
  TaskCreate,
  TaskUpdate,
  Spec,
  GitFileStatus,
  GitLogEntry,
} from './projectTypes';

// ── Projects ──────────────────────────────────────────────────────────────────

/** 전체 프로젝트 목록 조회 */
export async function getProjects(): Promise<Project[]> {
  const response = await client.get<Project[]>('/api/projects');
  return response.data;
}

/** 특정 프로젝트 단건 조회 */
export async function getProject(id: string): Promise<Project> {
  const response = await client.get<Project>(`/api/projects/${id}`);
  return response.data;
}

/** 새 프로젝트 생성 */
export async function createProject(body: ProjectCreate): Promise<Project> {
  const response = await client.post<Project>('/api/projects', body);
  return response.data;
}

/** 프로젝트 정보 수정 (이름, 상태, repo_url 등) */
export async function updateProject(
  id: string,
  body: Partial<ProjectCreate & { status: string }>,
): Promise<Project> {
  const response = await client.patch<Project>(`/api/projects/${id}`, body);
  return response.data;
}

/** 프로젝트 삭제 */
export async function removeProject(id: string): Promise<void> {
  const response = await client.delete(`/api/projects/${id}`);
  return response.data;
}

// ── Tasks ─────────────────────────────────────────────────────────────────────

/** 프로젝트의 전체 Task 목록 조회 */
export async function getTasks(projectId: string): Promise<Task[]> {
  const response = await client.get<Task[]>(`/api/projects/${projectId}/tasks`);
  return response.data;
}

/** 특정 Task 단건 조회 */
export async function getTask(taskId: string): Promise<Task> {
  const response = await client.get<Task>(`/api/tasks/${taskId}`);
  return response.data;
}

/** 새 Task 생성 */
export async function createTask(projectId: string, body: TaskCreate): Promise<Task> {
  const response = await client.post<Task>(`/api/projects/${projectId}/tasks`, body);
  return response.data;
}

/** Task 정보 수정 (상태, 담당자, 우선순위 등) */
export async function updateTask(taskId: string, body: TaskUpdate): Promise<Task> {
  const response = await client.patch<Task>(`/api/tasks/${taskId}`, body);
  return response.data;
}

// ── Specs ─────────────────────────────────────────────────────────────────────

/** 프로젝트의 전체 Spec 목록 조회 */
export async function getSpecs(projectId: string): Promise<Spec[]> {
  const response = await client.get<Spec[]>(`/api/projects/${projectId}/specs`);
  return response.data;
}

/** Spec 파일 업로드 (문서/이미지/텍스트) */
export async function uploadSpec(projectId: string, formData: FormData): Promise<Spec> {
  const response = await client.post<Spec>(`/api/projects/${projectId}/specs`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

/** Spec 삭제 */
export async function removeSpec(specId: string): Promise<void> {
  const response = await client.delete(`/api/specs/${specId}`);
  return response.data;
}

// ── Git ───────────────────────────────────────────────────────────────────────

/** 사용자 worktree의 변경 파일 목록 조회 (git status) */
export async function getGitStatus(projectId: string, userId: string): Promise<GitFileStatus[]> {
  const response = await client.get<GitFileStatus[]>(`/api/projects/${projectId}/git/status`, {
    params: { user_id: userId },
  });
  return response.data;
}

/** 특정 파일의 변경 내용 조회 (git diff). staged=true이면 staged diff 반환 */
export async function getGitDiff(
  projectId: string,
  userId: string,
  filePath: string,
  staged = false,
): Promise<{ diff: string }> {
  const response = await client.get<{ diff: string }>(`/api/projects/${projectId}/git/diff`, {
    params: { user_id: userId, file_path: filePath, staged },
  });
  return response.data;
}

/** 선택한 파일들을 staging area에 추가 (git add) */
export async function stageFiles(
  projectId: string,
  userId: string,
  filePaths: string[],
): Promise<void> {
  const response = await client.post(
    `/api/projects/${projectId}/git/stage`,
    { file_paths: filePaths },
    { params: { user_id: userId } },
  );
  return response.data;
}

/** staged 파일들을 커밋 (git commit -m) */
export async function commitGit(
  projectId: string,
  userId: string,
  message: string,
): Promise<void> {
  const response = await client.post(
    `/api/projects/${projectId}/git/commit`,
    { message },
    { params: { user_id: userId } },
  );
  return response.data;
}

/** 원격 브랜치에서 변경사항을 가져옴 (git pull). strategy: rebase | merge */
export async function pullGit(
  projectId: string,
  userId: string,
  strategy: 'rebase' | 'merge' = 'rebase',
): Promise<void> {
  const response = await client.post(
    `/api/projects/${projectId}/git/pull`,
    { strategy },
    { params: { user_id: userId } },
  );
  return response.data;
}

/** 현재 브랜치를 원격에 push (git push) */
export async function pushGit(projectId: string, userId: string): Promise<void> {
  const response = await client.post(
    `/api/projects/${projectId}/git/push`,
    {},
    { params: { user_id: userId } },
  );
  return response.data;
}

/** 커밋 히스토리 조회 (git log). count: 최대 반환 개수 */
export async function getGitLog(
  projectId: string,
  userId: string,
  count = 20,
): Promise<GitLogEntry[]> {
  const response = await client.get<GitLogEntry[]>(`/api/projects/${projectId}/git/log`, {
    params: { user_id: userId, count },
  });
  return response.data;
}

/** 특정 파일의 변경사항을 되돌림 (git checkout -- <file>) */
export async function revertGitFile(
  projectId: string,
  userId: string,
  filePath: string,
): Promise<void> {
  const response = await client.post(`/api/projects/${projectId}/git/revert`, null, {
    params: { user_id: userId, file_path: filePath },
  });
  return response.data;
}

/** 현재 체크아웃된 브랜치 이름 조회 (git branch --show-current) */
export async function getGitBranch(
  projectId: string,
  userId: string,
): Promise<{ branch: string }> {
  const response = await client.get<{ branch: string }>(`/api/projects/${projectId}/git/branch`, {
    params: { user_id: userId },
  });
  return response.data;
}
