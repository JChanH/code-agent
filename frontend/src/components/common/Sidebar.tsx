import { useState } from "react";
import { FolderOpen, GitBranch, Layers, Settings, Plus, Code2, Terminal, X, FolderSearch, Loader2 } from "lucide-react";
import { useAppStore } from "../../stores";
import { createProject } from "../../api/project/projectApis";
import type { ProjectCreate, ProjectType } from "../../api/project/projectTypes";
import type { ActiveTab } from "../../types";

const TABS: { id: ActiveTab; label: string; icon: React.ReactNode }[] = [
  { id: "design", label: "설계 Kanban", icon: <Layers size={14} /> },
  { id: "dev", label: "개발 Kanban", icon: <Code2 size={14} /> },
  { id: "console", label: "콘솔", icon: <Terminal size={14} /> },
  { id: "git", label: "Git 관리", icon: <GitBranch size={14} /> },
  { id: "settings", label: "프로젝트 설정", icon: <Settings size={14} /> },
];

const EMPTY_FORM: ProjectCreate = {
  project_type: "existing",
  name: "",
  repo_url: "",
  local_repo_path: "",
  description: "",
  main_branch: "main",
  project_stack: "python",
  framework: "fastapi",
};

const LOCAL_REPO_HINT: Record<string, string> = {
  existing: "에이전트가 코드베이스를 읽는 경로",
  new: "프로젝트를 생성할 로컬 폴더",
};

function NewProjectModal({ onClose, onCreated }: { onClose: () => void; onCreated: (id: string) => void }) {
  const { addProject } = useAppStore();
  const [form, setForm] = useState<ProjectCreate>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function set(field: keyof ProjectCreate, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function switchType(type: ProjectType) {
    setForm((prev) => ({ ...prev, project_type: type, local_repo_path: "" }));
    setError(null);
  }

  async function handlePickDirectory() {
    const path = await window.electronAPI?.openDirectory();
    if (path) set("local_repo_path", path);
  }

  async function handleSubmit(e: { preventDefault: () => void }) {
    e.preventDefault();
    if (!form.local_repo_path?.trim()) {
      setError("로컬 경로는 필수입니다.");
      return;
    }
    setLoading(true);
    setError(null);
    const result = await createProject(form);
    setLoading(false);
    if (result.success && result.data) {
      addProject(result.data);
      onCreated(result.data.id);
      onClose();
    } else {
      setError("프로젝트 생성에 실패했습니다.");
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <span>새 프로젝트</span>
          <button onClick={onClose}><X size={16} /></button>
        </div>

        {/* 프로젝트 타입 선택 */}
        <div className="modal-type-toggle">
          <button
            className={`modal-type-btn ${form.project_type === "existing" ? "active" : ""}`}
            onClick={() => switchType("existing")}
            type="button"
          >
            기존 프로젝트
          </button>
          <button
            className={`modal-type-btn ${form.project_type === "new" ? "active" : ""}`}
            onClick={() => switchType("new")}
            type="button"
          >
            신규 프로젝트
          </button>
        </div>

        <form className="modal-form" onSubmit={handleSubmit}>
          <label>
            프로젝트 이름 <span className="required">*</span>
            <input value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="My Project" required />
          </label>

          <label>
            로컬 경로 <span className="required">*</span>
            <div className="input-with-btn">
              <input
                value={form.local_repo_path ?? ""}
                onChange={(e) => set("local_repo_path", e.target.value)}
                placeholder="C:/Users/dev/projects/my-project"
                required
              />
              <button type="button" className="input-browse-btn" onClick={handlePickDirectory} title="폴더 선택">
                <FolderSearch size={15} />
              </button>
            </div>
            <span className="field-hint">{LOCAL_REPO_HINT[form.project_type]}</span>
          </label>

          <label>
            Git 저장소 URL <span className="optional">(선택)</span>
            <input value={form.repo_url ?? ""} onChange={(e) => set("repo_url", e.target.value)} placeholder="https://github.com/user/repo" />
            <span className="field-hint">나중에 Git 관리 화면에서 설정 가능</span>
          </label>

          <label>
            메인 브랜치
            <input value={form.main_branch ?? "main"} onChange={(e) => set("main_branch", e.target.value)} placeholder="main" />
          </label>

          <label>
            설명 <span className="optional">(선택)</span>
            <input value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} placeholder="프로젝트 설명" />
          </label>

          {error && <p className="modal-error">{error}</p>}

          <button className="modal-submit" type="submit" disabled={loading}>
            {loading ? "생성 중..." : "프로젝트 생성"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function Sidebar() {
  const { projects, selectedProjectId, activeTab, selectProject, setActiveTab, guidemapGeneratingProjectIds } = useAppStore();
  const [showModal, setShowModal] = useState(false);

  function handleTabClick(tabId: ActiveTab) {
    if (!selectedProjectId && projects.length > 0) selectProject(projects[0].id);
    setActiveTab(tabId);
  }

  return (
    <aside className="app-sidebar">
      <div className="sidebar-section">
        <div className="sidebar-section-title">
          <span>프로젝트</span>
          <button onClick={() => setShowModal(true)} title="새 프로젝트"><Plus size={13} /></button>
        </div>
        <ul className="sidebar-list">
          {projects.map((p) => {
            const isGenerating = guidemapGeneratingProjectIds.has(p.id);
            return (
              <li key={p.id} className={"sidebar-item " + (p.id === selectedProjectId ? "active" : "")} onClick={() => selectProject(p.id)}>
                {isGenerating
                  ? <Loader2 size={14} style={{ flexShrink: 0 }} className="animate-spin" />
                  : <FolderOpen size={14} style={{ flexShrink: 0 }} />
                }
                <span>{p.name}</span>
                {isGenerating && <span style={{ fontSize: 11, opacity: 0.6, marginLeft: "auto" }}>가이드맵 생성 중</span>}
              </li>
            );
          })}
        </ul>
      </div>
      <div className="sidebar-section">
        <div className="sidebar-section-title"><span>메뉴</span></div>
        <ul className="sidebar-list">
          {TABS.map((tab, i) => (
            <li key={tab.id} className={"sidebar-item " + (activeTab === tab.id && selectedProjectId ? "active" : "")} onClick={() => handleTabClick(tab.id)}>
              <span style={{ flexShrink: 0, display: "flex" }}>{tab.icon}</span>
              <span>{i + 1}. {tab.label}</span>
            </li>
          ))}
        </ul>
      </div>

      {showModal && (
        <NewProjectModal
          onClose={() => setShowModal(false)}
          onCreated={(id) => selectProject(id)}
        />
      )}
    </aside>
  );
}
