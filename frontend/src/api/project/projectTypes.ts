// ── Project ───────────────────────────────────────────────────────────────────

export type ProjectType = 'new' | 'existing';
export type ProjectStack = 'python' | 'java' | 'other';
export type ProjectStatus = 'setup' | 'designing' | 'developing' | 'completed';

export interface Project {
  id: string;
  name: string;
  description: string | null;
  project_type: ProjectType;
  repo_url: string | null;
  local_repo_path: string;
  main_branch: string;
  project_stack: ProjectStack;
  framework: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  project_type: ProjectType;
  name: string;
  description?: string;
  repo_url?: string;
  local_repo_path: string;
  main_branch?: string;
  project_stack?: ProjectStack;
  framework?: string;
}

// ── Task ──────────────────────────────────────────────────────────────────────

export type TaskStatus =
  | 'planning'
  | 'plan_reviewing'
  | 'confirmed';

export interface Task {
  id: string;
  project_id: string;
  spec_id: string | null;
  assigned_user_id: string | null;
  title: string;
  description: string;
  acceptance_criteria: string[] | null;
  status: TaskStatus;
  git_commit_hash: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  project_id: string;
  spec_id?: string;
  assigned_user_id?: string;
  title: string;
  description: string;
  acceptance_criteria?: string[];
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  assigned_user_id?: string;
  status?: TaskStatus;
}

// ── Spec ──────────────────────────────────────────────────────────────────────

export type SpecSourceType = 'document' | 'image' | 'text' | 'url';
export type SpecStatus = 'uploaded' | 'analyzing' | 'final_confirmed';

export interface Spec {
  id: string;
  project_id: string;
  source_type: SpecSourceType;
  source_path: string | null;
  raw_content: string | null;
  status: SpecStatus;
  created_at: string;
}

// ── Git ───────────────────────────────────────────────────────────────────────

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
