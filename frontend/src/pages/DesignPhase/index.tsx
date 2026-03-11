import { useEffect, useRef, useState } from 'react';
import { Upload, FileText, Image, Plus, X, CheckCircle, Loader, AlertCircle } from 'lucide-react';
import KanbanBoard from '../../components/kanban/KanbanBoard';
import { useTaskStore } from '../../stores';
import { useWebSocket } from '../../hooks/useWebSocket';
import {
  getSpecs,
  getTasks,
  uploadSpec,
  removeSpec,
  analyzeSpec,
  confirmSpec,
  updateTask,
} from '../../api/project/projectApis';
import type { Spec, Task, TaskStatus } from '../../types';

const TASK_COLUMNS = [
  { id: 'backlog' as TaskStatus, title: 'Task 분해됨' },
  { id: 'planning' as TaskStatus, title: '계획 중' },
  { id: 'plan_review' as TaskStatus, title: '검토 중' },
  { id: 'coding' as TaskStatus, title: '확정됨' },
];

const DESIGN_STATUSES: TaskStatus[] = ['backlog', 'planning', 'plan_review', 'coding'];

interface Props {
  projectId: string;
}

// ── Spec 상태 뱃지 ────────────────────────────────────────────────────────────

function SpecStatusBadge({ status }: { status: Spec['status'] }) {
  if (status === 'analyzing') {
    return (
      <span className="badge" style={{ background: '#854d0e', color: '#fef08a', display: 'flex', alignItems: 'center', gap: 4 }}>
        <Loader size={10} />
        분석 중
      </span>
    );
  }
  if (status === 'analyzed') {
    return <span className="badge" style={{ background: '#166534', color: '#bbf7d0' }}>분석 완료</span>;
  }
  if (status === 'confirmed') {
    return <span className="badge" style={{ background: '#1e3a5f', color: '#bae6fd' }}>확정됨</span>;
  }
  return <span className="badge">업로드됨</span>;
}

// ── Spec 카드 ─────────────────────────────────────────────────────────────────

function SpecCard({
  spec,
  onAnalyze,
  onConfirm,
  onDelete,
  isAnalyzing,
}: {
  spec: Spec;
  onAnalyze: (id: string) => void;
  onConfirm: (id: string) => void;
  onDelete: (id: string) => void;
  isAnalyzing: boolean;
}) {
  const canAnalyze = spec.status === 'uploaded' || spec.status === 'analyzed';
  const canConfirm = spec.status === 'analyzed';
  const label =
    spec.source_type === 'text'
      ? (spec.raw_content?.slice(0, 50) || 'Spec 텍스트') +
        (spec.raw_content && spec.raw_content.length > 50 ? '…' : '')
      : spec.source_path?.split(/[/\\]/).pop() || 'Spec 파일';

  return (
    <div
      style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
        borderRadius: 6,
        padding: '10px 12px',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 13, fontWeight: 500, flex: 1, wordBreak: 'break-all' }}>
          {label}
        </span>
        <SpecStatusBadge status={spec.status} />
        <button
          className="btn-icon"
          onClick={() => onDelete(spec.id)}
          title="삭제"
          disabled={isAnalyzing}
          style={{ opacity: isAnalyzing ? 0.4 : 1 }}
        >
          <X size={12} />
        </button>
      </div>
      <div style={{ display: 'flex', gap: 6 }}>
        {canAnalyze && (
          <button
            className="btn-sm"
            onClick={() => onAnalyze(spec.id)}
            disabled={isAnalyzing}
            style={{ opacity: isAnalyzing ? 0.5 : 1 }}
          >
            {isAnalyzing ? <Loader size={10} /> : <FileText size={10} />}
            {isAnalyzing ? '분석 중…' : '분석 시작'}
          </button>
        )}
        {canConfirm && (
          <button
            className="btn-sm"
            onClick={() => onConfirm(spec.id)}
            style={{ background: '#166534', color: '#bbf7d0' }}
          >
            <CheckCircle size={10} />
            확정
          </button>
        )}
      </div>
    </div>
  );
}

