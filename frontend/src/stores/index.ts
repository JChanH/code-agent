import { create } from 'zustand';
import type {
  ActiveTab,
  LogEntry,
  LogLevel,
  Project,
  Spec,
  SpecStatus,
  Task,
  TaskStatus,
  WsMessage,
  WsSpecAnalyzed,
} from '../types';

// ── Helpers ───────────────────────────────────────────────────────────────────

function nowTime(): string {
  return new Date().toTimeString().slice(0, 8);
}

function makeLogId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

/** Extract a human-readable line from a raw Claude agent SDK message dump */
function formatAgentMessage(raw: unknown): { level: LogLevel; msg: string } {
  if (!raw || typeof raw !== 'object') {
    return { level: 'info', msg: String(raw).slice(0, 120) };
  }
  const m = raw as Record<string, unknown>;

  // AssistantMessage: { role: "assistant", content: [...] }
  if (m.role === 'assistant' && Array.isArray(m.content)) {
    const parts: string[] = [];
    for (const block of m.content as Record<string, unknown>[]) {
      if (block.type === 'text' && typeof block.text === 'string') {
        const snippet = block.text.trim().slice(0, 100);
        if (snippet) parts.push(snippet);
      } else if (block.type === 'tool_use' && typeof block.name === 'string') {
        const input = block.input ? JSON.stringify(block.input).slice(0, 60) : '';
        parts.push(`[${block.name}] ${input}`);
      }
    }
    return { level: 'info', msg: parts.join(' | ') || '(assistant)' };
  }

  // ResultMessage: { result: "...", stop_reason: "..." }
  if (typeof m.result === 'string') {
    return { level: 'success', msg: `결과: ${m.result.slice(0, 100)}` };
  }

  // Fallback: show message type if available
  if (typeof m.type === 'string') {
    return { level: 'info', msg: `[${m.type}]` };
  }

  return { level: 'info', msg: JSON.stringify(raw).slice(0, 120) };
}

// ── App Store ─────────────────────────────────────────────────────────────────

// MVP: 단일 사용자 고정
export const CURRENT_USER_ID = '1';

interface AppState {
  projects: Project[];
  selectedProjectId: string | null;
  activeTab: ActiveTab;
  guidemapGeneratingProjectIds: Set<string>;
  logs: LogEntry[];

  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  selectProject: (id: string | null) => void;
  setActiveTab: (tab: ActiveTab) => void;
  addGuidemapGenerating: (projectId: string) => void;
  addLog: (level: LogLevel, msg: string) => void;
  clearLogs: () => void;
  handleWsMessage: (msg: WsMessage) => void;
}

