import { useEffect, useCallback } from 'react';
import KanbanBoard from '../../components/kanban/KanbanBoard';
import { tasksApi } from '../../services/api';
import { useTaskStore, useAppStore } from '../../stores';
import type { Task, TaskStatus } from '../../types';

const COLUMNS = [
  { id: 'backlog' as TaskStatus, title: 'Backlog' },
  { id: 'planning' as TaskStatus, title: 'Planning' },
  { id: 'coding' as TaskStatus, title: 'Coding' },
  { id: 'reviewing' as TaskStatus, title: 'Review' },
  { id: 'done' as TaskStatus, title: 'Done' },
];

interface Props {
  projectId: string;
}

export default function DevPhase({ projectId }: Props) {
  const { tasks, setTasks, updateTask } = useTaskStore();
  const { users, selectedUserId, selectUser } = useAppStore();

  useEffect(() => {
    tasksApi.list(projectId).then(setTasks).catch(console.error);
  }, [projectId, setTasks]);

  const filteredTasks = selectedUserId
    ? tasks.filter((t) => t.assigned_user_id === selectedUserId)
    : tasks;

  const handleStatusChange = useCallback(
    async (taskId: string, newStatus: TaskStatus) => {
      updateTask(taskId, { status: newStatus });
      await tasksApi.update(taskId, { status: newStatus }).catch(console.error);
    },
    [updateTask],
  );

  function handleCardClick(task: Task) {
    // TODO: 상세 패널 열기 (Phase 2)
    console.log('card clicked:', task.id);
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>개발 단계</h2>

        <div className="user-filter">
          <label>담당자</label>
          <select
            value={selectedUserId ?? ''}
            onChange={(e) => selectUser(e.target.value || null)}
          >
            <option value="">전체</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.display_name ?? u.username}
              </option>
            ))}
          </select>
        </div>
      </div>

      <KanbanBoard
        columns={COLUMNS}
        tasks={filteredTasks}
        users={users}
        onStatusChange={handleStatusChange}
        onCardClick={handleCardClick}
      />
    </div>
  );
}
