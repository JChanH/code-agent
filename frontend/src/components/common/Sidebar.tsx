import { useState } from "react";
import { FolderOpen, GitBranch, Layers, Settings, Plus, Code2, Terminal } from "lucide-react";
import { useAppStore } from "../../stores";
import type { ActiveTab } from "../../types";

const TABS: { id: ActiveTab; label: string; icon: React.ReactNode }[] = [
  { id: "design", label: "설계 Kanban", icon: <Layers size={14} /> },
  { id: "dev", label: "개발 Kanban", icon: <Code2 size={14} /> },
  { id: "console", label: "콘솔", icon: <Terminal size={14} /> },
  { id: "git", label: "Git 관리", icon: <GitBranch size={14} /> },
  { id: "settings", label: "프로젝트 설정", icon: <Settings size={14} /> },
];

export default function Sidebar() {
  const { projects, selectedProjectId, activeTab, selectProject, setActiveTab, addProject } = useAppStore();
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");

  function handleCreateProject() {
    if (!newProjectName.trim()) return;
    const now = new Date().toISOString();
    addProject({ id: 'p-' + Date.now(), name: newProjectName.trim(), description: null, repo_url: null, main_branch: "main", project_stack: "python", framework: null, status: "setup", created_at: now, updated_at: now });
    setNewProjectName("");
    setShowNewProject(false);
  }

  function handleTabClick(tabId: ActiveTab) {
    if (!selectedProjectId && projects.length > 0) selectProject(projects[0].id);
    setActiveTab(tabId);
  }

  return (
    <aside className="app-sidebar">
      <div className="sidebar-section">
        <div className="sidebar-section-title">
          <span>프로젝트</span>
          <button onClick={() => setShowNewProject((v) => !v)} title="새 프로젝트"><Plus size={13} /></button>
        </div>
        {showNewProject && (
          <div className="sidebar-new-form">
            <input autoFocus value={newProjectName} onChange={(e) => setNewProjectName(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleCreateProject(); if (e.key === "Escape") setShowNewProject(false); }}
              placeholder="프로젝트 이름" />
          </div>
        )}
        <ul className="sidebar-list">
          {projects.map((p) => (
            <li key={p.id} className={"sidebar-item " + (p.id === selectedProjectId ? "active" : "")} onClick={() => selectProject(p.id)}>
              <FolderOpen size={14} style={{ flexShrink: 0 }} />
              <span>{p.name}</span>
            </li>
          ))}
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
    </aside>
  );
}