// 전역에서 관리하는 상태값(싱글톤 -> 외부 컴포넌트에서든 같은 인스턴스를 유지한다)
// 상태가 바뀌면 해당 상태를 구독중인 컴포넌트만 자동 리렌더링
export const useAppStore = create<AppState>((set) => ({
  projects: [], // 전체 프로젝트 목록
  selectedProjectId: null, // 현재 선택된 프로젝트 ID
  activeTab: 'design', // 현재 활성된 탭
  guidemapGeneratingProjectIds: new Set(),
  logs: [],

  setProjects: (projects) => set({ projects }),
  addProject: (project) => set((s) => ({ projects: [...s.projects, project] })),
  selectProject: (id) => set({ selectedProjectId: id, activeTab: 'dashboard' }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  addGuidemapGenerating: (projectId) =>
    set((s) => {
      const next = new Set(s.guidemapGeneratingProjectIds);
      next.add(projectId);
      return { guidemapGeneratingProjectIds: next };
    }),

  addLog: (level, msg) =>
    set((s) => ({
      logs: [
        ...s.logs,
        { id: makeLogId(), time: nowTime(), level, msg },
      ],
    })),

  clearLogs: () => set({ logs: [] }),

  handleWsMessage: (msg) => {
    switch (msg.type) {
      case 'guidemap_generating': {
        const data = msg as unknown as { project_id: string };
        set((s) => {
          const next = new Set(s.guidemapGeneratingProjectIds);
          next.add(data.project_id);
          return { guidemapGeneratingProjectIds: next };
        });
        useAppStore.getState().addLog('info', '가이드맵 생성 시작...');
        break;
      }
      case 'guidemap_generated': {
        const data = msg as unknown as { project_id: string };
        set((s) => {
          const next = new Set(s.guidemapGeneratingProjectIds);
          next.delete(data.project_id);
          return { guidemapGeneratingProjectIds: next };
        });
        useAppStore.getState().addLog('success', '가이드맵 생성 완료');
        break;
      }
      case 'guidemap_failed': {
        const data = msg as unknown as { project_id: string; error?: string };
        set((s) => {
          const next = new Set(s.guidemapGeneratingProjectIds);
          next.delete(data.project_id);
          return { guidemapGeneratingProjectIds: next };
        });
        useAppStore.getState().addLog('error', `가이드맵 생성 실패${data.error ? ': ' + data.error : ''}`);
        break;
      }
    }
  },
}));

// ── Task Store ────────────────────────────────────────────────────────────────

interface TaskState {
  tasks: Task[];
  specs: Spec[];
  // spec_id → 분석 진행 메시지 (분석 중 표시용)
  analyzingSpecIds: Set<string>;

  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, patch: Partial<Task>) => void;
  setSpecs: (specs: Spec[]) => void;
  addSpec: (spec: Spec) => void;
  updateSpec: (specId: string, patch: Partial<Spec>) => void;
  removeSpec: (specId: string) => void;

  handleWsMessage: (msg: WsMessage) => void;
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: [],
  specs: [],
  analyzingSpecIds: new Set(),

  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((s) => ({ tasks: [...s.tasks, task] })),
  updateTask: (taskId, patch) =>
    set((s) => ({
      tasks: s.tasks.map((t) => (t.id === taskId ? { ...t, ...patch } : t)),
    })),
  setSpecs: (specs) => set({ specs }),
  addSpec: (spec) => set((s) => ({ specs: [...s.specs, spec] })),
  updateSpec: (specId, patch) =>
    set((s) => ({
      specs: s.specs.map((sp) => (sp.id === specId ? { ...sp, ...patch } : sp)),
    })),
  removeSpec: (specId) => set((s) => ({ specs: s.specs.filter((sp) => sp.id !== specId) })),

  handleWsMessage: (msg) => {
    const addLog = useAppStore.getState().addLog;

    switch (msg.type) {
      case 'task_update': {
        const data = msg as unknown as { task_id: string; status: TaskStatus; message?: string };
        set((s) => ({
          tasks: s.tasks.map((t) =>
            t.id === data.task_id ? { ...t, status: data.status } : t
          ),
        }));
        const level: LogLevel = data.status === 'done' ? 'success' : data.status === 'failed' ? 'error' : 'info';
        addLog(level, `Task #${data.task_id} 상태 변경: ${data.status}${data.message ? ' — ' + data.message : ''}`);
        break;
      }

      case 'spec_analyzing': {
        const data = msg as unknown as { spec_id: string };
        set((s) => {
          const next = new Set(s.analyzingSpecIds);
          next.add(data.spec_id);
          return {
            analyzingSpecIds: next,
            specs: s.specs.map((sp) =>
              sp.id === data.spec_id ? { ...sp, status: 'analyzing' as SpecStatus } : sp
            ),
          };
        });
        addLog('info', `Spec #${(msg as unknown as { spec_id: string }).spec_id} 분석 시작...`);
        break;
      }

      case 'spec_analyzed': {
        const data = msg as unknown as WsSpecAnalyzed;
        set((s) => {
          const next = new Set(s.analyzingSpecIds);
          next.delete(data.spec_id);
          // 새로 생성된 Task들 스토어에 추가
          const existingIds = new Set(s.tasks.map((t) => t.id));
          const newTasks = data.tasks.filter((t) => !existingIds.has(t.id)) as unknown as Task[];
          return {
            analyzingSpecIds: next,
            // 분석 완료 후 spec은 'uploaded'로 복귀 (kanban column 1에서 사라짐)
            specs: s.specs.map((sp) =>
              sp.id === data.spec_id ? { ...sp, status: 'uploaded' as SpecStatus } : sp
            ),
            tasks: [...s.tasks, ...newTasks],
          };
        });
        addLog('success', `Spec 분석 완료 — ${data.tasks.length}개 태스크 생성${data.analysis_summary ? ': ' + data.analysis_summary.slice(0, 80) : ''}`);
        break;
      }

      case 'spec_analyze_failed': {
        const data = msg as unknown as { spec_id: string; error: string };
        set((s) => {
          const next = new Set(s.analyzingSpecIds);
          next.delete(data.spec_id);
          return {
            analyzingSpecIds: next,
            specs: s.specs.map((sp) =>
              sp.id === data.spec_id ? { ...sp, status: 'uploaded' as SpecStatus } : sp
            ),
          };
        });
        addLog('error', `Spec 분석 실패: ${data.error}`);
        break;
      }

      case 'agent_message': {
        const data = msg as unknown as { spec_id: string; message: unknown };
        const { level, msg: text } = formatAgentMessage(data.message);
        if (text) addLog(level, text);
        break;
      }
    }
  },
}));