// ── 텍스트 입력 모달 ──────────────────────────────────────────────────────────

function TextInputModal({ onSubmit, onClose }: { onSubmit: (text: string) => void; onClose: () => void }) {
  const [text, setText] = useState('');
  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}
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

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────

export default function DesignPhase({ projectId }: Props) {
  const {
    tasks, specs, analyzingSpecIds,
    setTasks, setSpecs, addSpec,
    updateTask: storeUpdateTask,
    removeSpec: storeRemoveSpec,
    updateSpec,
  } = useTaskStore();

  const [error, setError] = useState<string | null>(null);
  const [showTextModal, setShowTextModal] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  useWebSocket(projectId);

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
  const designTasks = tasks.filter((t) => t.project_id === projectId && DESIGN_STATUSES.includes(t.status));

  // 파일 업로드 api연결
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

  async function handleConfirm(specId: string) {
    setError(null);
    try {
      await confirmSpec(specId);
      updateSpec(specId, { status: 'confirmed' });
    } catch {
      setError('Spec 확정에 실패했습니다.');
    }
  }

  async function handleDelete(specId: string) {
    setError(null);
    try {
      await removeSpec(specId);
      storeRemoveSpec(specId);
    } catch {
      setError('삭제에 실패했습니다.');
    }
  }

  async function handleTaskStatusChange(taskId: string, newStatus: TaskStatus) {
    storeUpdateTask(taskId, { status: newStatus });
    try {
      await updateTask(taskId, { status: newStatus });
    } catch {
      // 낙관적 업데이트 유지
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (!file) return;
    handleFileUpload(file, file.type.startsWith('image/') ? 'image' : 'document');
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>설계 단계</h2>
        <span className="badge">{projectSpecs.length}개 Spec · {designTasks.length}개 Task</span>
      </div>

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#450a0a', color: '#fca5a5', border: '1px solid #7f1d1d', borderRadius: 6, padding: '8px 12px', fontSize: 13, marginBottom: 8 }}>
          <AlertCircle size={14} />
          {error}
          <button className="btn-icon" style={{ marginLeft: 'auto' }} onClick={() => setError(null)}><X size={12} /></button>
        </div>
      )}

      {/* 업로드 드롭존 */}
      <div className="dropzone" onDragOver={(e) => e.preventDefault()} onDrop={handleDrop}>
        <Upload size={16} />
        <span>파일 / 이미지를 드래그하거나</span>
        <div style={{ display: 'flex', gap: 6, marginLeft: 'auto' }}>
          <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt,.md" style={{ display: 'none' }}
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileUpload(f, 'document'); e.target.value = ''; }}
          />
          <input ref={imageInputRef} type="file" accept="image/*" style={{ display: 'none' }}
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileUpload(f, 'image'); e.target.value = ''; }}
          />
          <button className="btn-sm" onClick={() => fileInputRef.current?.click()}><FileText size={11} /> 파일 업로드</button>
          <button className="btn-sm" onClick={() => imageInputRef.current?.click()}><Image size={11} /> 이미지</button>
          <button className="btn-sm" onClick={() => setShowTextModal(true)}><Plus size={11} /> 텍스트 입력</button>
        </div>
      </div>

      {/* Spec 목록 */}
      {projectSpecs.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            업로드된 Spec ({projectSpecs.length})
          </div>
          {projectSpecs.map((spec) => (
            <SpecCard
              key={spec.id}
              spec={spec}
              onAnalyze={handleAnalyze}
              onConfirm={handleConfirm}
              onDelete={handleDelete}
              isAnalyzing={analyzingSpecIds.has(spec.id)}
            />
          ))}
        </div>
      )}

      {/* 분해된 Task Kanban */}
      <KanbanBoard
        columns={TASK_COLUMNS}
        tasks={designTasks}
        onStatusChange={handleTaskStatusChange}
      />

      {showTextModal && <TextInputModal onSubmit={handleTextUpload} onClose={() => setShowTextModal(false)} />}
    </div>
  );
}
