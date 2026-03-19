import { create } from 'zustand';
import type { RuntimeError, RuntimeErrorStatus, WsMessage } from '../types';
import { useAppStore } from './index';

interface RuntimeErrorState {
  errors: RuntimeError[];
  totalCount: number;
  isLoading: boolean;

  setErrors: (errors: RuntimeError[], total: number) => void;
  prependError: (error: RuntimeError) => void;
  setLoading: (loading: boolean) => void;
  clearErrors: () => void;
  updateErrorStatus: (errorId: string, status: RuntimeErrorStatus) => void;
  updateErrorSourcePath: (errorId: string, sourcePath: string) => void;

  handleWsMessage: (msg: WsMessage) => void;
}

export const useRuntimeErrorStore = create<RuntimeErrorState>((set) => ({
  errors: [],
  totalCount: 0,
  isLoading: false,

  setErrors: (errors, total) => set({ errors, totalCount: total }),
  prependError: (error) =>
    set((s) => ({ errors: [error, ...s.errors], totalCount: s.totalCount + 1 })),
  setLoading: (isLoading) => set({ isLoading }),
  clearErrors: () => set({ errors: [], totalCount: 0 }),
  updateErrorStatus: (errorId, status) =>
    set((s) => ({
      errors: s.errors.map((e) => (e.id === errorId ? { ...e, status } : e)),
    })),
  updateErrorSourcePath: (errorId, sourcePath) =>
    set((s) => ({
      errors: s.errors.map((e) => (e.id === errorId ? { ...e, source_path: sourcePath } : e)),
    })),

  handleWsMessage: (msg) => {
    if (msg.type !== 'runtime_error') return;
    const data = (msg as unknown as { type: string; data: RuntimeError }).data;
    set((s) => ({
      errors: [data, ...s.errors],
      totalCount: s.totalCount + 1,
    }));
    useAppStore.getState().addLog('error', `[런타임 에러] ${data.error_code}: ${data.message}`);
  },
}));
