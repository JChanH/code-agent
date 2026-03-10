/* ──────────────────────────────────────
   Zustand stores for application state
   ────────────────────────────────────── */

import { create } from 'zustand';
import type { Project, User, Task } from '../types';
import { projectsApi, usersApi, tasksApi } from '../services/api';

// ── App Store (global) ───────────────
interface AppStore {
  currentUser: User | null;
  currentProject: Project | null;
  activeTab: 'design' | 'dev' | 'git';
  setCurrentUser: (user: User | null) => void;
  setCurrentProject: (project: Project | null) => void;
  setActiveTab: (tab: 'design' | 'dev' | 'git') => void;
}

export const useAppStore = create<AppStore>((set) => ({
  currentUser: null,
  currentProject: null,
  activeTab: 'dev',
  setCurrentUser: (user) => set({ currentUser: user }),
  setCurrentProject: (project) => set({ currentProject: project }),
  setActiveTab: (tab) => set({ activeTab: tab }),
}));

// ── Projects Store ───────────────────
interface ProjectStore {
  projects: Project[];
  loading: boolean;
  error: string | null;
  fetchProjects: () => Promise<void>;
  createProject: (data: Partial<Project>) => Promise<Project>;
  deleteProject: (id: string) => Promise<void>;
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  projects: [],
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true, error: null });
    try {
      const projects = await projectsApi.list();
      set({ projects, loading: false });
    } catch (e: any) {
      set({ error: e.message, loading: false });
    }
  },

  createProject: async (data) => {
    const project = await projectsApi.create(data);
    set({ projects: [project, ...get().projects] });
    return project;
  },

  deleteProject: async (id) => {
    await projectsApi.delete(id);
    set({ projects: get().projects.filter((p) => p.id !== id) });
  },
}));

// ── Users Store ──────────────────────
interface UserStore {
  users: User[];
  fetchUsers: () => Promise<void>;
  createUser: (data: { username: string; display_name?: string }) => Promise<User>;
}

export const useUserStore = create<UserStore>((set, get) => ({
  users: [],

  fetchUsers: async () => {
    const users = await usersApi.list();
    set({ users });
  },

  createUser: async (data) => {
    const user = await usersApi.create(data);
    set({ users: [...get().users, user] });
    return user;
  },
}));

// ── Tasks Store ──────────────────────
interface TaskStore {
  tasks: Task[];
  selectedTask: Task | null;
  loading: boolean;
  fetchTasks: (projectId: string, userId?: string) => Promise<void>;
  updateTaskStatus: (taskId: string, status: Task['status']) => Promise<void>;
  selectTask: (task: Task | null) => void;
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  selectedTask: null,
  loading: false,

  fetchTasks: async (projectId, userId) => {
    set({ loading: true });
    try {
      const tasks = await tasksApi.list({
        project_id: projectId,
        assigned_user_id: userId,
      });
      set({ tasks, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  updateTaskStatus: async (taskId, status) => {
    await tasksApi.update(taskId, { status });
    set({
      tasks: get().tasks.map((t) =>
        t.id === taskId ? { ...t, status } : t
      ),
    });
  },

  selectTask: (task) => set({ selectedTask: task }),
}));
