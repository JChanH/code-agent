import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  AlertCircle, CheckCircle2, Circle, Clock, Loader2, XCircle,
  Play, Check, X, RotateCcw,
} from "lucide-react";
import type { Task, TaskPriority, TaskStatus } from "../../types";

const STATUS_ICON: Record<TaskStatus, React.ReactNode> = {
  backlog: <Circle size={13} />,
  planning: <Clock size={13} style={{ color: "#6366f1" }} />,
  plan_review: <Clock size={13} style={{ color: "#f59e0b" }} />,
  coding: <Loader2 size={13} className="animate-spin" style={{ color: "#3b82f6" }} />,
  reviewing: <AlertCircle size={13} style={{ color: "#f59e0b" }} />,
  done: <CheckCircle2 size={13} style={{ color: "#22c55e" }} />,
  failed: <XCircle size={13} style={{ color: "#ef4444" }} />,
};

const PRIORITY_COLOR: Record<TaskPriority, string> = {
  low: "#6b7280",
  medium: "#3b82f6",
  high: "#f59e0b",
  critical: "#ef4444",
};

// 상태별 가상 진행률 (UI 데모용)
const MOCK_PROGRESS: Partial<Record<TaskStatus, number>> = {
  planning: 30,
  coding: 67,
  reviewing: 95,
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
      {task.status === "backlog" && (
        <div className="card-actions">
          <button className="card-btn-run" onClick={(e) => e.stopPropagation()}>
            <Play size={10} /> 실행
          </button>
        </div>
      )}
      {task.status === "reviewing" && (
        <div className="card-actions">
          <button className="card-btn-approve" onClick={(e) => e.stopPropagation()}>
            <Check size={10} /> 승인
          </button>
          <button className="card-btn-reject" onClick={(e) => e.stopPropagation()}>
            <X size={10} /> 거절
          </button>
          <button className="card-btn-run" onClick={(e) => e.stopPropagation()}>
            <RotateCcw size={10} /> 자동승인
          </button>
        </div>
      )}
      {task.status === "done" && task.git_commit_hash && (
        <div className="card-footer-commit" style={{ marginTop: 6, fontSize: 10, color: "#6b7280", fontFamily: "monospace" }}>
          {task.git_commit_hash}
        </div>
      )}
    </div>
  );
}
