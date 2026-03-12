import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { CheckCircle2, Clock, Play } from "lucide-react";
import type { Task, TaskPriority, TaskStatus } from "../../types";

const STATUS_ICON: Record<TaskStatus, React.ReactNode> = {
  planning: <Clock size={13} style={{ color: "#6366f1" }} />,
  plan_reviewing: <Clock size={13} style={{ color: "#f59e0b" }} />,
  confirmed: <CheckCircle2 size={13} style={{ color: "#22c55e" }} />,
};

const PRIORITY_COLOR: Record<TaskPriority, string> = {
  low: "#6b7280",
  medium: "#3b82f6",
  high: "#f59e0b",
  critical: "#ef4444",
};

const MOCK_PROGRESS: Partial<Record<TaskStatus, number>> = {};

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

  const progress = MOCK_PROGRESS[task.status];
  const initial = assigneeName ? assigneeName[0].toUpperCase() : null;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="kanban-card"
      onClick={onClick}
      {...attributes}
      {...listeners}
    >
      {/* 상단: 상태 아이콘 + 우선순위 점 */}
      <div className="kanban-card-header">
        {STATUS_ICON[task.status]}
        <span
          className="priority-dot"
          style={{ background: PRIORITY_COLOR[task.priority] }}
          title={task.priority}
        />
      </div>

      {/* 제목 */}
      <p className="kanban-card-title">{task.title}</p>

      {/* 진행률 바 (planning/coding/reviewing) */}
      {progress !== undefined && (
        <div className="progress-bar-wrap">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
      )}

      {/* 하단: 담당자 + 액션 */}
      <div className="kanban-card-footer">
        {assigneeName && (
          <div className="kanban-card-assignee">
            <span className="card-avatar">{initial}</span>
            <span>@{assigneeName}</span>
          </div>
        )}
        {progress !== undefined && (
          <span className="card-tag">{progress}%</span>
        )}
      </div>

      {/* 액션 버튼: 상태별 */}
      {task.status === "planning" && (
        <div className="card-actions">
          <button className="card-btn-run" onClick={(e) => e.stopPropagation()}>
            <Play size={10} /> 실행
          </button>
        </div>
      )}
    </div>
  );
}
