import { useEffect, useRef, useState, lazy, Suspense } from 'react';
import { Bell, Settings, Code2, Trash2 } from 'lucide-react';
import ComingSoon from './components/common/ComingSoon';
import Sidebar from './components/common/Sidebar';
import { useAppStore, CURRENT_USER_ID } from './stores';
import { useWebSocket } from './hooks/useWebSocket';
import { getProjects } from './api/project/projectApis';
import './App.css';

const DesignPhase = lazy(() => import('./pages/DesignPhase'));
const DevPhase = lazy(() => import('./pages/DevPhase'));
const GitManagement = lazy(() => import('./pages/GitManagement'));
const ConsolePage = lazy(() => import('./pages/Console'));
const SettingsPage = lazy(() => import('./pages/Settings'));
const LegacyAnalysis = lazy(() => import('./pages/LegacyAnalysis'));
const RuntimeErrors = lazy(() => import('./pages/RuntimeErrors'));

// ── Header ────────────────────────────────────────────────────────────────────

function AppHeader() {
  const initial = (CURRENT_USER_ID[0] ?? 'U').toUpperCase();

  return (
    <header className="app-header">
      <div className="header-logo">
        <Code2 size={20} />
        <span>Code Agent</span>
      </div>
      <div className="header-spacer" />
      <div className="header-user">
        <span>사용자: {CURRENT_USER_ID}</span>
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
  const logs = useAppStore((s) => s.logs);
  const clearLogs = useAppStore((s) => s.clearLogs);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (activeTab === '로그') {
      logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, activeTab]);

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
        {activeTab === '로그' && logs.length > 0 && (
          <button
            className="bottom-tab"
            title="로그 지우기"
            onClick={clearLogs}
            style={{ marginLeft: 'auto', opacity: 0.6 }}
          >
            <Trash2 size={13} />
          </button>
        )}
      </div>
      <div className="bottom-content">
        {activeTab === '로그' && (
          logs.length === 0 ? (
            <div className="log-msg" style={{ opacity: 0.4 }}>WebSocket 메시지를 기다리는 중...</div>
          ) : (
            <>
              {logs.map((log) => (
                <div key={log.id} className="log-entry">
                  <span className="log-time">{log.time}</span>
                  <span className={LEVEL_CLASS[log.level]}>{LEVEL_LABEL[log.level]}</span>
                  <span className="log-msg">{log.msg}</span>
                </div>
              ))}
              <div ref={logEndRef} />
            </>
          )
        )}
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
  const { selectedProjectId, activeTab, projects } = useAppStore();
  const selectedProject = projects.find((p) => p.id === selectedProjectId);
  useWebSocket(selectedProject?.id ?? null);

  // Project-independent pages
  if (activeTab === 'legacy') {
    return (
      <Suspense fallback={<div className="loading">로딩 중...</div>}>
        <LegacyAnalysis />
      </Suspense>
    );
  }

  if (activeTab === 'runtime_errors') {
    return (
      <Suspense fallback={<div className="loading">로딩 중...</div>}>
        <RuntimeErrors />
      </Suspense>
    );
  }

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
      {activeTab === 'dashboard' && (
        <ComingSoon
          title="대시보드"
          description="프로젝트 진행 현황, 태스크 통계, 에이전트 활동 이력을 한눈에 확인하는 대시보드입니다."
          details={[
            '태스크 상태별 현황 차트',
            '에이전트 실행 이력 타임라인',
            '프로젝트별 진행률 요약',
          ]}
        />
      )}
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
  const { setProjects, selectProject } = useAppStore();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // 프로젝트 조회
  useEffect(() => {
    getProjects().then((result) => {
      if (result.success && result.data) {
        setProjects(result.data);
        if (result.data.length > 0) selectProject(result.data[0].id);
      }
    });
  }, []);

  return (
    <div
      className="app-shell"
      style={{ gridTemplateColumns: sidebarOpen ? 'var(--sidebar-w) 1fr' : '40px 1fr' }}
    >
      <AppHeader />
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(v => !v)} />
      <main className="app-main">
        <MainContent />
      </main>
      <BottomPanel />
    </div>
  );
}
