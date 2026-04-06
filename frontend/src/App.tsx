import { useEffect, useRef, useState, lazy, Suspense } from 'react';
import { Bell, Settings, Code2, Trash2, Loader2, CheckCircle2, Sun, Moon } from 'lucide-react';
import ComingSoon from './components/common/ComingSoon';
import Sidebar from './components/common/Sidebar';
import { useAppStore, useTaskStore } from './stores';
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

// ── Agent Notification Popup ──────────────────────────────────────────────────

function AgentNotificationPopup({ onClose }: { onClose: () => void }) {
  const projects = useAppStore((s) => s.projects);
  const guidemapGeneratingProjectIds = useAppStore((s) => s.guidemapGeneratingProjectIds);
  const tasks = useTaskStore((s) => s.tasks);
  const analyzingSpecIds = useTaskStore((s) => s.analyzingSpecIds);

  const activeAgents: { key: string; label: string; sub: string }[] = [];

  // 가이드맵 생성 중
  guidemapGeneratingProjectIds.forEach((pid) => {
    const project = projects.find((p) => p.id === pid);
    activeAgents.push({
      key: `guidemap-${pid}`,
      label: '가이드맵 생성 중',
      sub: project?.name ?? `프로젝트 #${pid}`,
    });
  });

  // Spec 분석 중
  analyzingSpecIds.forEach((specId) => {
    activeAgents.push({
      key: `spec-${specId}`,
      label: 'Spec 분석 중',
      sub: `Spec #${specId}`,
    });
  });

  // 코딩 중인 Task (code agent)
  tasks
    .filter((t) => t.status === 'coding' || t.status === 'reviewing')
    .forEach((t) => {
      activeAgents.push({
        key: `task-${t.id}`,
        label: t.status === 'coding' ? '코딩 중' : '리뷰 중',
        sub: t.title.length > 36 ? t.title.slice(0, 36) + '…' : t.title,
      });
    });

  return (
    <>
      <div className="notif-backdrop" onClick={onClose} />
      <div className="notif-popup">
        <div className="notif-header">
          <span>진행 중인 Agent</span>
          {activeAgents.length > 0 && (
            <span className="notif-count-badge">{activeAgents.length}</span>
          )}
        </div>
        <div className="notif-body">
          {activeAgents.length === 0 ? (
            <div className="notif-empty">
              <CheckCircle2 size={20} style={{ color: 'var(--success)', opacity: 0.7 }} />
              <span>실행 중인 Agent가 없습니다</span>
            </div>
          ) : (
            <ul className="notif-list">
              {activeAgents.map((a) => (
                <li key={a.key} className="notif-item">
                  <Loader2 size={13} className="animate-spin notif-item-icon" />
                  <div className="notif-item-text">
                    <span className="notif-item-label">{a.label}</span>
                    <span className="notif-item-sub">{a.sub}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  );
}

// ── Header ────────────────────────────────────────────────────────────────────

function AppHeader() {
  const [notifOpen, setNotifOpen] = useState(false);

  const guidemapGeneratingProjectIds = useAppStore((s) => s.guidemapGeneratingProjectIds);
  const tasks = useTaskStore((s) => s.tasks);
  const analyzingSpecIds = useTaskStore((s) => s.analyzingSpecIds);
  const theme = useAppStore((s) => s.theme);
  const toggleTheme = useAppStore((s) => s.toggleTheme);

  const activeCount =
    guidemapGeneratingProjectIds.size +
    analyzingSpecIds.size +
    tasks.filter((t) => t.status === 'coding' || t.status === 'reviewing').length;

  return (
    <header className="app-header">
      <div className="header-logo">
        <Code2 size={20} />
        <span>Code Agent</span>
      </div>
      <div className="header-spacer" />
      <div style={{ position: 'relative' }}>
        <button
          className={`header-icon-btn${notifOpen ? ' active' : ''}`}
          title="알림"
          onClick={() => setNotifOpen((v) => !v)}
        >
          <Bell size={16} />
          {activeCount > 0 && (
            <span className="notif-badge">{activeCount}</span>
          )}
        </button>
        {notifOpen && <AgentNotificationPopup onClose={() => setNotifOpen(false)} />}
      </div>
      <button
        className="header-icon-btn"
        title={theme === 'dark' ? '라이트 모드로 전환' : '다크 모드로 전환'}
        onClick={toggleTheme}
      >
        {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
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
  const theme = useAppStore((s) => s.theme);

  // 초기 테마 적용
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

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
