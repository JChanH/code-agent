import { useEffect, useState } from 'react';
import { FolderGit2, Plus, Settings, Code2, GitBranch, LayoutDashboard, ChevronDown } from 'lucide-react';
import { useAppStore, useProjectStore, useUserStore } from './stores';
import type { Project, User } from './types';

/* ══════════════════════════════════════
   Tab content placeholder components
   (will be replaced in Phase 1–3)
   ══════════════════════════════════════ */

function DesignPhase() {
  return (
    <div className="flex items-center justify-center h-full text-zinc-500">
      <div className="text-center">
        <LayoutDashboard className="w-12 h-12 mx-auto mb-3 opacity-40" />
        <p className="text-lg font-medium">설계 단계 Kanban</p>
        <p className="text-sm mt-1">Phase 2에서 구현 예정</p>
      </div>
    </div>
  );
}

function DevPhase() {
  return (
    <div className="flex items-center justify-center h-full text-zinc-500">
      <div className="text-center">
        <Code2 className="w-12 h-12 mx-auto mb-3 opacity-40" />
        <p className="text-lg font-medium">개발 단계 Kanban</p>
        <p className="text-sm mt-1">Phase 1에서 구현 예정</p>
      </div>
    </div>
  );
}

function GitManagement() {
  return (
    <div className="flex items-center justify-center h-full text-zinc-500">
      <div className="text-center">
        <GitBranch className="w-12 h-12 mx-auto mb-3 opacity-40" />
        <p className="text-lg font-medium">Git 관리</p>
        <p className="text-sm mt-1">Phase 1에서 구현 예정</p>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════
   Main App
   ══════════════════════════════════════ */

const TABS = [
  { id: 'design' as const, label: '설계', icon: LayoutDashboard },
  { id: 'dev' as const, label: '개발', icon: Code2 },
  { id: 'git' as const, label: 'Git 관리', icon: GitBranch },
];

export default function App() {
  const {
    currentProject, setCurrentProject,
    currentUser, setCurrentUser,
    activeTab, setActiveTab,
  } = useAppStore();

  const { projects, fetchProjects } = useProjectStore();
  const { users, fetchUsers } = useUserStore();

  const [backendStatus, setBackendStatus] = useState<'checking' | 'ok' | 'error'>('checking');

  // Check backend health on mount
  useEffect(() => {
    fetch('/api/projects')
      .then((res) => {
        setBackendStatus(res.ok ? 'ok' : 'error');
      })
      .catch(() => setBackendStatus('error'));
  }, []);

  // Load initial data
  useEffect(() => {
    if (backendStatus === 'ok') {
      fetchProjects();
      fetchUsers();
    }
  }, [backendStatus, fetchProjects, fetchUsers]);

  // Auto-select first project/user
  useEffect(() => {
    if (!currentProject && projects.length > 0) {
      setCurrentProject(projects[0]);
    }
  }, [projects, currentProject, setCurrentProject]);

  useEffect(() => {
    if (!currentUser && users.length > 0) {
      setCurrentUser(users[0]);
    }
  }, [users, currentUser, setCurrentUser]);

  return (
    <div className="h-screen flex flex-col bg-zinc-950 text-zinc-100">
      {/* ── Top Bar ──────────────────────── */}
      <header className="flex items-center justify-between h-12 px-4 border-b border-zinc-800 bg-zinc-900 shrink-0">
        <div className="flex items-center gap-3">
          <FolderGit2 className="w-5 h-5 text-blue-400" />
          <span className="font-semibold text-sm">Code Agent</span>

          {/* Project selector */}
          <div className="relative ml-4">
            <select
              className="appearance-none bg-zinc-800 text-sm rounded px-3 py-1.5 pr-7 border border-zinc-700 focus:outline-none focus:border-blue-500"
              value={currentProject?.id ?? ''}
              onChange={(e) => {
                const p = projects.find((p) => p.id === e.target.value);
                setCurrentProject(p ?? null);
              }}
            >
              <option value="" disabled>프로젝트 선택</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* User selector */}
          <select
            className="appearance-none bg-zinc-800 text-sm rounded px-3 py-1.5 border border-zinc-700 focus:outline-none focus:border-blue-500"
            value={currentUser?.id ?? ''}
            onChange={(e) => {
              const u = users.find((u) => u.id === e.target.value);
              setCurrentUser(u ?? null);
            }}
          >
            <option value="" disabled>사용자 선택</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.display_name || u.username}
              </option>
            ))}
          </select>

          {/* Backend status indicator */}
          <div className="flex items-center gap-1.5 text-xs">
            <div className={`w-2 h-2 rounded-full ${
              backendStatus === 'ok' ? 'bg-green-500' :
              backendStatus === 'error' ? 'bg-red-500' :
              'bg-yellow-500 animate-pulse'
            }`} />
            <span className="text-zinc-500">Backend</span>
          </div>

          <button className="p-1.5 rounded hover:bg-zinc-800 transition">
            <Settings className="w-4 h-4 text-zinc-400" />
          </button>
        </div>
      </header>

      {/* ── Main Layout ──────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar — Project list */}
        <aside className="w-56 border-r border-zinc-800 bg-zinc-900 flex flex-col shrink-0">
          <div className="p-3 border-b border-zinc-800">
            <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">프로젝트</h2>
          </div>
          <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => setCurrentProject(p)}
                className={`w-full text-left px-3 py-2 rounded text-sm transition ${
                  currentProject?.id === p.id
                    ? 'bg-blue-500/20 text-blue-300'
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                }`}
              >
                <div className="font-medium truncate">{p.name}</div>
                <div className="text-xs text-zinc-600 mt-0.5">
                  {p.project_stack} · {p.status}
                </div>
              </button>
            ))}
          </nav>
          <div className="p-2 border-t border-zinc-800">
            <button className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded text-sm text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition">
              <Plus className="w-4 h-4" />
              새 프로젝트
            </button>
          </div>
        </aside>

        {/* Content area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-zinc-800 bg-zinc-900 shrink-0">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition border-b-2 ${
                    isActive
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-zinc-500 hover:text-zinc-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-auto">
            {!currentProject ? (
              <div className="flex items-center justify-center h-full text-zinc-600">
                프로젝트를 선택하거나 새로 만들어주세요
              </div>
            ) : (
              <>
                {activeTab === 'design' && <DesignPhase />}
                {activeTab === 'dev' && <DevPhase />}
                {activeTab === 'git' && <GitManagement />}
              </>
            )}
          </div>

          {/* Bottom panel — Logs (placeholder) */}
          <div className="h-40 border-t border-zinc-800 bg-zinc-900 p-3 shrink-0 overflow-auto">
            <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">로그</div>
            <div className="text-xs text-zinc-600 font-mono">
              {backendStatus === 'ok'
                ? `[System] Backend connected. ${projects.length} project(s), ${users.length} user(s) loaded.`
                : backendStatus === 'error'
                ? '[System] Backend connection failed. Check if the server is running on port 8000.'
                : '[System] Checking backend connection...'}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
