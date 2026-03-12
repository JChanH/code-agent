import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import KanbanCard from './KanbanCard';
import type { Task, User } from '../../types';

interface Props {
  id: string;
  title: string;
  tasks: Task[];
  users?: User[];
  onCardClick?: (task: Task) => void;
  onRun?: (taskId: string) => void;
}

export default function KanbanColumn({ id, title, tasks, users = [], onCardClick, onRun }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id });

  const getUserName = (userId: string | null) => {
    if (!userId) return undefined;
    const u = users.find((u) => u.id === userId);
    return u?.display_name ?? u?.username;
  };

  return (
    <div className={`kanban-column ${isOver ? 'over' : ''}`}>
      <div className="kanban-column-header">
        <span className="kanban-column-title">{title}</span>
        <span className="kanban-column-count">{tasks.length}</span>
      </div>

      <div ref={setNodeRef} className="kanban-column-body">
        <SortableContext items={tasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
          {tasks.map((task) => (
            <KanbanCard
              key={task.id}
              task={task}
              assigneeName={getUserName(task.assigned_user_id)}
              onClick={() => onCardClick?.(task)}
              onRun={onRun}
            />
          ))}
        </SortableContext>
      </div>
    </div>
  );
}
