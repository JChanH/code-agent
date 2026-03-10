import { lazy, Suspense } from 'react';
import Sidebar from './components/common/Sidebar';
import { useAppStore } from './stores';
import { useWebSocket } from './hooks/useWebSocket';
import './App.css';

const DesignPhase = lazy(() => import('./pages/DesignPhase'));
const DevPhase = lazy(() => import('./pages/DevPhase'));
const GitManagement = lazy(() => import('./pages/GitManagement'));
const Settings = lazy(() => import('./pages/Settings'));

function MainContent() {
  const { selectedProjectId, activeTab } = useAppStore();

  if (!selectedProjectId) {
    return (
      <div className="empty-state">
        <p>좌측에서 프로젝트를 선택하거나 새로 만드세요.</p>
      </div>
    );
  }

  return (
    <Suspense fallback={<div className="loading">로딩 중...</div>}>
      {activeTab === 'design' && <DesignPhase projectId={selectedProjectId} />}
      {activeTab === 'dev' && <DevPhase projectId={selectedProjectId} />}
      {activeTab === 'git' && <GitManagement projectId={selectedProjectId} />}
      {activeTab === 'settings' && <Settings projectId={selectedProjectId} />}
    </Suspense>
  );
}

export default function App() {
  const selectedProjectId = useAppStore((s) => s.selectedProjectId);
  useWebSocket(selectedProjectId);

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <MainContent />
      </main>
    </div>
  );
}
