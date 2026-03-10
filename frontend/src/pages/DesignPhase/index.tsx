import { useEffect, useCallback } from 'react';
import { Upload } from 'lucide-react';
import KanbanBoard from '../../components/kanban/KanbanBoard';
import { tasksApi, specsApi } from '../../services/api';
import { useTaskStore } from '../../stores';
import type { TaskStatus } from '../../types';

const COLUMNS = [
  { id: 'backlog' as TaskStatus, title: 'Spec 입력' },
  { id: 'planning' as TaskStatus, title: 'AI 분석중' },
  { id: 'plan_review' as TaskStatus, title: 'Task 분해됨' },
  { id: 'coding' as TaskStatus, title: '확정됨' },
];

interface Props {
  projectId: string;
}

export default function DesignPhase({ projectId }: Props) {
  const { tasks, specs, setTasks, setSpecs, updateTask } = useTaskStore();

  useEffect(() => {
    tasksApi.list(projectId).then(setTasks).catch(console.error);
    specsApi.list(projectId).then(setSpecs).catch(console.error);
  }, [projectId, setTasks, setSpecs]);

  const handleStatusChange = useCallback(
    async (taskId: string, newStatus: TaskStatus) => {
      updateTask(taskId, { status: newStatus });
      await tasksApi.update(taskId, { status: newStatus }).catch(console.error);
    },
    [updateTask],
  );

  async function handleFileDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    fd.append('source_type', 'document');
    const spec = await specsApi.upload(projectId, fd).catch(console.error);
    if (spec) setSpecs([...specs, spec]);
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>설계 단계</h2>
        <span className="badge">{specs.length}개 Spec</span>
      </div>

      {/* Spec 업로드 드롭존 */}
      <div
        className="dropzone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleFileDrop}
      >
        <Upload size={20} />
        <span>문서/이미지를 드래그하거나 클릭해서 Spec을 추가하세요</span>
      </div>

      <KanbanBoard
        columns={COLUMNS}
        tasks={tasks}
        onStatusChange={handleStatusChange}
      />
    </div>
  );
}
