import { create } from 'zustand';
import type {
  ActiveTab,
  Project,
  Spec,
  SpecStatus,
  Task,
  TaskStatus,
  WsMessage,
  WsSpecAnalyzed,
} from '../types';

// ── App Store ─────────────────────────────────────────────────────────────────

// MVP: 단일 사용자 고정
export const CURRENT_USER_ID = '1';

interface AppState {
  projects: Project[];
  selectedProjectId: string | null;
  activeTab: ActiveTab;

  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  selectProject: (id: string | null) => void;
  setActiveTab: (tab: ActiveTab) => void;
}

// 전역에서 관리하는 상태값(싱글톤 -> 외부 컴포넌트에서든 같은 인스턴스를 유지한다)
// 상태가 바뀌면 해당 상태를 구독중인 컴포넌트만 자동 리렌더링
export const useAppStore = create<AppState>((set) => ({
  projects: [], // 전체 프로젝트 목록
  selectedProjectId: null, // 현재 선택된 프로젝트 ID
  activeTab: 'design', // 현재 활성된 탭

  setProjects: (projects) => set({ projects }),
  addProject: (project) => set((s) => ({ projects: [...s.projects, project] })),
  selectProject: (id) => set({ selectedProjectId: id, activeTab: 'dashboard' }),
  setActiveTab: (tab) => set({ activeTab: tab }),
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
    switch (msg.type) {
      case 'task_update': {
        const data = msg as unknown as { task_id: string; status: TaskStatus };
        set((s) => ({
          tasks: s.tasks.map((t) =>
            t.id === data.task_id ? { ...t, status: data.status } : t
          ),
        }));
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
            specs: s.specs.map((sp) =>
              sp.id === data.spec_id ? { ...sp, status: 'analyzed' as SpecStatus } : sp
            ),
            tasks: [...s.tasks, ...newTasks],
          };
        });
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
        break;
      }
    }
  },
}));
