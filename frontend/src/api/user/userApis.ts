import client from '../client';
import type { User, UserWorktree } from './userTypes';

// ── Users ─────────────────────────────────────────────────────────────────────

/** 전체 사용자 목록 조회 */
export async function getUsers(): Promise<User[]> {
  const response = await client.get<User[]>('/api/users');
  return response.data;
}

/** 특정 사용자 단건 조회 */
export async function getUser(id: string): Promise<User> {
  const response = await client.get<User>(`/api/users/${id}`);
  return response.data;
}

/** 새 사용자 생성 */
export async function createUser(body: { username: string; display_name?: string }): Promise<User> {
  const response = await client.post<User>('/api/users', body);
  return response.data;
}

// ── Worktrees ─────────────────────────────────────────────────────────────────

/** 프로젝트에 속한 사용자별 worktree 목록 조회 */
export async function getWorktrees(projectId: string): Promise<UserWorktree[]> {
  const response = await client.get<UserWorktree[]>(`/api/projects/${projectId}/worktrees`);
  return response.data;
}

/** 특정 사용자의 worktree 생성 (브랜치 분기) */
export async function createWorktree(
  projectId: string,
  body: { user_id: string; branch_name: string },
): Promise<UserWorktree> {
  const response = await client.post<UserWorktree>(`/api/projects/${projectId}/worktrees`, body);
  return response.data;
}

/** worktree 제거 */
export async function removeWorktree(worktreeId: string): Promise<void> {
  const response = await client.delete(`/api/worktrees/${worktreeId}`);
  return response.data;
}
