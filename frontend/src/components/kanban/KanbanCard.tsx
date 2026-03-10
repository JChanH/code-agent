import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { AlertCircle, CheckCircle2, Circle, Clock, Loader2, XCircle } from 'lucide-react';
import type { Task, TaskPriority, TaskStatus } from '../../types';

const STATUS_ICON: Record<TaskStatus, React.ReactNode> = {
  backlog: <Circle size={14} />,
  planning: <Clock size={14} />,
  plan_review: <Clock size={14} className="text-yellow-400" />,
  coding: <Loader2 size={14} className="animate-spin text-blue-400" />,
  reviewing: <AlertCircle size={14} className="text-yellow-400" />,
  done: <CheckCircle2 size={14} className="text-green-400" />,
  failed: <XCircle size={14} className="text-red-400" />,
};

const PRIORITY_COLOR: Record<TaskPriority, string> = {
  low: '#6b7280',
  medium: '#3b82f6',
  high: '#f59e0b',
  critical: '#ef4444',
};

interface Props {
  task: Task;
  assigneeName?: string;
  onClick?: () => void;
}

export default function KanbanCard({ task, assigneeName, onClick }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="kanban-card"
      onClick={onClick}
      {...attributes}
      {...listeners}
    >
      <div className="kanban-card-header">
        {STATUS_ICON[task.status]}
        <span
          className="priority-dot"
          style={{ background: PRIORITY_COLOR[task.priority] }}
          title={task.priority}
        />
      </div>
      <p className="kanban-card-title">{task.title}</p>
      {assigneeName && (
        <p className="kanban-card-assignee">{assigneeName}</p>
      )}
    </div>
  );
}
