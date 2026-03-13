import { useEffect } from 'react';
import { wsClient } from '../services/websocket';
import { useTaskStore, useAppStore } from '../stores';

export function useWebSocket(projectId: string | null) {
  const handleTaskWsMessage = useTaskStore((s) => s.handleWsMessage);
  const handleAppWsMessage = useAppStore((s) => s.handleWsMessage);

  useEffect(() => {
    if (!projectId) return;

    wsClient.connect(projectId);
    const unsub1 = wsClient.onMessage(handleTaskWsMessage);
    const unsub2 = wsClient.onMessage(handleAppWsMessage);

    return () => {
      unsub1();
      unsub2();
      wsClient.disconnect();
    };
  }, [projectId]);
}
