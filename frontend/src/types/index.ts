// ── Enums ────────────────────────────────────────────────────────────────────

export type ProjectStack = 'python' | 'java' | 'other';
export type ProjectStatus = 'setup' | 'designing' | 'developing' | 'completed';

export type TaskStatus =
  | 'backlog'
  | 'planning'
  | 'plan_review'
  | 'coding'
  | 'reviewing'
  | 'done'
  | 'failed';

export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';
export type TaskComplexity = 'trivial' | 'low' | 'medium' | 'high' | 'very_high';

export type SpecSourceType = 'document' | 'image' | 'text' | 'url';
export type SpecStatus = 'uploaded' | 'analyzing' | 'analyzed' | 'confirmed';

export type WorktreeStatus = 'active' | 'inactive' | 'archived';

export type ActiveTab = 'design' | 'dev' | 'console' | 'git' | 'settings';

// ── Domain Models ─────────────────────────────────────────────────────────────

export interface Project {
  id: string;
  name: string;
  description: string | null;
  repo_url: string | null;
  main_branch: string;
  project_stack: ProjectStack;
  framework: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  username: string;
  display_name: string | null;
  created_at: string;
}

export interface UserWorktree {
  id: string;
  user_id: string;
  project_id: string;
  worktree_path: string;
  branch_name: string;
  status: WorktreeStatus;
  created_at: string;
}

export interface Task {
  id: string;
  project_id: string;
  spec_id: string | null;
  assigned_user_id: string | null;
  title: string;
  description: string;
  acceptance_criteria: string[] | null;
  priority: TaskPriority;
  complexity: TaskComplexity;
  status: TaskStatus;
  dependencies: string[] | null;
  sort_order: number;
  auto_approve: boolean;
  auto_approve_config: Record<string, unknown> | null;
  git_commit_hash: string | null;
  created_at: string;
  updated_at: string;
}

export interface Spec {
  id: string;
  project_id: string;
  source_type: SpecSourceType;
  source_path: string | null;
  raw_content: string | null;
  analysis_result: Record<string, unknown> | null;
  status: SpecStatus;
  created_at: string;
}

// ── Git Types ─────────────────────────────────────────────────────────────────

export interface GitFileStatus {
  status: string;
  path: string;
}

export interface GitLogEntry {
  hash: string;
  short_hash: string;
  message: string;
  author: string;
  relative_date: string;
}

// ── Request Bodies ────────────────────────────────────────────────────────────

export interface ProjectCreate {
  name: string;
  description?: string;
  repo_url?: string;
  main_branch?: string;
  project_stack?: ProjectStack;
  framework?: string;
}

export interface TaskCreate {
  project_id: string;
  spec_id?: string;
  assigned_user_id?: string;
  title: string;
  description: string;
  acceptance_criteria?: string[];
  priority?: TaskPriority;
  complexity?: TaskComplexity;
  dependencies?: string[];
  auto_approve?: boolean;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  assigned_user_id?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  complexity?: TaskComplexity;
  sort_order?: number;
}

// ── WebSocket Messages ────────────────────────────────────────────────────────

export interface WsMessage {
  type: string;
  data: unknown;
}

export interface WsTaskUpdate {
  task_id: string;
  status: TaskStatus;
  progress?: number;
  message?: string;
}
