/* ──────────────────────────────────────
   Shared TypeScript types
   ────────────────────────────────────── */

// ── Enums ────────────────────────────
export type ProjectStack = 'python' | 'java' | 'other';
export type ProjectStatus = 'setup' | 'designing' | 'developing' | 'completed';
export type TaskStatus = 'backlog' | 'planning' | 'plan_review' | 'coding' | 'reviewing' | 'done' | 'failed';
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';
export type TaskComplexity = 'trivial' | 'low' | 'medium' | 'high' | 'very_high';
export type SpecSourceType = 'document' | 'image' | 'text' | 'url';
export type SpecStatus = 'uploaded' | 'analyzing' | 'analyzed' | 'confirmed';

// ── Models ───────────────────────────
export interface Project {
  id: string;
  name: string;
  description?: string;
  repo_url?: string;
  main_branch: string;
  project_stack: ProjectStack;
  framework?: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  username: string;
  display_name?: string;
  created_at: string;
}

export interface UserWorktree {
  id: string;
  user_id: string;
  project_id: string;
  worktree_path: string;
  branch_name: string;
  status: 'active' | 'inactive' | 'archived';
  created_at: string;
}

export interface Task {
  id: string;
  project_id: string;
  spec_id?: string;
  assigned_user_id?: string;
  title: string;
  description: string;
  acceptance_criteria?: string[];
  priority: TaskPriority;
  complexity: TaskComplexity;
  status: TaskStatus;
  dependencies?: string[];
  sort_order: number;
  auto_approve: boolean;
  auto_approve_config?: Record<string, unknown>;
  git_commit_hash?: string;
  created_at: string;
  updated_at: string;
}

export interface Spec {
  id: string;
  project_id: string;
  source_type: SpecSourceType;
  source_path?: string;
  raw_content?: string;
  analysis_result?: string;
  status: SpecStatus;
  created_at: string;
}

// ── Git ──────────────────────────────
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

// ── WebSocket Messages ───────────────
export interface WSMessage {
  type: string;
  [key: string]: unknown;
}

// ── Kanban ────────────────────────────
export interface KanbanColumn<T> {
  id: string;
  title: string;
  status: string;
  color: string;
  items: T[];
  allowDrop: boolean;
}

// ── Electron API (exposed via preload) 
declare global {
  interface Window {
    electronAPI?: {
      openDirectory: () => Promise<string | null>;
      openFile: (filters?: Array<{ name: string; extensions: string[] }>) => Promise<string | null>;
      getBackendUrl: () => Promise<string>;
      getWsUrl: () => Promise<string>;
    };
  }
}
