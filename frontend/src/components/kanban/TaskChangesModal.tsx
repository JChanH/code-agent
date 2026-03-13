import { useEffect, useState } from "react";
import { X, RotateCcw, FileCode, GitCommit, Loader } from "lucide-react";
import { getTaskChanges, rollbackTask } from "../../api/project/projectApis";
import type { Task } from "../../types";

const FILE_STATUS_LABEL: Record<string, { label: string; color: string }> = {
  M: { label: "수정", color: "#f59e0b" },
  A: { label: "추가", color: "#22c55e" },
  D: { label: "삭제", color: "#ef4444" },
  R: { label: "이름변경", color: "#8b5cf6" },
};

interface Props {
  task: Task;
  onClose: () => void;
  onRollback: (task: Task) => void;
}

export default function TaskChangesModal({ task, onClose, onRollback }: Props) {
  const [loading, setLoading] = useState(true);
  const [changes, setChanges] = useState<{
    commit_hash: string | null;
    diff: string | null;
    files: { status: string; path: string }[];
  } | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [rolling, setRolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTaskChanges(task.id)
      .then((data) => {
        setChanges(data);
        if (data.files.length > 0) setSelectedFile(data.files[0].path);
      })
      .catch(() => setError("변경사항을 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [task.id]);

  async function handleRollback() {
    if (!window.confirm(`"${task.title}" 의 변경사항을 롤백할까요?\n이전 상태로 되돌리는 새 커밋이 생성됩니다.`)) return;
    setRolling(true);
    try {
      await rollbackTask(task.id);
      onRollback({ ...task, status: "confirmed", git_commit_hash: null });
      onClose();
    } catch {
      setError("롤백에 실패했습니다.");
    } finally {
      setRolling(false);
    }
  }

  const fileDiff = (() => {
    if (!changes?.diff || !selectedFile) return "";
    const sections = changes.diff.split(/^diff --git /m);
    const match = sections.find((s) => s.includes(` b/${selectedFile}`));
    return match ? "diff --git " + match : "";
  })();

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal"
        style={{ width: 780, maxWidth: "95vw", maxHeight: "85vh", display: "flex", flexDirection: "column" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <GitCommit size={15} style={{ color: "#10b981" }} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>{task.title}</span>
          </div>
          <button onClick={onClose}><X size={15} /></button>
        </div>

        {/* Commit hash */}
        {changes?.commit_hash && (
          <div style={{ padding: "8px 16px", borderBottom: "1px solid var(--border)", fontSize: 11, color: "var(--text-muted)", fontFamily: "monospace" }}>
            commit {changes.commit_hash}
          </div>
        )}

        {loading && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 40, gap: 8, color: "var(--text-muted)" }}>
            <Loader size={14} className="animate-spin" /> 불러오는 중...
          </div>
        )}

        {error && (
          <div className="modal-error" style={{ margin: 16 }}>{error}</div>
        )}

        {!loading && !error && changes && (
          <>
            {changes.commit_hash === null ? (
              <div style={{ padding: 24, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
                커밋 정보가 없습니다. 에이전트 실행 후 생성됩니다.
              </div>
            ) : (
              <div style={{ display: "flex", flex: 1, overflow: "hidden", minHeight: 0 }}>
                {/* File list */}
                <div style={{ width: 220, flexShrink: 0, borderRight: "1px solid var(--border)", overflowY: "auto", padding: "8px 0" }}>
                  {changes.files.map((f) => {
                    const meta = FILE_STATUS_LABEL[f.status] ?? { label: f.status, color: "#6b7280" };
                    return (
                      <div
                        key={f.path}
                        onClick={() => setSelectedFile(f.path)}
                        style={{
                          display: "flex", alignItems: "center", gap: 8, padding: "6px 12px",
                          cursor: "pointer", fontSize: 12,
                          background: selectedFile === f.path ? "var(--bg-3)" : "transparent",
                        }}
                      >
                        <FileCode size={12} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
                        <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "var(--text)" }}>
                          {f.path.split("/").pop()}
                        </span>
                        <span style={{ fontSize: 10, color: meta.color, fontWeight: 600 }}>{meta.label}</span>
                      </div>
                    );
                  })}
                </div>

                {/* Diff viewer */}
                <div style={{ flex: 1, overflowY: "auto", background: "var(--bg-1)" }}>
                  {fileDiff ? (
                    <pre style={{ margin: 0, padding: "12px 16px", fontSize: 11.5, lineHeight: 1.6, fontFamily: "monospace", whiteSpace: "pre" }}>
                      {fileDiff.split("\n").map((line, i) => {
                        const color = line.startsWith("+") && !line.startsWith("+++")
                          ? "#22c55e"
                          : line.startsWith("-") && !line.startsWith("---")
                          ? "#ef4444"
                          : line.startsWith("@@")
                          ? "#8b5cf6"
                          : "var(--text)";
                        return (
                          <span key={i} style={{ color, display: "block" }}>{line}</span>
                        );
                      })}
                    </pre>
                  ) : (
                    <div style={{ padding: 24, color: "var(--text-muted)", fontSize: 12 }}>파일을 선택하세요.</div>
                  )}
                </div>
              </div>
            )}
          </>
        )}

        {/* Footer */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, padding: "12px 16px", borderTop: "1px solid var(--border)" }}>
          <button className="btn-sm" onClick={onClose}>닫기</button>
          {changes?.commit_hash && (
            <button
              className="btn-sm"
              style={{ background: "rgba(239,68,68,0.15)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.3)" }}
              onClick={handleRollback}
              disabled={rolling}
            >
              {rolling ? <Loader size={12} className="animate-spin" /> : <RotateCcw size={12} />}
              {rolling ? "롤백 중..." : "롤백"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
