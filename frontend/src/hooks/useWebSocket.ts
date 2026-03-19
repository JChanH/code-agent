import { useEffect } from 'react';
import { wsClient } from '../services/websocket';
import { useTaskStore, useAppStore } from '../stores';
import { useRuntimeErrorStore } from '../stores/runtimeErrorStore';

export function useWebSocket(projectId: string | null) {
  const handleTaskWsMessage = useTaskStore((s) => s.handleWsMessage);
  const handleAppWsMessage = useAppStore((s) => s.handleWsMessage);
  const handleRuntimeErrorWsMessage = useRuntimeErrorStore((s) => s.handleWsMessage);

  useEffect(() => {
    if (!projectId) return;

    wsClient.connect(projectId);
    const unsub1 = wsClient.onMessage(handleTaskWsMessage);
    const unsub2 = wsClient.onMessage(handleAppWsMessage);
    const unsub3 = wsClient.onMessage(handleRuntimeErrorWsMessage);

    return () => {
      unsub1();
      unsub2();
      unsub3();
      wsClient.disconnect();
    };
  }, [projectId]);
}
