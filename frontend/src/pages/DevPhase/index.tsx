import { useEffect } from "react";
import { Code2 } from "lucide-react";
import KanbanBoard from "../../components/kanban/KanbanBoard";
import { useTaskStore, useAppStore } from "../../stores";
import { getTasks, runAgent } from "../../api/project/projectApis";
import type { Task, TaskStatus } from "../../types";

const COLUMNS = [
  { id: "confirmed" as TaskStatus, title: "Backlog" },
  { id: "coding"    as TaskStatus, title: "In Progress" },
  { id: "reviewing" as TaskStatus, title: "AI Review" },
  { id: "done"      as TaskStatus, title: "Done" },
];

const DEV_STATUSES: TaskStatus[] = ["confirmed", "coding", "reviewing", "done", "failed"];

interface Props { projectId: string; }

export default function DevPhase({ projectId }: Props) {
  const { tasks, setTasks, updateTask } = useTaskStore();
  const { projects } = useAppStore();
  const project = projects.find((p) => p.id === projectId);

  useEffect(() => {
    getTasks(projectId)
      .then((loaded) => setTasks(loaded as Task[]))
      .catch(() => {});
  }, [projectId]);

  const devTasks = tasks.filter(
    (t) => t.project_id === projectId && DEV_STATUSES.includes(t.status),
  );

  async function handleRun(taskId: string) {
    updateTask(taskId, { status: "coding" });
    try {
      await runAgent(taskId);
    } catch {
      updateTask(taskId, { status: "confirmed" });
    }
  }

  function handleOpenVSCode() {
    if (project?.local_repo_path) {
      window.electronAPI?.openVSCode(project.local_repo_path);
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>개발 단계</h2>
        {project?.local_repo_path && (
          <button className="btn-sm" onClick={handleOpenVSCode} title={project.local_repo_path}>
            <Code2 size={12} /> VSCode 열기
          </button>
        )}
      </div>
      <KanbanBoard
        columns={COLUMNS}
        tasks={devTasks}
        onStatusChange={(id, s) => updateTask(id, { status: s })}
        onRun={handleRun}
      />
    </div>
  );
}
