import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { CheckCircle2, Clock, Play, Loader, XCircle } from "lucide-react";
import type { Task, TaskStatus } from "../../types";

const STATUS_ICON: Record<TaskStatus, React.ReactNode> = {
  plan_reviewing: <Clock size={13} style={{ color: "#f59e0b" }} />,
  confirmed:      <CheckCircle2 size={13} style={{ color: "#22c55e" }} />,
  coding:         <Loader size={13} className="animate-spin" style={{ color: "#6366f1" }} />,
  reviewing:      <Clock size={13} style={{ color: "#8b5cf6" }} />,
  done:           <CheckCircle2 size={13} style={{ color: "#10b981" }} />,
  failed:         <XCircle size={13} style={{ color: "#ef4444" }} />,
};

const MOCK_PROGRESS: Partial<Record<TaskStatus, number>> = {};

interface Props {
  task: Task;
  onClick?: () => void;
  onRun?: (taskId: string) => void;
}

export default function KanbanCard({ task, onClick, onRun }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  const progress = MOCK_PROGRESS[task.status];

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="kanban-card"
      onClick={onClick}
      {...attributes}
      {...listeners}
    >
      {/* 상단: 상태 아이콘 */}
      <div className="kanban-card-header">
        {STATUS_ICON[task.status]}
      </div>

      {/* 제목 */}
      <p className="kanban-card-title">{task.title}</p>

      {/* 진행률 바 */}
      {progress !== undefined && (
        <div className="progress-bar-wrap">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
      )}

      {/* 하단: 액션 */}
      <div className="kanban-card-footer">
        {progress !== undefined && (
          <span className="card-tag">{progress}%</span>
        )}
      </div>

      {/* 액션 버튼: confirmed 상태에서 에이전트 실행 */}
      {task.status === "confirmed" && onRun && (
        <div className="card-actions">
          <button
            className="card-btn-run"
            onClick={(e) => { e.stopPropagation(); onRun(task.id); }}
          >
            <Play size={10} /> 실행
          </button>
        </div>
      )}
    </div>
  );
}
