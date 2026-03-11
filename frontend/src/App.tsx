import { useEffect, useState, lazy, Suspense } from 'react';
import { Bell, Settings, Code2 } from 'lucide-react';
import Sidebar from './components/common/Sidebar';
import { useAppStore, useTaskStore } from './stores';
import { MOCK_PROJECTS, MOCK_USERS, MOCK_TASKS, MOCK_LOGS } from './mock/data';
import './App.css';

const DesignPhase = lazy(() => import('./pages/DesignPhase'));
const DevPhase = lazy(() => import('./pages/DevPhase'));
const GitManagement = lazy(() => import('./pages/GitManagement'));
const ConsolePage = lazy(() => import('./pages/Console'));
const SettingsPage = lazy(() => import('./pages/Settings'));

// ── Header ────────────────────────────────────────────────────────────────────

function AppHeader() {
  const { users, selectedUserId } = useAppStore();
  const user = users.find((u) => u.id === selectedUserId) ?? users[0];
  const name = user?.display_name ?? user?.username ?? 'User';
  const initial = (name[0] ?? 'U').toUpperCase();

  return (
    <header className="app-header">
      <div className="header-logo">
        <Code2 size={20} />
        <span>Code Agent</span>
      </div>
      <div className="header-spacer" />
      <div className="header-user">
        <span>사용자: {name}</span>
        <div className="header-avatar">{initial}</div>
      </div>
      <button className="header-icon-btn" title="알림">
        <Bell size={16} />
      </button>
      <button className="header-icon-btn" title="설정">
        <Settings size={16} />
      </button>
    </header>
  );
}

// ── Bottom Panel ──────────────────────────────────────────────────────────────

const BOTTOM_TABS = ['로그', '실행 결과', 'Git 상태'] as const;
type BottomTab = (typeof BOTTOM_TABS)[number];

const LEVEL_CLASS: Record<string, string> = {
  info: 'log-info',
  success: 'log-success',
  warn: 'log-warn',
  error: 'log-error',
};

const LEVEL_LABEL: Record<string, string> = {
  info: '[INFO]   ',
  success: '[OK]     ',
  warn: '[WARN]   ',
  error: '[ERROR]  ',
};

function BottomPanel() {
  const [activeTab, setActiveTab] = useState<BottomTab>('로그');

  return (
    <div className="app-bottom">
      <div className="bottom-tabs">
        {BOTTOM_TABS.map((tab) => (
          <button
            key={tab}
            className={`bottom-tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="bottom-content">
        {activeTab === '로그' &&
          MOCK_LOGS.map((log, i) => (
            <div key={i} className="log-entry">
              <span className="log-time">{log.time}</span>
              <span className={LEVEL_CLASS[log.level]}>{LEVEL_LABEL[log.level]}</span>
              <span className="log-msg">{log.msg}</span>
            </div>
          ))}
        {activeTab === '실행 결과' && (
          <div className="log-msg">마지막 에이전트 실행 결과가 여기에 표시됩니다.</div>
        )}
        {activeTab === 'Git 상태' && (
          <div className="log-msg">현재 워크트리 Git 상태가 여기에 표시됩니다.</div>
        )}
      </div>
    </div>
  );
}

// ── Main Content ──────────────────────────────────────────────────────────────

function MainContent() {
  const { selectedProjectId, activeTab } = useAppStore();

  if (!selectedProjectId) {
    return (
      <div className="empty-state">
        <Code2 size={40} style={{ opacity: 0.15 }} />
        <p>좌측에서 프로젝트를 선택하거나 새로 만드세요.</p>
      </div>
    );
  }

  return (
    <Suspense fallback={<div className="loading">로딩 중...</div>}>
      {activeTab === 'design' && <DesignPhase projectId={selectedProjectId} />}
      {activeTab === 'dev' && <DevPhase projectId={selectedProjectId} />}
      {activeTab === 'console' && <ConsolePage projectId={selectedProjectId} />}
      {activeTab === 'git' && <GitManagement projectId={selectedProjectId} />}
      {activeTab === 'settings' && <SettingsPage projectId={selectedProjectId} />}
    </Suspense>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  const { setProjects, setUsers, selectProject, selectUser } = useAppStore();
  const { setTasks } = useTaskStore();

  useEffect(() => {
    setProjects(MOCK_PROJECTS);
    setUsers(MOCK_USERS);
    setTasks(MOCK_TASKS);
    selectProject(MOCK_PROJECTS[0].id);
    selectUser(MOCK_USERS[0].id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="app-shell">
      <AppHeader />
      <Sidebar />
      <main className="app-main">
        <MainContent />
      </main>
      <BottomPanel />
    </div>
  );
}
