// ── Electron API ─────────────────────────────────────────────────────────────

declare global {
  interface Window {
    electronAPI?: {
      openDirectory: () => Promise<string | null>;
      openFile: (filters?: { name: string; extensions: string[] }[]) => Promise<string | null>;
      getBackendUrl: () => Promise<string>;
      getWsUrl: () => Promise<string>;
      openVSCode: (folderPath: string) => Promise<boolean>;
    };
  }
}

// ── Enums ────────────────────────────────────────────────────────────────────

export type ProjectStack = 'python' | 'java' | 'other';
export type ProjectStatus = 'setup' | 'designing' | 'developing' | 'completed';

export type TaskStatus =
  | 'plan_reviewing'
  | 'confirmed'
  | 'coding'
  | 'reviewing'
  | 'done'
  | 'failed';

export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';
export type TaskComplexity = 'trivial' | 'low' | 'medium' | 'high' | 'very_high';

export type SpecSourceType = 'document' | 'image' | 'text' | 'url';
export type SpecStatus = 'uploaded' | 'analyzing' | 'final_confirmed';

export type WorktreeStatus = 'active' | 'inactive' | 'archived';

export type ActiveTab = 'dashboard' | 'design' | 'dev' | 'console' | 'git' | 'settings' | 'legacy' | 'runtime_errors';

// ── Domain Models ─────────────────────────────────────────────────────────────

export interface Project {
  id: string;
  name: string;
  description: string | null;
  repo_url: string | null;
  local_repo_path: string;
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

// ── Log ───────────────────────────────────────────────────────────────────────

export type LogLevel = 'info' | 'success' | 'warn' | 'error';

export interface LogEntry {
  id: string;
  time: string;
  level: LogLevel;
  msg: string;
}

// ── WebSocket Messages ────────────────────────────────────────────────────────

export interface WsMsgSpecAnalyzing {
  type: 'spec_analyzing';
  spec_id: string;
}

export interface WsMsgSpecAnalyzed {
  type: 'spec_analyzed';
  spec_id: string;
  analysis_summary: string;
  tasks: Array<{
    id: string;
    title: string;
    description: string;
    priority: TaskPriority;
    complexity: TaskComplexity;
    status: TaskStatus;
  }>;
}

export interface WsMsgSpecAnalyzeFailed {
  type: 'spec_analyze_failed';
  spec_id: string;
  error: string;
}

export interface WsMsgTaskUpdate {
  type: 'task_update';
  task_id: string;
  status: TaskStatus;
  attempt?: number;
  error?: string;
}

export interface WsMsgReviewResult {
  type: 'review_result';
  task_id: string;
  attempt: number;
  passed: boolean;
  test_output: string;
  feedback: string;
}

export interface WsMsgAgentMessage {
  type: 'agent_message';
  message: unknown;
  spec_id?: string;
  task_id?: string;
  project_id?: string;
  session_id?: string;
  agent?: string;
}

export interface WsMsgGuidemapGenerating {
  type: 'guidemap_generating';
  project_id: string;
}

export interface WsMsgGuidemapGenerated {
  type: 'guidemap_generated';
  project_id: string;
}

export interface WsMsgGuidemapFailed {
  type: 'guidemap_failed';
  project_id: string;
  error: string;
}

export interface WsMsgLegacyAnalyzing {
  type: 'legacy_analyzing';
  session_id: string;
}

export interface WsMsgLegacyAnalyzed {
  type: 'legacy_analyzed';
  session_id: string;
  sections: Array<{ title: string; content: string }>;
}

export interface WsMsgLegacyAnalyzeFailed {
  type: 'legacy_analyze_failed';
  session_id: string;
  error: string;
}

export interface WsMsgRuntimeError {
  type: 'runtime_error';
  data: RuntimeError;
}

export interface WsMsgRuntimeErrorUpdate {
  type: 'runtime_error_update';
  data: { id: string; status: RuntimeErrorStatus; fix_suggestion?: string | null };
}

export interface WsMsgRuntimeErrorAgentMessage {
  type: 'runtime_error_agent_message';
  data: { error_id: string; message: string };
}

export type WsMessage =
  | WsMsgSpecAnalyzing
  | WsMsgSpecAnalyzed
  | WsMsgSpecAnalyzeFailed
  | WsMsgTaskUpdate
  | WsMsgReviewResult
  | WsMsgAgentMessage
  | WsMsgGuidemapGenerating
  | WsMsgGuidemapGenerated
  | WsMsgGuidemapFailed
  | WsMsgLegacyAnalyzing
  | WsMsgLegacyAnalyzed
  | WsMsgLegacyAnalyzeFailed
  | WsMsgRuntimeError
  | WsMsgRuntimeErrorUpdate
  | WsMsgRuntimeErrorAgentMessage;

// Legacy aliases (기존 코드 호환)
/** @deprecated WsMsgSpecAnalyzed 사용 */
export type WsSpecAnalyzed = WsMsgSpecAnalyzed;

// ── Runtime Error ─────────────────────────────────────────────────────────────

export type RuntimeErrorLevel = 'error' | 'warning' | 'critical' | 'info';
export type RuntimeErrorStatus = 'pending' | 'analyzing' | 'analyzed' | 'resolved' | 'ignored';

export interface RuntimeErrorMetadata {
  path: string;
  method: string;
  status_code: number;
  query_params: string;
  request_body: string | null;
}

export interface RuntimeError {
  id: string;
  error_code: string;
  message: string;
  project_id: string;
  level: RuntimeErrorLevel;
  error_timestamp: string | null;
  metadata: RuntimeErrorMetadata | null;
  fix_suggestion: string | null;
  status: RuntimeErrorStatus;
  created_at: string;
}

export interface RuntimeErrorListResponse {
  items: RuntimeError[];
  total: number;
  limit: number;
  offset: number;
}
