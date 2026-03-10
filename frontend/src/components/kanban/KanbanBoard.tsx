import { DndContext, DragEndEvent, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
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
}

export default function KanbanBoard({ columns, tasks, users = [], onStatusChange, onCardClick }: Props) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const taskId = active.id as string;
    const newStatus = over.id as TaskStatus;

    // over.id could be a column id or a card id — resolve to column id
    const targetColumn = columns.find((c) => c.id === newStatus);
    if (targetColumn) {
      onStatusChange(taskId, newStatus);
    } else {
      // dropped on another card — find which column it belongs to
      const targetTask = tasks.find((t) => t.id === newStatus);
      if (targetTask) {
        onStatusChange(taskId, targetTask.status);
      }
    }
  }

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="kanban-board">
        {columns.map((col) => (
          <KanbanColumn
            key={col.id}
            id={col.id}
            title={col.title}
            tasks={tasks.filter((t) => t.status === col.id)}
            users={users}
            onCardClick={onCardClick}
          />
        ))}
      </div>
    </DndContext>
  );
}
