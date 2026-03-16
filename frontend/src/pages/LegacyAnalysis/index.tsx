import { useState, useRef, useEffect, useCallback } from 'react';
import {
  FolderSearch,
  Play,
  Send,
  FileCode2,
  MessageSquare,
  ChevronRight,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Bot,
  User,
  Terminal,
} from 'lucide-react';
import { startAnalysis, sendChat, type AnalysisSection } from '../../api/legacy/legacyApis';
import { WebSocketClient } from '../../services/websocket';
import type { WsMessage } from '../../types';
import './LegacyAnalysis.css';

// ── Types ─────────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

type AnalysisStatus = 'idle' | 'analyzing' | 'done' | 'error';

// ── Helpers ───────────────────────────────────────────────────────────────────

function nowStr() {
  return new Date().toLocaleTimeString('ko-KR', { hour12: false });
}

function uid() {
  return Math.random().toString(36).slice(2);
}

function makeSessionId() {
  return `legacy-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

/** SDK agent_message에서 사람이 읽을 수 있는 한 줄 텍스트 추출 (stores/index.ts formatAgentMessage 동일 로직) */
function extractLogLine(raw: unknown): string | null {
  if (!raw || typeof raw !== 'object') return typeof raw === 'string' ? raw : null;
  const m = raw as Record<string, unknown>;

  // AssistantMessage: { role: "assistant", content: [...] }
  if (m.role === 'assistant' && Array.isArray(m.content)) {
    const parts: string[] = [];
    for (const block of m.content as Record<string, unknown>[]) {
      if (block.type === 'text' && typeof block.text === 'string') {
        const snippet = block.text.trim().split('\n')[0].slice(0, 100);
        if (snippet) parts.push(snippet);
      } else if (block.type === 'tool_use' && typeof block.name === 'string') {
        const input = block.input as Record<string, unknown> | undefined;
        const detail = input
          ? (Object.values(input).find((v) => typeof v === 'string') as string ?? '')
          : '';
        parts.push(`[${block.name}] ${detail}`);
      }
    }
    return parts.join(' | ') || null;
  }

  // ResultMessage: { result: "..." }
  if (typeof m.result === 'string' && m.result.length > 0) {
    return `완료: ${m.result.split('\n')[0].slice(0, 100)}`;
  }

  return null;
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: AnalysisStatus }) {
  if (status === 'idle') return null;
  if (status === 'analyzing')
    return (
      <span className="la-badge la-badge--analyzing">
        <Loader2 size={12} className="animate-spin" />
        분석 중
      </span>
    );
  if (status === 'done')
    return (
      <span className="la-badge la-badge--done">
        <CheckCircle2 size={12} />
        분석 완료
      </span>
    );
  return (
    <span className="la-badge la-badge--error">
      <AlertCircle size={12} />
      오류
    </span>
  );
}

function ProgressLog({ logs }: { logs: string[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="la-progress-log">
      <div className="la-progress-log-header">
        <Terminal size={12} />
        <span>에이전트 진행 상황</span>
        <Loader2 size={12} className="animate-spin" style={{ marginLeft: 'auto' }} />
      </div>
      <div className="la-progress-log-body">
        {logs.length === 0 && (
          <span className="la-progress-line la-progress-line--muted">에이전트 시작 중...</span>
        )}
        {logs.map((line, i) => (
          <div key={i} className="la-progress-line">{line}</div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

// ── Smart Content Renderer ────────────────────────────────────────────────────

const METHOD_COLORS: Record<string, string> = {
  get: '#22c55e',
  post: '#3b82f6',
  put: '#f59e0b',
  delete: '#ef4444',
  patch: '#a78bfa',
};

function SmartContent({ content }: { content: string }) {
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];

  lines.forEach((line, i) => {
    // 그룹 헤더: 【...】
    const groupMatch = line.match(/^【(.+)】$/);
    if (groupMatch) {
      elements.push(
        <div key={i} className="sc-group-header">{groupMatch[1]}</div>
      );
      return;
    }

    // HTTP 메서드 라인: "  GET   /path   - 설명"
    const methodMatch = line.match(/^\s+(GET|POST|PUT|DELETE|PATCH)\s+(\S+)\s+-\s*(.+)$/);
    if (methodMatch) {
      const [, method, path, desc] = methodMatch;
      const color = METHOD_COLORS[method.toLowerCase()] ?? '#6b7280';
      elements.push(
        <div key={i} className="sc-api-row">
          <span className="sc-method" style={{ color, borderColor: color }}>{method}</span>
          <code className="sc-path">{path}</code>
          <span className="sc-desc">{desc}</span>
        </div>
      );
      return;
    }

    // 번호 단계: "1. [레이어] 설명" 또는 "1. 설명"
    const stepMatch = line.match(/^(\d+)\.\s+(\[.+?\])?\s*(.+)$/);
    if (stepMatch) {
      const [, num, label, desc] = stepMatch;
      elements.push(
        <div key={i} className="sc-step">
          <span className="sc-step-num">{num}</span>
          <span className="sc-step-body">
            {label && <span className="sc-step-label">{label}</span>}
            {desc}
          </span>
        </div>
      );
      return;
    }

    // 들여쓰기 불릿/화살표: "  - " or "  → "
    const bulletMatch = line.match(/^\s{2,}[-→]\s+(.+)$/);
    if (bulletMatch) {
      elements.push(
        <div key={i} className="sc-bullet">· {bulletMatch[1]}</div>
      );
      return;
    }

    // 빈 줄
    if (line.trim() === '') {
      elements.push(<div key={i} className="sc-spacer" />);
      return;
    }

    // 기본 텍스트
    elements.push(<div key={i} className="sc-text">{line}</div>);
  });

  return <div className="sc-root">{elements}</div>;
}

// ── Analysis Result Panel ─────────────────────────────────────────────────────

function AnalysisResultPanel({
  sections,
  status,
  progressLogs,
}: {
  sections: AnalysisSection[];
  status: AnalysisStatus;
  progressLogs: string[];
}) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  function toggle(title: string) {
    setExpanded((prev) => ({ ...prev, [title]: !prev[title] }));
  }

  if (status === 'analyzing') {
    return <ProgressLog logs={progressLogs} />;
  }

  if (sections.length === 0) {
    return (
      <div className="la-empty">
        <FileCode2 size={36} style={{ opacity: 0.15 }} />
        <p>경로를 입력하고 분석을 시작하면 결과가 여기에 표시됩니다.</p>
      </div>
    );
  }

  return (
    <div className="la-sections">
      {sections.map((sec) => {
        const open = expanded[sec.title] !== false;
        return (
          <div key={sec.title} className="la-section">
            <button className="la-section-header" onClick={() => toggle(sec.title)}>
              <ChevronRight size={14} className={`la-chevron ${open ? 'open' : ''}`} />
              <span>{sec.title}</span>
            </button>
            {open && (
              <div className="la-section-body">
                <SmartContent content={sec.content} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function ChatPanel({
  messages,
  onSend,
  disabled,
  sending,
}: {
  messages: ChatMessage[];
  onSend: (text: string) => void;
  disabled: boolean;
  sending: boolean;
}) {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function handleSend() {
    const text = input.trim();
    if (!text || sending) return;
    onSend(text);
    setInput('');
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="la-chat">
      <div className="la-chat-header">
        <MessageSquare size={14} />
        <span>코드 Q&amp;A 채팅</span>
      </div>
      <div className="la-chat-messages">
        {messages.length === 0 && (
          <div className="la-chat-empty">
            <Bot size={28} style={{ opacity: 0.2 }} />
            <p>분석 후 코드에 대해 질문하세요.</p>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`la-msg la-msg--${msg.role}`}>
            <div className="la-msg-avatar">
              {msg.role === 'user' ? <User size={13} /> : <Bot size={13} />}
            </div>
            <div className="la-msg-body">
              <div className="la-msg-content">{msg.content}</div>
              <div className="la-msg-time">{msg.timestamp}</div>
            </div>
          </div>
        ))}
        {sending && (
          <div className="la-msg la-msg--assistant">
            <div className="la-msg-avatar"><Bot size={13} /></div>
            <div className="la-msg-body">
              <div className="la-msg-content" style={{ opacity: 0.5 }}>
                <Loader2 size={13} className="animate-spin" style={{ display: 'inline' }} /> 답변 생성 중...
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="la-chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder={disabled ? '분석이 완료된 후 질문할 수 있습니다.' : '코드에 대해 질문하세요... (Enter 전송)'}
          disabled={disabled || sending}
          rows={2}
        />
        <button
          className="la-send-btn"
          onClick={handleSend}
          disabled={disabled || sending || !input.trim()}
          title="전송"
        >
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function LegacyAnalysis() {
  const [codePath, setCodePath] = useState('');
  const [status, setStatus] = useState<AnalysisStatus>('idle');
  const [sections, setSections] = useState<AnalysisSection[]>([]);
  const [progressLogs, setProgressLogs] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const sessionIdRef = useRef<string>(makeSessionId());
  const wsRef = useRef<WebSocketClient | null>(null);

  const connectWs = useCallback((sessionId: string) => {
    if (wsRef.current) wsRef.current.disconnect();

    const ws = new WebSocketClient();
    ws.connect(sessionId);

    ws.onMessage((msg: WsMessage) => {
      // 백엔드 메시지는 flat 구조: { type, session_id, ...fields }
      const raw = msg as unknown as Record<string, unknown>;

      if (raw.type === 'agent_message') {
        const line = extractLogLine(raw.message);
        if (line) setProgressLogs((prev) => [...prev, line]);
      } else if (raw.type === 'legacy_analyzed') {
        const sections = (raw.sections as AnalysisSection[]) ?? [];
        setSections(sections);
        setStatus('done');
        setMessages([{
          id: uid(),
          role: 'assistant',
          content: '코드 분석이 완료되었습니다. 궁금한 점을 질문해 주세요.',
          timestamp: nowStr(),
        }]);
        ws.disconnect();
      } else if (raw.type === 'legacy_analyze_failed') {
        setErrorMsg((raw.error as string) ?? '분석 중 오류가 발생했습니다.');
        setStatus('error');
        ws.disconnect();
      }
    });

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    return () => { wsRef.current?.disconnect(); };
  }, []);

  async function handlePickDirectory() {
    const path = await window.electronAPI?.openDirectory();
    if (path) setCodePath(path);
  }

  async function handleAnalyze() {
    if (!codePath.trim() || status === 'analyzing') return;

    const sessionId = makeSessionId();
    sessionIdRef.current = sessionId;

    setStatus('analyzing');
    setSections([]);
    setProgressLogs([]);
    setMessages([]);
    setErrorMsg(null);

    connectWs(sessionId);

    const result = await startAnalysis(sessionId, codePath);
    if (!result.success) {
      setStatus('error');
      setErrorMsg(result.error?.message ?? '분석 요청에 실패했습니다.');
      wsRef.current?.disconnect();
    }
  }

  async function handleChatSend(text: string) {
    const userMsg: ChatMessage = { id: uid(), role: 'user', content: text, timestamp: nowStr() };
    setMessages((prev) => [...prev, userMsg]);
    setSending(true);

    const result = await sendChat(sessionIdRef.current, text);
    setSending(false);

    const replyContent = result.success && result.data
      ? result.data.answer
      : result.error?.message ?? '답변을 가져오지 못했습니다.';

    setMessages((prev) => [...prev, {
      id: uid(),
      role: 'assistant',
      content: replyContent,
      timestamp: nowStr(),
    }]);
  }

  return (
    <div className="la-root">
      <div className="la-topbar">
        <div className="la-topbar-left">
          <FileCode2 size={16} style={{ color: 'var(--accent-hover)' }} />
          <h2>레거시 코드 분석</h2>
          <StatusBadge status={status} />
        </div>
        <div className="la-path-row">
          <div className="la-path-input-wrap">
            <input
              className="la-path-input"
              value={codePath}
              onChange={(e) => setCodePath(e.target.value)}
              placeholder="분석할 코드 경로를 입력하세요 (예: C:/projects/legacy-app)"
            />
            <button className="la-path-browse" onClick={handlePickDirectory} title="폴더 선택">
              <FolderSearch size={15} />
            </button>
          </div>
          <button
            className="la-analyze-btn"
            onClick={handleAnalyze}
            disabled={!codePath.trim() || status === 'analyzing'}
          >
            {status === 'analyzing'
              ? <><Loader2 size={13} className="animate-spin" /> 분석 중...</>
              : <><Play size={13} /> 분석 시작</>
            }
          </button>
        </div>
        {errorMsg && (
          <div className="la-error-bar">
            <AlertCircle size={13} />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      <div className="la-body">
        <div className="la-result-panel">
          <div className="la-panel-header">
            <FileCode2 size={13} />
            <span>분석 결과</span>
          </div>
          <div className="la-result-scroll">
            <AnalysisResultPanel sections={sections} status={status} progressLogs={progressLogs} />
          </div>
        </div>

        <div className="la-chat-panel">
          <ChatPanel
            messages={messages}
            onSend={handleChatSend}
            disabled={status !== 'done'}
            sending={sending}
          />
        </div>
      </div>
    </div>
  );
}
