import { useEffect, useState } from 'react';
import { FolderOpen, GitBranch, Layers, Settings, Plus, Code2 } from 'lucide-react';
import { projectsApi, usersApi } from '../../services/api';
import { useAppStore } from '../../stores';
import type { ActiveTab } from '../../types';

const TABS: { id: ActiveTab; label: string; icon: React.ReactNode }[] = [
  { id: 'design', label: '설계', icon: <Layers size={16} /> },
  { id: 'dev', label: '개발', icon: <Code2 size={16} /> },
  { id: 'git', label: 'Git 관리', icon: <GitBranch size={16} /> },
  { id: 'settings', label: '설정', icon: <Settings size={16} /> },
];

export default function Sidebar() {
  const { projects, selectedProjectId, users, selectedUserId, activeTab, setProjects, setUsers, selectProject, selectUser, setActiveTab } =
    useAppStore();
  const [newProjectName, setNewProjectName] = useState('');
  const [showNewProject, setShowNewProject] = useState(false);

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(console.error);
    usersApi.list().then(setUsers).catch(console.error);
  }, [setProjects, setUsers]);

  async function handleCreateProject() {
    if (!newProjectName.trim()) return;
    const project = await projectsApi.create({ name: newProjectName.trim() });
    setProjects([...projects, project]);
    selectProject(project.id);
    setNewProjectName('');
    setShowNewProject(false);
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <Code2 size={20} />
        <span>Code Agent</span>
      </div>

      {/* Projects */}
      <div className="sidebar-section">
        <div className="sidebar-section-header">
          <span>프로젝트</span>
          <button onClick={() => setShowNewProject(true)} title="새 프로젝트">
            <Plus size={14} />
          </button>
        </div>

        {showNewProject && (
          <div className="new-project-form">
            <input
              autoFocus
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleCreateProject();
                if (e.key === 'Escape') setShowNewProject(false);
              }}
              placeholder="프로젝트 이름"
            />
          </div>
        )}

        <ul className="project-list">
          {projects.map((p) => (
            <li
              key={p.id}
              className={`project-item ${p.id === selectedProjectId ? 'active' : ''}`}
              onClick={() => selectProject(p.id)}
            >
              <FolderOpen size={14} />
              <span>{p.name}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Tabs */}
      {selectedProjectId && (
        <div className="sidebar-section">
          <div className="sidebar-section-header">
            <span>메뉴</span>
          </div>
          <ul className="tab-list">
            {TABS.map((tab) => (
              <li
                key={tab.id}
                className={`tab-item ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* User selector */}
      {selectedProjectId && users.length > 0 && (
        <div className="sidebar-section sidebar-user">
          <div className="sidebar-section-header">
            <span>사용자</span>
          </div>
          <select
            value={selectedUserId ?? ''}
            onChange={(e) => selectUser(e.target.value || null)}
          >
            <option value="">전체</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.display_name ?? u.username}
              </option>
            ))}
          </select>
        </div>
      )}
    </aside>
  );
}
