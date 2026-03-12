import { useEffect, useRef, useState } from 'react';
import {
  DndContext, PointerSensor, useSensor, useSensors,
  useDroppable,
} from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import {
  Upload, FileText, Image, Plus, X, Loader, AlertCircle, CheckCircle,
} from 'lucide-react';
import DesignTaskCard from '../../components/kanban/DesignTaskCard';
import { useTaskStore } from '../../stores';
import {
  getSpecs, getTasks, uploadSpec, removeSpec, analyzeSpec,
  finalConfirmSpec, updateTask, deleteTask,
} from '../../api/project/projectApis';
import type { Spec, Task, TaskPriority, TaskComplexity } from '../../types';

// ── 컬럼 ID ───────────────────────────────────────────────────────────────────

const COL_REVIEWING = 'plan_reviewing';
const COL_CONFIRMED = 'confirmed';

// ── Task 편집 모달 ────────────────────────────────────────────────────────────

interface EditModalProps {
  task: Task;
  onSave: (patch: Partial<Task>) => void;
  onClose: () => void;
}

function TaskEditModal({ task, onSave, onClose }: EditModalProps) {
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description);
  const [criteria, setCriteria] = useState<string[]>(task.acceptance_criteria ?? []);
  const [priority, setPriority] = useState<TaskPriority>(task.priority);
  const [complexity, setComplexity] = useState<TaskComplexity>(task.complexity);
  const [newCriterion, setNewCriterion] = useState('');

  function addCriterion() {
    if (newCriterion.trim()) {
      setCriteria([...criteria, newCriterion.trim()]);
      setNewCriterion('');
    }
  }

  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}
      onClick={onClose}
    >
      <div
        style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8, padding: 20, width: 520, maxHeight: '80vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 12 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 600 }}>Task 수정</span>
          <button className="btn-icon" onClick={onClose}><X size={14} /></button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>제목</label>
          <input
            style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 4, padding: '6px 8px', color: 'inherit', fontSize: 13 }}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>설명</label>
          <textarea
            style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 4, padding: '6px 8px', color: 'inherit', fontSize: 13, resize: 'vertical', minHeight: 100, fontFamily: 'inherit' }}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>우선순위</label>
            <select
              style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 4, padding: '6px 8px', color: 'inherit', fontSize: 13 }}
              value={priority}
              onChange={(e) => setPriority(e.target.value as TaskPriority)}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>복잡도</label>
            <select
              style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 4, padding: '6px 8px', color: 'inherit', fontSize: 13 }}
              value={complexity}
              onChange={(e) => setComplexity(e.target.value as TaskComplexity)}
            >
              <option value="trivial">Trivial</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="very_high">Very High</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>수용 기준</label>
          {criteria.map((c, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ flex: 1, fontSize: 12, color: 'var(--text-secondary)', background: 'var(--bg-primary)', padding: '4px 8px', borderRadius: 4 }}>{c}</span>
              <button className="btn-icon" onClick={() => setCriteria(criteria.filter((_, idx) => idx !== i))}><X size={11} /></button>
            </div>
          ))}
          <div style={{ display: 'flex', gap: 6 }}>
            <input
              style={{ flex: 1, background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 4, padding: '5px 8px', color: 'inherit', fontSize: 12 }}
              placeholder="기준 추가… (Enter)"
              value={newCriterion}
              onChange={(e) => setNewCriterion(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') addCriterion(); }}
            />
            <button className="btn-sm" onClick={addCriterion}><Plus size={11} /></button>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button className="btn-sm" onClick={onClose}>취소</button>
          <button
            className="btn-sm"
            style={{ background: '#1d4ed8', color: '#fff' }}
            onClick={() => onSave({ title, description, acceptance_criteria: criteria, priority, complexity })}
            disabled={!title.trim()}
          >
            저장
          </button>
        </div>
      </div>
    </div>
  );
}

// ── 텍스트 입력 모달 ──────────────────────────────────────────────────────────

