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

  handleWsMessage: (msg) => {
    if (msg.type === 'runtime_error') {
      const data = (msg as unknown as { type: string; data: RuntimeError }).data;
      set((s) => ({
        errors: [data, ...s.errors],
        totalCount: s.totalCount + 1,
      }));
      useAppStore.getState().addLog('error', `[런타임 에러] ${data.error_code}: ${data.message}`);
      return;
    }

    if (msg.type === 'runtime_error_update') {
      const data = msg.data as { id: string; status: RuntimeErrorStatus; fix_suggestion: string };
      set((s) => ({
        errors: s.errors.map((e) =>
          e.id === data.id
            ? { ...e, status: data.status, fix_suggestion: data.fix_suggestion }
            : e,
        ),
      }));
      return;
    }

    if (msg.type === 'runtime_error_agent_message') {
      const data = msg.data as { error_id: string; message: string };
      useAppStore.getState().addLog('info', `[런타임 분석] ${data.message}`);
      return;
    }
  },
}));
