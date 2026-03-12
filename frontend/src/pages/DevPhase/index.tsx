import KanbanBoard from "../../components/kanban/KanbanBoard";
import { useTaskStore, useAppStore } from "../../stores";
import type { TaskStatus } from "../../types";

const COLUMNS = [
  { id: "confirmed" as TaskStatus, title: "Ready" },
  { id: "planning" as TaskStatus, title: "In Progress" },
];

const DEV_STATUSES: TaskStatus[] = ["confirmed", "planning"];

interface Props { projectId: string; }

export default function DevPhase({ projectId }: Props) {
  const { tasks, updateTask } = useTaskStore();
  const { users, selectedUserId, selectUser } = useAppStore();

  const devTasks = tasks.filter(
    (t) => t.project_id === projectId && DEV_STATUSES.includes(t.status),
  );
  const filtered = selectedUserId
    ? devTasks.filter((t) => t.assigned_user_id === selectedUserId)
    : devTasks;

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>개발 단계</h2>
        <div className="user-filter">
          <label>담당자</label>
          <select value={selectedUserId ?? ""} onChange={(e) => selectUser(e.target.value || null)}>
            <option value="">전체</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.display_name ?? u.username}</option>
            ))}
          </select>
        </div>
      </div>
      <KanbanBoard
        columns={COLUMNS}
        tasks={filtered}
        users={users}
        onStatusChange={(id, s) => updateTask(id, { status: s })}
      />
    </div>
  );
}
