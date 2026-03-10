import { create } from 'zustand';
import type { ActiveTab, Project, Spec, Task, TaskStatus, User, WsMessage } from '../types';

// ── App Store ─────────────────────────────────────────────────────────────────

interface AppState {
  projects: Project[];
  selectedProjectId: string | null;
  users: User[];
  selectedUserId: string | null;
  activeTab: ActiveTab;

  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  selectProject: (id: string | null) => void;
  setUsers: (users: User[]) => void;
  selectUser: (id: string | null) => void;
  setActiveTab: (tab: ActiveTab) => void;
}

export const useAppStore = create<AppState>((set) => ({
  projects: [],
  selectedProjectId: null,
  users: [],
  selectedUserId: null,
  activeTab: 'design',

  setProjects: (projects) => set({ projects }),
  addProject: (project) => set((s) => ({ projects: [...s.projects, project] })),
  selectProject: (id) => set({ selectedProjectId: id }),
  setUsers: (users) => set({ users }),
  selectUser: (id) => set({ selectedUserId: id }),
  setActiveTab: (tab) => set({ activeTab: tab }),
}));

// ── Task Store ────────────────────────────────────────────────────────────────

interface TaskState {
  tasks: Task[];
  specs: Spec[];

  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, patch: Partial<Task>) => void;
  setSpecs: (specs: Spec[]) => void;
  addSpec: (spec: Spec) => void;
  removeSpec: (specId: string) => void;

  handleWsMessage: (msg: WsMessage) => void;
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: [],
  specs: [],

  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((s) => ({ tasks: [...s.tasks, task] })),
  updateTask: (taskId, patch) =>
    set((s) => ({
      tasks: s.tasks.map((t) => (t.id === taskId ? { ...t, ...patch } : t)),
    })),
  setSpecs: (specs) => set({ specs }),
  addSpec: (spec) => set((s) => ({ specs: [...s.specs, spec] })),
  removeSpec: (specId) => set((s) => ({ specs: s.specs.filter((sp) => sp.id !== specId) })),

  handleWsMessage: (msg) => {
    if (msg.type === 'task_update') {
      const data = msg.data as { task_id: string; status: TaskStatus; progress?: number };
      set((s) => ({
        tasks: s.tasks.map((t) =>
          t.id === data.task_id ? { ...t, status: data.status } : t
        ),
      }));
    }
  },
}));
