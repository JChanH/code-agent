import { useEffect, useState, useCallback } from 'react';
import { GitCommit, GitPullRequest, RefreshCw, RotateCcw, Upload } from 'lucide-react';
import DiffViewer from '../../components/diff-viewer/DiffViewer';
import { gitApi } from '../../services/api';
import { useAppStore } from '../../stores';
import type { GitFileStatus, GitLogEntry } from '../../types';

interface Props {
  projectId: string;
}

export default function GitManagement({ projectId }: Props) {
  const { selectedUserId } = useAppStore();

  const [files, setFiles] = useState<GitFileStatus[]>([]);
  const [staged, setStaged] = useState<Set<string>>(new Set());
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [diff, setDiff] = useState('');
  const [commitMsg, setCommitMsg] = useState('');
  const [log, setLog] = useState<GitLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [branch, setBranch] = useState('');

  const userId = selectedUserId ?? '';

  const refresh = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const [statusRes, logRes, branchRes] = await Promise.all([
        gitApi.status(projectId, userId),
        gitApi.log(projectId, userId),
        gitApi.branch(projectId, userId),
      ]);
      setFiles(statusRes);
      setLog(logRes);
      setBranch(branchRes.branch);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [projectId, userId]);

  useEffect(() => { refresh(); }, [refresh]);

  async function handleFileClick(path: string) {
    setSelectedFile(path);
    if (!userId) return;
    const res = await gitApi.diff(projectId, userId, path).catch(() => ({ diff: '' }));
    setDiff(res.diff);
  }

  function toggleStage(path: string) {
    setStaged((prev) => {
      const next = new Set(prev);
      next.has(path) ? next.delete(path) : next.add(path);
      return next;
    });
  }

  async function handleStage() {
    if (!userId || staged.size === 0) return;
    await gitApi.stage(projectId, userId, Array.from(staged));
    refresh();
  }

  async function handleCommit() {
    if (!userId || !commitMsg.trim()) return;
    await gitApi.commit(projectId, userId, commitMsg.trim());
    setCommitMsg('');
    refresh();
  }

  async function handlePull(strategy: 'rebase' | 'merge') {
    if (!userId) return;
    await gitApi.pull(projectId, userId, strategy);
    refresh();
  }

  async function handlePush() {
    if (!userId) return;
    await gitApi.push(projectId, userId);
  }

  async function handleRevert(path: string) {
    if (!userId) return;
    await gitApi.revert(projectId, userId, path);
    refresh();
  }

  if (!userId) {
    return (
      <div className="page-container empty-state">
        <p>사이드바에서 사용자를 선택해 주세요.</p>
      </div>
    );
  }

  return (
    <div className="page-container git-page">
      <div className="page-header">
        <h2>Git 관리</h2>
        <span className="badge">{branch}</span>
        <button className="icon-btn" onClick={refresh} title="새로고침">
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="git-layout">
        {/* 좌측: 변경 파일 목록 */}
        <div className="git-files">
          <div className="git-files-header">
            <span>변경 파일 ({files.length})</span>
            <button className="btn-sm" onClick={handleStage} disabled={staged.size === 0}>
              Stage 선택
            </button>
          </div>

          <ul>
            {files.map((f) => (
              <li
                key={f.path}
                className={`git-file-item ${selectedFile === f.path ? 'active' : ''}`}
                onClick={() => handleFileClick(f.path)}
              >
                <input
                  type="checkbox"
                  checked={staged.has(f.path)}
                  onChange={() => toggleStage(f.path)}
                  onClick={(e) => e.stopPropagation()}
                />
                <span className="git-file-status">{f.status}</span>
                <span className="git-file-path">{f.path}</span>
                <button
                  className="icon-btn revert-btn"
                  title="되돌리기"
                  onClick={(e) => { e.stopPropagation(); handleRevert(f.path); }}
                >
                  <RotateCcw size={12} />
                </button>
              </li>
            ))}
          </ul>

          {/* Commit 영역 */}
          <div className="git-commit-area">
            <textarea
              value={commitMsg}
              onChange={(e) => setCommitMsg(e.target.value)}
              placeholder="커밋 메시지"
              rows={3}
            />
            <div className="git-actions">
              <button className="btn-primary" onClick={handleCommit} disabled={!commitMsg.trim()}>
                <GitCommit size={14} /> Commit
              </button>
              <button className="btn-secondary" onClick={() => handlePull('rebase')}>
                Pull (rebase)
              </button>
              <button className="btn-secondary" onClick={handlePush}>
                <Upload size={14} /> Push
              </button>
            </div>
          </div>

          {/* 커밋 로그 */}
          <div className="git-log">
            <div className="git-log-header">커밋 로그</div>
            <ul>
              {log.map((entry) => (
                <li key={entry.hash} className="git-log-item">
                  <span className="git-log-hash">{entry.short_hash}</span>
                  <span className="git-log-msg">{entry.message}</span>
                  <span className="git-log-date">{entry.relative_date}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* 우측: Diff 뷰어 */}
        <div className="git-diff">
          {selectedFile ? (
            <>
              <div className="git-diff-header">{selectedFile}</div>
              <DiffViewer original="" modified={diff} />
            </>
          ) : (
            <div className="empty-state">
              <GitPullRequest size={32} />
              <p>파일을 선택하면 diff를 볼 수 있습니다.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
