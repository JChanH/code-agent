// ── User ──────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  username: string;
  display_name: string | null;
  created_at: string;
}

// ── Worktree ───────────────────────────────────────────────────────────────────

export type WorktreeStatus = 'active' | 'inactive' | 'archived';

export interface UserWorktree {
  id: string;
  user_id: string;
  project_id: string;
  worktree_path: string;
  branch_name: string;
  status: WorktreeStatus;
  created_at: string;
}
