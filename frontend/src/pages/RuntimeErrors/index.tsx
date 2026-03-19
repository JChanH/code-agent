import { useEffect, useState } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { useRuntimeErrorStore } from '../../stores/runtimeErrorStore';
import { getRuntimeErrors } from '../../api/runtimeErrors/runtimeErrorApis';
import type { RuntimeErrorLevel } from '../../types';
import './RuntimeErrors.css';

const LEVEL_COLORS: Record<RuntimeErrorLevel, string> = {
  error: 'badge-error',
  warning: 'badge-warning',
  critical: 'badge-critical',
  info: 'badge-info',
};

const LIMIT = 50;

export default function RuntimeErrors() {
  const { errors, totalCount, isLoading, setErrors, setLoading } = useRuntimeErrorStore();
  const [page, setPage] = useState(0);
  const [levelFilter, setLevelFilter] = useState<string>('all');

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

  const filtered = levelFilter === 'all' ? errors : errors.filter((e) => e.level === levelFilter);
  const totalPages = Math.max(1, Math.ceil(totalCount / LIMIT));

  function formatTime(ts: string | null): string {
    if (!ts) return '—';
    const d = new Date(ts);
    return d.toLocaleString('ko-KR', { hour12: false });
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
                <th>수신 시각</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((err) => (
                <tr key={err.id}>
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
          <span>
            {page + 1} / {totalPages}
          </span>
          <button onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}>
            다음
          </button>
        </div>
      )}
    </div>
  );
}
