import { useEffect } from 'react';
import { wsClient } from '../services/websocket';
import { useTaskStore } from '../stores';

export function useWebSocket(projectId: string | null) {
  const handleWsMessage = useTaskStore((s) => s.handleWsMessage);

  useEffect(() => {
    if (!projectId) return;

    wsClient.connect(projectId);
    const unsubscribe = wsClient.onMessage(handleWsMessage);

    return () => {
      unsubscribe();
      wsClient.disconnect();
    };
  }, [projectId]);
}
