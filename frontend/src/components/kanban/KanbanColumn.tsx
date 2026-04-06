import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import KanbanCard from './KanbanCard';
import type { Task } from '../../types';

interface Props {
  id: string;
  title: string;
  tasks: Task[];
  onCardClick?: (task: Task) => void;
  onRun?: (taskId: string) => void;
}

export default function KanbanColumn({ id, title, tasks, onCardClick, onRun }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div className={`kanban-column ${isOver ? 'over' : ''}`}>
      <div className="kanban-column-header">
        <span className="kanban-column-title">{title}</span>
        <span className="kanban-column-count">{tasks.length}</span>
      </div>

      <div ref={setNodeRef} className="kanban-column-body">
        <SortableContext items={tasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
          {tasks.map((task) => (
            <KanbanCard
              key={task.id}
              task={task}
              onClick={() => onCardClick?.(task)}
              onRun={onRun}
            />
          ))}
        </SortableContext>
      </div>
    </div>
  );
}
