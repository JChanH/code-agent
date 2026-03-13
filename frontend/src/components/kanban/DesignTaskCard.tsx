import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { CheckCircle2, Circle, Trash2 } from 'lucide-react';
import type { Task, TaskPriority } from '../../types';

const PRIORITY_COLOR: Record<TaskPriority, string> = {
  low: '#6b7280',
  medium: '#3b82f6',
  high: '#f59e0b',
  critical: '#ef4444',
};

const PRIORITY_LABEL: Record<TaskPriority, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  critical: 'Critical',
};

interface Props {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: string) => void;
}

export default function DesignTaskCard({ task, onEdit, onDelete }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  const isConfirmed = task.status === 'confirmed';
  const criteriaCount = task.acceptance_criteria?.length ?? 0;

  return (
    <div
      ref={setNodeRef}
      style={{ ...style, cursor: isDragging ? 'grabbing' : 'pointer' }}
      className="kanban-card"
      {...attributes}
      {...listeners}
      onClick={() => onEdit(task)}
    >
      {/* 상단: 상태 아이콘 + 우선순위 */}
      <div className="kanban-card-header">
        {isConfirmed
          ? <CheckCircle2 size={13} style={{ color: '#22c55e' }} />
          : <Circle size={13} style={{ color: '#6b7280' }} />
        }
        <span
          className="priority-dot"
          style={{ background: PRIORITY_COLOR[task.priority] }}
          title={PRIORITY_LABEL[task.priority]}
        />
        <span style={{ fontSize: 10, color: PRIORITY_COLOR[task.priority], marginLeft: 2 }}>
          {PRIORITY_LABEL[task.priority]}
        </span>
      </div>

      {/* 제목 */}
      <p className="kanban-card-title" style={{ marginTop: 6 }}>{task.title}</p>

      {/* 하단: 기준 개수 + 액션 버튼 */}
      <div className="kanban-card-footer" style={{ marginTop: 8, alignItems: 'center' }}>
        {criteriaCount > 0 && (
          <span className="card-tag">{criteriaCount}개 기준</span>
        )}

        <div style={{ display: 'flex', gap: 4, marginLeft: 'auto' }}>
          {/* 삭제 */}
          <button
            className="btn-icon"
            title="삭제"
            style={{ color: '#ef4444' }}
            onClick={(e) => { e.stopPropagation(); onDelete(task.id); }}
          >
            <Trash2 size={11} />
          </button>
        </div>
      </div>
    </div>
  );
}
