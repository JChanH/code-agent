import { useEffect, useState } from 'react';
import { AlertCircle, FolderOpen, RefreshCw, X } from 'lucide-react';
import { useAppStore } from '../../stores';
import { useRuntimeErrorStore } from '../../stores/runtimeErrorStore';
import {
  getRuntimeErrors,
  updateRuntimeErrorSourcePath,
  updateRuntimeErrorStatus,
} from '../../api/runtimeErrors/runtimeErrorApis';
import type { RuntimeError, RuntimeErrorLevel, RuntimeErrorStatus } from '../../types';
import './RuntimeErrors.css';

const LEVEL_COLORS: Record<RuntimeErrorLevel, string> = {
  error: 'badge-error',
  warning: 'badge-warning',
  critical: 'badge-critical',
  info: 'badge-info',
};

const STATUS_LABELS: Record<RuntimeErrorStatus, string> = {
  pending: '대기',
  analyzed: '분석완료',
  resolved: '해결됨',
  ignored: '무시',
};

const LIMIT = 50;

export default function RuntimeErrors() {
  const { errors, totalCount, isLoading, setErrors, setLoading, updateErrorStatus, updateErrorSourcePath } =
    useRuntimeErrorStore();
  const { projects, selectedProjectId } = useAppStore();
  const currentProject = projects.find((p) => p.id === selectedProjectId);

  const [page, setPage] = useState(0);
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [selected, setSelected] = useState<RuntimeError | null>(null);
  const [sourcePath, setSourcePath] = useState('');
  const [savingPath, setSavingPath] = useState(false);

  async function fetchErrors(pageNum: number) {
    setLoading(true);
    const result = await getRuntimeErrors({ limit: LIMIT, offset: pageNum * LIMIT });
    if (result.success && result.data) {
      setErrors(result.data.items, result.data.total);
    }
    setLoading(false);
  }

  useEffect(() => {
    fetchErrors(page);
  }, [page]);

  function openModal(err: RuntimeError) {
    setSelected(err);
    setSourcePath(err.source_path ?? currentProject?.local_repo_path ?? '');
  }

  function closeModal() {
    setSelected(null);
    setSourcePath('');
  }

  async function handleStatusChange(status: RuntimeErrorStatus) {
    if (!selected) return;
    const result = await updateRuntimeErrorStatus(selected.id, status);
    if (result.success) {
      updateErrorStatus(selected.id, status);
      setSelected((prev) => (prev ? { ...prev, status } : null));
    }
  }

  async function handleSavePath() {
    if (!selected || !sourcePath.trim()) return;
    setSavingPath(true);
    const result = await updateRuntimeErrorSourcePath(selected.id, sourcePath.trim());
    if (result.success) {
      updateErrorSourcePath(selected.id, sourcePath.trim());
      setSelected((prev) => (prev ? { ...prev, source_path: sourcePath.trim() } : null));
    }
    setSavingPath(false);
  }

  const filtered = levelFilter === 'all' ? errors : errors.filter((e) => e.level === levelFilter);
  const totalPages = Math.max(1, Math.ceil(totalCount / LIMIT));

  function formatTime(ts: string | null): string {
    if (!ts) return '—';
    return new Date(ts).toLocaleString('ko-KR', { hour12: false });
  }

  return (
    <div className="re-page">
      <div className="re-header">
        <div className="re-title">
          <AlertCircle size={16} />
          <span>런타임 에러</span>
          <span className="re-count">{totalCount}건</span>
        </div>
        <div className="re-controls">
          <select
            className="re-filter"
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
          >
            <option value="all">전체 레벨</option>
            <option value="error">Error</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
            <option value="info">Info</option>
          </select>
          <button
            className="re-refresh"
            onClick={() => fetchErrors(page)}
            disabled={isLoading}
            title="새로고침"
          >
            <RefreshCw size={14} className={isLoading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      <div className="re-table-wrap">
        {filtered.length === 0 ? (
          <div className="re-empty">
            <AlertCircle size={32} style={{ opacity: 0.2 }} />
            <p>수신된 런타임 에러가 없습니다.</p>
          </div>
        ) : (
          <table className="re-table">
            <thead>
              <tr>
                <th>레벨</th>
                <th>상태코드</th>
                <th>메서드</th>
                <th>경로</th>
                <th>메시지</th>
                <th>프로젝트</th>
                <th>검토 상태</th>
                <th>수신 시각</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((err) => (
                <tr key={err.id} className="re-row" onClick={() => openModal(err)}>
                  <td>
                    <span className={`re-badge ${LEVEL_COLORS[err.level] ?? 'badge-error'}`}>
                      {err.level}
                    </span>
                  </td>
                  <td className="re-code">{err.metadata?.status_code ?? err.error_code}</td>
                  <td className="re-code">{err.metadata?.method ?? '—'}</td>
                  <td className="re-path" title={err.metadata?.path}>
                    {err.metadata?.path ?? '—'}
                  </td>
                  <td className="re-message" title={err.message}>
                    {err.message.length > 80 ? err.message.slice(0, 80) + '…' : err.message}
                  </td>
                  <td className="re-project">{err.project_id}</td>
                  <td>
                    <span className={`re-status-chip re-status-${err.status}`}>
                      {STATUS_LABELS[err.status]}
                    </span>
                  </td>
                  <td className="re-time">{formatTime(err.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {totalPages > 1 && (
        <div className="re-pagination">
          <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}>
            이전
          </button>
          <span>{page + 1} / {totalPages}</span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
          >
            다음
          </button>
        </div>
      )}

      {selected && (
        <div className="re-overlay" onClick={closeModal}>
          <div className="re-modal" onClick={(e) => e.stopPropagation()}>
            {/* 헤더 */}
            <div className="re-modal-header">
              <div className="re-modal-title">
                <span className={`re-badge ${LEVEL_COLORS[selected.level] ?? 'badge-error'}`}>
                  {selected.level}
                </span>
                <span className="re-modal-endpoint">
                  {selected.metadata?.method} {selected.metadata?.path}
                </span>
              </div>
              <button className="re-modal-close" onClick={closeModal}>
                <X size={16} />
              </button>
            </div>

            {/* 에러 정보 */}
            <div className="re-modal-section">
              <div className="re-modal-meta">
                <span className="re-modal-label">상태코드</span>
                <span className="re-code">{selected.metadata?.status_code ?? selected.error_code}</span>
                <span className="re-modal-label">프로젝트</span>
                <span>{selected.project_id}</span>
                <span className="re-modal-label">수신 시각</span>
                <span>{formatTime(selected.created_at)}</span>
              </div>
              <div className="re-modal-message">{selected.message}</div>
            </div>

            {/* 소스 코드 경로 */}
            <div className="re-modal-section">
              <div className="re-modal-section-title">
                <FolderOpen size={13} />
                소스 코드 경로
              </div>
              <div className="re-path-row">
                <input
                  className="re-path-input"
                  type="text"
                  placeholder="/src/routes/users.py"
                  value={sourcePath}
                  onChange={(e) => setSourcePath(e.target.value)}
                />
                <button
                  className="re-analyze-btn"
                  onClick={handleSavePath}
                  disabled={savingPath || !sourcePath.trim()}
                >
                  {savingPath ? '저장 중…' : '분석 요청'}
                </button>
              </div>
            </div>

            {/* 수정 방안 (analyzed일 때만) */}
            {selected.status === 'analyzed' && selected.fix_suggestion && (
              <div className="re-modal-section">
                <div className="re-modal-section-title">수정 방안</div>
                <pre className="re-fix-suggestion">{selected.fix_suggestion}</pre>
              </div>
            )}

            {/* 검토 상태 */}
            <div className="re-modal-section">
              <div className="re-modal-section-title">검토 상태</div>
              <div className="re-status-btns">
                {(Object.keys(STATUS_LABELS) as RuntimeErrorStatus[]).map((s) => (
                  <button
                    key={s}
                    className={`re-status-btn re-status-btn-${s}${selected.status === s ? ' active' : ''}`}
                    onClick={() => handleStatusChange(s)}
                  >
                    {STATUS_LABELS[s]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
