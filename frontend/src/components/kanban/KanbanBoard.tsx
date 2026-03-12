import { DndContext, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import KanbanColumn from './KanbanColumn';
import type { Task, TaskStatus, User } from '../../types';

interface ColumnDef {
  id: TaskStatus;
  title: string;
}

interface Props {
  columns: ColumnDef[];
  tasks: Task[];
  users?: User[];
  onStatusChange: (taskId: string, newStatus: TaskStatus) => void;
  onCardClick?: (task: Task) => void;
  onRun?: (taskId: string) => void;
}

export default function KanbanBoard({ columns, tasks, users = [], onStatusChange, onCardClick, onRun }: Props) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  function getColumnIdForTask(task: Task): TaskStatus | null {
    if (columns.some((c) => c.id === task.status)) {
      return task.status;
    }

    // Development board: include failed tasks in Done column
    if (task.status === 'failed' && columns.some((c) => c.id === 'done')) {
      return 'done';
    }

    return null;
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const taskId = active.id as string;
    const overId = over.id as string;
    const activeTask = tasks.find((t) => t.id === taskId);
    if (!activeTask) return;

    // over.id could be a column id or a card id — resolve to column id
    const targetColumn = columns.find((c) => c.id === overId);
    const targetTask = tasks.find((t) => t.id === overId);
    const targetColumnId = targetColumn
      ? targetColumn.id
      : targetTask
      ? getColumnIdForTask(targetTask)
      : null;

    if (!targetColumnId) return;

    const activeColumnId = getColumnIdForTask(activeTask);
    if (activeColumnId === targetColumnId) {
      return;
    }

    onStatusChange(taskId, targetColumnId);
  }

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="kanban-board">
        {columns.map((col) => (
          <KanbanColumn
            key={col.id}
            id={col.id}
            title={col.title}
            tasks={tasks.filter((t) => getColumnIdForTask(t) === col.id)}
            users={users}
            onCardClick={onCardClick}
            onRun={onRun}
          />
        ))}
      </div>
    </DndContext>
  );
}
