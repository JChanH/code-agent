import { Upload, FileText, Image, Plus } from "lucide-react";
import KanbanBoard from "../../components/kanban/KanbanBoard";
import { useTaskStore, useAppStore } from "../../stores";
import type { TaskStatus } from "../../types";

const COLUMNS = [
  { id: "backlog" as TaskStatus, title: "Spec 입력" },
  { id: "planning" as TaskStatus, title: "AI 분석중" },
  { id: "plan_review" as TaskStatus, title: "Task 분해됨" },
  { id: "coding" as TaskStatus, title: "확정됨" },
];

const DESIGN_STATUSES: TaskStatus[] = ["backlog", "planning", "plan_review", "coding"];

interface Props { projectId: string; }

export default function DesignPhase({ projectId }: Props) {
  const { tasks, updateTask } = useTaskStore();
  const { users } = useAppStore();
  const designTasks = tasks.filter(
    (t) => t.project_id === projectId && DESIGN_STATUSES.includes(t.status),
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>설계 단계</h2>
        <span className="badge">{designTasks.length}개 항목</span>
      </div>
      <div className="dropzone" onDragOver={(e) => e.preventDefault()}>
        <Upload size={16} />
        <span>파일 / 이미지 / 텍스트 Spec을 드래그하거나</span>
        <div style={{ display: "flex", gap: 6, marginLeft: "auto" }}>
          <button className="btn-sm"><FileText size={11} /> 파일 업로드</button>
          <button className="btn-sm"><Image size={11} /> 이미지</button>
          <button className="btn-sm"><Plus size={11} /> 텍스트 입력</button>
        </div>
      </div>
      <KanbanBoard
        columns={COLUMNS}
        tasks={designTasks}
        users={users}
        onStatusChange={(id, s) => updateTask(id, { status: s })}
      />
    </div>
  );
}
