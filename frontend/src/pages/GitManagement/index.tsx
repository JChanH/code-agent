import { useState } from "react";
import { GitCommit, GitPullRequest, RefreshCw, RotateCcw, Upload, GitMerge } from "lucide-react";
import { MOCK_GIT_FILES, MOCK_GIT_LOG, MOCK_DIFF } from "../../mock/data";
import { useAppStore } from "../../stores";

interface Props { projectId: string; }

function statusClass(s: string) {
  if (s === "A") return "added";
  if (s === "M") return "modified";
  return "untracked";
}

export default function GitManagement({ projectId: _projectId }: Props) {
  const { users, selectedUserId } = useAppStore();
  const user = users.find((u) => u.id === selectedUserId);
  const branch = user ? `worktree/${user.username}` : "worktree/kim";

  const [staged, setStaged] = useState<Set<string>>(new Set());
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [commitMsg, setCommitMsg] = useState("");

  function toggleStage(path: string) {
    setStaged((prev) => {
      const next = new Set(prev);
      next.has(path) ? next.delete(path) : next.add(path);
      return next;
    });
  }

  const stageAll = () => setStaged(new Set(MOCK_GIT_FILES.map((f) => f.path)));

  const diffLines = MOCK_DIFF.split("\n").map((line, i) => {
    let cls = "diff-meta";
    if (!line.startsWith("+++") && !line.startsWith("---")) {
      if (line.startsWith("+")) cls = "diff-add";
      else if (line.startsWith("-")) cls = "diff-remove";
      else if (line.startsWith("@@")) cls = "diff-hunk";
    }
    return <div key={i} className={`diff-line ${cls}`}>{line || "\u00a0"}</div>;
  });

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>Git 관리</h2>
        <span className="badge">{branch}</span>
        <button className="icon-btn" title="새로고침"><RefreshCw size={14} /></button>
      </div>
      <div className="git-layout">
        <div className="git-files">
          <div className="git-files-header">
            <span>변경 파일 ({MOCK_GIT_FILES.length})</span>
            <button className="btn-sm" onClick={stageAll}>Stage All</button>
          </div>
          <ul className="git-file-list">
            {MOCK_GIT_FILES.map((f) => (
              <li
                key={f.path}
                className={`git-file-item ${selectedFile === f.path ? "active" : ""}`}
                onClick={() => setSelectedFile(f.path)}
              >
                <input
                  type="checkbox"
                  checked={staged.has(f.path)}
                  onChange={() => toggleStage(f.path)}
                  onClick={(e) => e.stopPropagation()}
                />
                <span className={`git-file-status ${statusClass(f.status)}`}>{f.status}</span>
                <span className="git-file-path">{f.path}</span>
                <button className="icon-btn revert-btn" title="되돌리기" onClick={(e) => e.stopPropagation()}>
                  <RotateCcw size={11} />
                </button>
              </li>
            ))}
          </ul>
          <div className="git-commit-area">
            <textarea
              value={commitMsg}
              onChange={(e) => setCommitMsg(e.target.value)}
              placeholder="커밋 메시지 (예: feat: 사용자 인증 API 구현)"
              rows={3}
            />
            <div className="git-actions">
              <button className="btn-sm" onClick={stageAll}>Stage Selected</button>
              <button className="btn-sm" onClick={stageAll}>Stage All</button>
            </div>
            <div className="git-actions">
              <button className="btn-primary" disabled={!commitMsg.trim() || staged.size === 0}>
                <GitCommit size={13} /> Commit
              </button>
              <button className="btn-secondary"><GitMerge size={13} /> Pull</button>
              <button className="btn-secondary"><Upload size={13} /> Push</button>
            </div>
          </div>
          <div className="git-log">
            <div className="git-log-header">커밋 이력 (최근)</div>
            <ul className="git-log-list">
              {MOCK_GIT_LOG.map((entry) => (
                <li key={entry.hash} className="git-log-item">
                  <span className="git-log-hash">{entry.short_hash}</span>
                  <span className="git-log-msg">{entry.message}</span>
                  <span className="git-log-date">{entry.relative_date}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="git-diff">
          {selectedFile ? (
            <>
              <div className="git-diff-header">{selectedFile}</div>
              <div className="git-diff-body">{diffLines}</div>
            </>
          ) : (
            <div className="empty-state">
              <GitPullRequest size={32} style={{ opacity: 0.2 }} />
              <p>파일을 선택하면 diff를 볼 수 있습니다.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
