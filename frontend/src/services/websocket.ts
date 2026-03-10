/* ──────────────────────────────────────
   WebSocket client for real-time agent updates
   ────────────────────────────────────── */

type MessageHandler = (msg: Record<string, unknown>) => void;

export class AgentWebSocket {
  private ws: WebSocket | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private projectId: string = '';

  connect(projectId: string): void {
    this.projectId = projectId;
    this.disconnect();

    const wsUrl = `ws://localhost:8000/ws/${projectId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log(`[WS] Connected to project ${projectId}`);
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const type = msg.type as string;
        // Call type-specific handlers
        this.handlers.get(type)?.forEach((h) => h(msg));
        // Call wildcard handlers
        this.handlers.get('*')?.forEach((h) => h(msg));
      } catch {
        console.warn('[WS] Failed to parse message:', event.data);
      }
    };

    this.ws.onclose = () => {
      console.log('[WS] Disconnected, reconnecting in 3s...');
      this.reconnectTimer = setTimeout(() => this.connect(this.projectId), 3000);
    };

    this.ws.onerror = (err) => {
      console.error('[WS] Error:', err);
    };
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  on(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, []);
    }
    this.handlers.get(type)!.push(handler);

    // Return unsubscribe function
    return () => {
      const list = this.handlers.get(type);
      if (list) {
        this.handlers.set(type, list.filter((h) => h !== handler));
      }
    };
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const agentWs = new AgentWebSocket();