function TextInputModal({ onSubmit, onClose }: { onSubmit: (text: string) => void; onClose: () => void }) {
  const [text, setText] = useState('');
  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}
      onClick={onClose}
    >
      <div
        style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8, padding: 20, width: 480, display: 'flex', flexDirection: 'column', gap: 12 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 600 }}>텍스트 Spec 입력</span>
          <button className="btn-icon" onClick={onClose}><X size={14} /></button>
        </div>
        <textarea
          style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 4, padding: 8, color: 'inherit', fontFamily: 'inherit', fontSize: 13, resize: 'vertical', minHeight: 160 }}
          placeholder="개발할 기능을 텍스트로 입력하세요…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          autoFocus
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button className="btn-sm" onClick={onClose}>취소</button>
          <button
            className="btn-sm"
            style={{ background: '#1d4ed8', color: '#fff' }}
            onClick={() => { if (text.trim()) onSubmit(text.trim()); }}
            disabled={!text.trim()}
          >
            업로드
          </button>
        </div>
      </div>
    </div>
  );
}

// ── 드롭 가능한 컬럼 ──────────────────────────────────────────────────────────

function DroppableColumn({
  id, title, count, headerExtra, children,
}: {
  id: string;
  title: string;
  count: number;
  headerExtra?: React.ReactNode;
  children: React.ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });
  return (
    <div
      ref={setNodeRef}
      style={{
        flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column',
        background: isOver ? 'rgba(99,102,241,0.06)' : 'var(--bg-secondary)',
        border: `1px solid ${isOver ? '#6366f1' : 'var(--border)'}`,
        borderRadius: 8, padding: '12px 10px', gap: 8, minHeight: 300,
        transition: 'border-color 0.15s, background 0.15s',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
        <span style={{ fontWeight: 600, fontSize: 13 }}>{title}</span>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', background: 'var(--bg-primary)', borderRadius: 10, padding: '1px 7px' }}>
          {count}
        </span>
        {headerExtra}
      </div>
      {children}
    </div>
  );
}

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────

export default function DesignPhase({ projectId }: { projectId: string }) {
  const {
    tasks, specs, analyzingSpecIds,
    setTasks, setSpecs, addSpec,
    updateTask: storeUpdateTask,
    removeSpec: storeRemoveSpec,
  } = useTaskStore();

  const [error, setError] = useState<string | null>(null);
  const [showTextModal, setShowTextModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  useEffect(() => {
    Promise.all([
      getSpecs(projectId).catch(() => [] as Spec[]),
      getTasks(projectId).catch(() => [] as Task[]),
    ]).then(([loadedSpecs, loadedTasks]) => {
      setSpecs(loadedSpecs as Spec[]);
      setTasks(loadedTasks as Task[]);
    });
  }, [projectId]);

  const projectSpecs = specs.filter((sp) => sp.project_id === projectId);
  const analyzingSpecs = projectSpecs.filter((sp) => sp.status === 'analyzing');
  const uploadedSpecs = projectSpecs.filter((sp) => sp.status === 'uploaded');

  const reviewingTasks = tasks.filter((t) => t.project_id === projectId && t.status === 'plan_reviewing');
  const confirmedTasks = tasks.filter((t) => t.project_id === projectId && t.status === 'confirmed');

  // ── 파일 업로드 ─────────────────────────────────────────────────────────────

  async function handleFileUpload(file: File, sourceType: 'document' | 'image') {
    setError(null);
    const formData = new FormData();
    formData.append('source_type', sourceType);
    formData.append('file', file);
    try {
      const spec = await uploadSpec(projectId, formData);
      addSpec(spec as Spec);
    } catch {
      setError('파일 업로드에 실패했습니다.');
    }
  }

  async function handleTextUpload(text: string) {
    setShowTextModal(false);
    setError(null);
    const formData = new FormData();
    formData.append('source_type', 'text');
    formData.append('raw_content', text);
    try {
      const spec = await uploadSpec(projectId, formData);
      addSpec(spec as Spec);
    } catch {
      setError('텍스트 업로드에 실패했습니다.');
    }
  }

  async function handleAnalyze(specId: string) {
    setError(null);
    try {
      await analyzeSpec(specId);
    } catch {
      setError('분석 시작에 실패했습니다.');
    }
  }

  async function handleDeleteSpec(specId: string) {
    setError(null);
    try {
      await removeSpec(specId);
      storeRemoveSpec(specId);
    } catch {
      setError('Spec 삭제에 실패했습니다.');
    }
  }

  // ── Task 수정 ────────────────────────────────────────────────────────────────

  async function handleSaveTask(patch: Partial<Task>) {
    if (!editingTask) return;
    storeUpdateTask(editingTask.id, patch);
    setEditingTask(null);
    try {
      const { assigned_user_id, ...rest } = patch;
      await updateTask(editingTask.id, {
        ...rest,
        ...(assigned_user_id !== null ? { assigned_user_id } : {}),
      });
    } catch {
      setError('Task 수정에 실패했습니다.');
    }
  }

  // ── Task 삭제 ────────────────────────────────────────────────────────────────

  async function handleDeleteTask(taskId: string) {
    setError(null);
    try {
      await deleteTask(taskId);
      const loadedTasks = await getTasks(projectId).catch(() => [] as Task[]);
      setTasks(loadedTasks as Task[]);
    } catch {
      setError('Task 삭제에 실패했습니다.');
    }
  }

  // ── Drag & Drop ──────────────────────────────────────────────────────────────

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const taskId = active.id as string;
    const overId = over.id as string;

    let newStatus: 'plan_reviewing' | 'confirmed' | null = null;

    if (overId === COL_REVIEWING) {
      newStatus = 'plan_reviewing';
    } else if (overId === COL_CONFIRMED) {
      newStatus = 'confirmed';
    } else {
      const targetTask = tasks.find((t) => t.id === overId);
      if (targetTask?.status === 'plan_reviewing' || targetTask?.status === 'confirmed') {
        newStatus = targetTask.status;
      }
    }

    if (newStatus) {
      storeUpdateTask(taskId, { status: newStatus });
      updateTask(taskId, { status: newStatus }).catch(() => setError('Task 상태 변경에 실패했습니다.'));
    }
  }

  // ── Task 전체 확정 (plan_reviewing → confirmed) ───────────────────────────────

  async function handleConfirmAll() {
    const ids = reviewingTasks.map((t) => t.id);
    ids.forEach((id) => storeUpdateTask(id, { status: 'confirmed' }));
    try {
      await Promise.all(ids.map((id) => updateTask(id, { status: 'confirmed' })));
    } catch {
      setError('전체 확정에 실패했습니다.');
    }
  }

  // ── Spec 최종 확정 ────────────────────────────────────────────────────────────

  async function handleFinalConfirmSpec(specId: string) {
    setError(null);
    try {
      await finalConfirmSpec(specId);
      const loadedSpecs = await getSpecs(projectId).catch(() => [] as Spec[]);
      setSpecs(loadedSpecs as Spec[]);
    } catch {
      setError('최종 확정에 실패했습니다.');
    }
  }

  function handleFileDrop(e: React.DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (!file) return;
    handleFileUpload(file, file.type.startsWith('image/') ? 'image' : 'document');
  }

  // ── 렌더 ─────────────────────────────────────────────────────────────────────

  const colStyle: React.CSSProperties = {
    flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column',
    background: 'var(--bg-secondary)', border: '1px solid var(--border)',
    borderRadius: 8, padding: '12px 10px', gap: 8, minHeight: 300,
  };

  const colHeaderStyle: React.CSSProperties = {
    display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4,
  };

  const colCountStyle: React.CSSProperties = {
    fontSize: 11, color: 'var(--text-muted)', background: 'var(--bg-primary)',
    borderRadius: 10, padding: '1px 7px',
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>설계 단계</h2>
        <span className="badge">
          {reviewingTasks.length + confirmedTasks.length}개 Task
        </span>
      </div>

      {/* 숨김 파일 입력 */}
      <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt,.md" style={{ display: 'none' }}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileUpload(f, 'document'); e.target.value = ''; }}
      />
      <input ref={imageInputRef} type="file" accept="image/*" style={{ display: 'none' }}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileUpload(f, 'image'); e.target.value = ''; }}
      />

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#450a0a', color: '#fca5a5', border: '1px solid #7f1d1d', borderRadius: 6, padding: '8px 12px', fontSize: 13, marginBottom: 8 }}>
          <AlertCircle size={14} />
          {error}
          <button className="btn-icon" style={{ marginLeft: 'auto' }} onClick={() => setError(null)}><X size={12} /></button>
        </div>
      )}

      {/* Spec 입력 패널 (Kanban 외부) */}
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
          background: 'var(--bg-secondary)', border: '1px solid var(--border)',
          borderRadius: 8, marginBottom: 10,
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleFileDrop}
      >
        <span style={{ fontSize: 12, color: 'var(--text-muted)', marginRight: 4, flexShrink: 0 }}>Spec 추가</span>
        <button className="btn-sm" style={{ gap: 6, flexShrink: 0 }} onClick={() => fileInputRef.current?.click()}>
          <FileText size={12} /> 파일 업로드
        </button>
        <button className="btn-sm" style={{ gap: 6, flexShrink: 0 }} onClick={() => imageInputRef.current?.click()}>
          <Image size={12} /> 이미지
        </button>
        <button className="btn-sm" style={{ gap: 6, flexShrink: 0 }} onClick={() => setShowTextModal(true)}>
          <Plus size={12} /> 텍스트 입력
        </button>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>
          또는 파일을 여기에 드래그하세요
        </span>
      </div>

      {/* 4컬럼 Kanban */}
      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        <div style={{ display: 'flex', gap: 12, flex: 1, minHeight: 0 }}>

          {/* ── 컬럼 1: Spec 입력 ── */}
          <div style={colStyle}>
            <div style={colHeaderStyle}>
              <span style={{ fontWeight: 600, fontSize: 13 }}>Spec 입력</span>
              <span style={colCountStyle}>{uploadedSpecs.length}</span>
            </div>

            {/* 업로드된 Spec 카드 목록 */}
            {uploadedSpecs.map((spec) => {
              const label = spec.source_type === 'text'
                ? (spec.raw_content?.slice(0, 40) ?? 'Spec 텍스트') + ((spec.raw_content?.length ?? 0) > 40 ? '…' : '')
                : spec.source_path?.split(/[/\\]/).pop() ?? 'Spec 파일';
              const isAnalyzing = analyzingSpecIds.has(spec.id);
              return (
                <div key={spec.id} style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 6, padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <FileText size={12} style={{ flexShrink: 0, color: 'var(--text-muted)' }} />
                    <span style={{ fontSize: 12, fontWeight: 500, flex: 1, wordBreak: 'break-all' }}>{label}</span>
                    <button className="btn-icon" title="삭제" onClick={() => handleDeleteSpec(spec.id)} disabled={isAnalyzing}>
                      <X size={11} />
                    </button>
                  </div>
                  <button
                    className="btn-sm"
                    onClick={() => handleAnalyze(spec.id)}
                    disabled={isAnalyzing}
                    style={{ opacity: isAnalyzing ? 0.5 : 1 }}
                  >
                    {isAnalyzing ? <Loader size={10} /> : <Upload size={10} />}
                    {isAnalyzing ? '분석 중…' : '분석 시작'}
                  </button>
                </div>
              );
            })}

            {uploadedSpecs.length === 0 && (
              <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', marginTop: 12 }}>
                상단 입력 패널에서 Spec을 업로드하세요
              </p>
            )}
          </div>

          {/* ── 컬럼 2: AI 분석중 ── */}
          <div style={colStyle}>
            <div style={colHeaderStyle}>
              <span style={{ fontWeight: 600, fontSize: 13 }}>AI 분석중</span>
              <span style={colCountStyle}>{analyzingSpecs.length}</span>
            </div>

            {analyzingSpecs.map((spec) => {
              const label = spec.source_type === 'text'
                ? (spec.raw_content?.slice(0, 40) ?? 'Spec 텍스트') + ((spec.raw_content?.length ?? 0) > 40 ? '…' : '')
                : spec.source_path?.split(/[/\\]/).pop() ?? 'Spec 파일';
              return (
                <div key={spec.id} style={{ background: 'var(--bg-primary)', border: '1px solid #92400e', borderRadius: 6, padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Loader size={12} style={{ color: '#f59e0b', flexShrink: 0 }} className="animate-spin" />
                    <span style={{ fontSize: 12, fontWeight: 500, flex: 1, wordBreak: 'break-all' }}>{label}</span>
                  </div>
                  <span style={{ fontSize: 11, color: '#f59e0b' }}>Task를 분리하고 있습니다…</span>
                </div>
              );
            })}

            {analyzingSpecs.length === 0 && (
              <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', marginTop: 24 }}>
                분석 시작 후 여기에 표시됩니다
              </p>
            )}
          </div>

          {/* ── 컬럼 3: Task 분해됨 ── */}
          <DroppableColumn
            id={COL_REVIEWING}
            title="Task 분해됨"
            count={reviewingTasks.length}
            headerExtra={
              reviewingTasks.length > 0 ? (
                <button
                  className="btn-sm"
                  style={{ marginLeft: 'auto', background: '#1d4ed8', color: '#fff', fontSize: 10 }}
                  onClick={handleConfirmAll}
                >
                  <CheckCircle size={10} /> 전체 확정→
                </button>
              ) : null
            }
          >
            <SortableContext items={reviewingTasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
              {reviewingTasks.map((task) => (
                <DesignTaskCard
                  key={task.id}
                  task={task}
                  onEdit={setEditingTask}
                  onDelete={handleDeleteTask}
                />
              ))}
            </SortableContext>
            {reviewingTasks.length === 0 && (
              <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', marginTop: 24 }}>
                분석 완료 후 Task가 여기에 나타납니다
              </p>
            )}
          </DroppableColumn>

          {/* ── 컬럼 4: 확정됨 ── */}
          <DroppableColumn
            id={COL_CONFIRMED}
            title="확정됨"
            count={confirmedTasks.length}
            headerExtra={
              confirmedTasks.length > 0 && uploadedSpecs.length > 0 ? (
                <button
                  className="btn-sm"
                  style={{ marginLeft: 'auto', background: '#166534', color: '#bbf7d0', fontSize: 10 }}
                  onClick={() => handleFinalConfirmSpec(uploadedSpecs[0].id)}
                >
                  Spec 확정
                </button>
              ) : null
            }
          >
            <SortableContext items={confirmedTasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
              {confirmedTasks.map((task) => (
                <DesignTaskCard
                  key={task.id}
                  task={task}
                  onEdit={setEditingTask}
                  onDelete={handleDeleteTask}
                />
              ))}
            </SortableContext>
            {confirmedTasks.length === 0 && (
              <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', marginTop: 24 }}>
                Task를 드래그하거나 전체 확정 버튼을 사용하세요
              </p>
            )}
          </DroppableColumn>

        </div>
      </DndContext>

      {showTextModal && (
        <TextInputModal onSubmit={handleTextUpload} onClose={() => setShowTextModal(false)} />
      )}
      {editingTask && (
        <TaskEditModal
          task={editingTask}
          onSave={handleSaveTask}
          onClose={() => setEditingTask(null)}
        />
      )}
    </div>
  );
}
