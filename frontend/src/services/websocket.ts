import type { WsMessage } from '../types';

type MessageHandler = (msg: WsMessage) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private projectId: string = '';
  private handlers: MessageHandler[] = [];
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;

  connect(projectId: string) {
    this.projectId = projectId;
    this.shouldReconnect = true;
    this._open();
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }

  onMessage(handler: MessageHandler) {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter(h => h !== handler);
    };
  }

  send(msg: WsMessage) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  private _open() {
    const url = `ws://localhost:8000/ws/${this.projectId}`;
    const ws = new WebSocket(url);
    this.ws = ws;

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data);
        this.handlers.forEach(h => h(msg));
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (this.ws !== ws) return; // 이미 교체된 stale 커넥션이면 무시
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this._open(), 3000);
      }
    };
  }
}

export const wsClient = new WebSocketClient();
