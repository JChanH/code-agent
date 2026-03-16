import { useState, useRef, useEffect } from 'react';
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
} from 'lucide-react';
import './LegacyAnalysis.css';

// ── Types ────────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface AnalysisSection {
  title: string;
  content: string;
}

type AnalysisStatus = 'idle' | 'analyzing' | 'done' | 'error';

// ── Helpers ──────────────────────────────────────────────────────────────────

function now() {
  return new Date().toLocaleTimeString('ko-KR', { hour12: false });
}

function uid() {
  return Math.random().toString(36).slice(2);
}

// ── Sub-components ───────────────────────────────────────────────────────────

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

function AnalysisResultPanel({ sections }: { sections: AnalysisSection[] }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  function toggle(title: string) {
    setExpanded((prev) => ({ ...prev, [title]: !prev[title] }));
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
        const open = expanded[sec.title] !== false; // default open
        return (
          <div key={sec.title} className="la-section">
            <button className="la-section-header" onClick={() => toggle(sec.title)}>
              <ChevronRight size={14} className={`la-chevron ${open ? 'open' : ''}`} />
              <span>{sec.title}</span>
            </button>
            {open && (
              <div className="la-section-body">
                <pre>{sec.content}</pre>
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
}: {
  messages: ChatMessage[];
  onSend: (text: string) => void;
  disabled: boolean;
}) {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function handleSend() {
    const text = input.trim();
    if (!text) return;
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
        <div ref={bottomRef} />
      </div>
      <div className="la-chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder={disabled ? '분석이 완료된 후 질문할 수 있습니다.' : '코드에 대해 질문하세요... (Enter 전송)'}
          disabled={disabled}
          rows={2}
        />
        <button
          className="la-send-btn"
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          title="전송"
        >
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}

// ── Mock analysis helper (UI 데모용) ─────────────────────────────────────────

function buildMockSections(path: string): AnalysisSection[] {
  return [
    {
      title: '📁 프로젝트 개요',
      content: `분석 경로: ${path}\n\n이 코드베이스는 레거시 시스템으로, 여러 모듈로 구성되어 있습니다.\n언어 및 프레임워크를 자동으로 감지하여 분석 결과를 제공합니다.`,
    },
    {
      title: '🏗️ 아키텍처 분석',
      content: `레이어 구조:\n  • Presentation Layer (UI / Controller)\n  • Business Logic Layer (Service / Domain)\n  • Data Access Layer (Repository / DAO)\n\n의존성 방향: 상위 → 하위 레이어 단방향 의존`,
    },
    {
      title: '⚠️ 코드 품질 이슈',
      content: `발견된 주요 이슈:\n  1. 순환 의존성 3건\n  2. God Object 패턴 2개 파일\n  3. 하드코딩된 설정값 (DB, API URL 등)\n  4. 테스트 커버리지 낮음 (~12%)\n  5. 미사용 코드(Dead Code) 다수`,
    },
    {
      title: '🔄 리팩토링 제안',
      content: `우선순위 높음:\n  → 설정 분리: config 파일 또는 환경변수로 이동\n  → 의존성 주입(DI) 패턴 도입\n  → 공통 유틸 메서드 추출\n\n우선순위 중간:\n  → 서비스 레이어 분리\n  → 인터페이스/추상화 도입\n  → 단위 테스트 추가`,
    },
    {
      title: '📊 파일 통계',
      content: `총 파일 수: 142개\nLOC (총 라인 수): 18,432\n\n언어 분포:\n  Python   62%  ██████████████████░░\n  SQL      18%  █████░░░░░░░░░░░░░░░\n  Shell     8%  ██░░░░░░░░░░░░░░░░░░\n  기타     12%  ███░░░░░░░░░░░░░░░░░`,
    },
  ];
}

function buildMockReply(question: string): string {
  const q = question.toLowerCase();
  if (q.includes('아키텍처') || q.includes('구조'))
    return '이 코드베이스는 MVC 패턴 기반으로 구성되어 있으나 레이어 간 결합도가 높습니다. Service 레이어가 직접 DB를 호출하는 경우가 많아 Repository 패턴 도입을 권장합니다.';
  if (q.includes('테스트') || q.includes('test'))
    return '현재 테스트 커버리지는 약 12%로 매우 낮습니다. 핵심 비즈니스 로직부터 단위 테스트를 작성하고, CI/CD에 테스트 실행 단계를 추가하는 것을 권장합니다.';
  if (q.includes('의존성') || q.includes('순환'))
    return '순환 의존성 3건이 발견되었습니다. ModuleA → ModuleB → ModuleC → ModuleA 형태의 의존 고리가 있습니다. 공통 인터페이스를 추출하거나 이벤트 기반 통신으로 해소할 수 있습니다.';
  return `"${question}"에 대한 분석 결과:\n\n분석된 코드베이스를 기반으로 답변드립니다. 실제 구현에서는 Claude API를 통해 코드 컨텍스트와 함께 질문을 처리하여 더 정확한 답변을 제공할 수 있습니다.`;
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function LegacyAnalysis() {
  const [codePath, setCodePath] = useState('');
  const [status, setStatus] = useState<AnalysisStatus>('idle');
  const [sections, setSections] = useState<AnalysisSection[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  async function handlePickDirectory() {
    const path = await window.electronAPI?.openDirectory();
    if (path) setCodePath(path);
  }

  async function handleAnalyze() {
    if (!codePath.trim()) return;
    setStatus('analyzing');
    setSections([]);
    setMessages([]);

    // TODO: replace with real API call
    await new Promise((r) => setTimeout(r, 1800));
    setSections(buildMockSections(codePath));
    setStatus('done');
    setMessages([
      {
        id: uid(),
        role: 'assistant',
        content: `${codePath} 경로의 코드 분석이 완료되었습니다. 코드에 대해 궁금한 점을 질문해 주세요.`,
        timestamp: now(),
      },
    ]);
  }

  function handleChatSend(text: string) {
    const userMsg: ChatMessage = { id: uid(), role: 'user', content: text, timestamp: now() };
    setMessages((prev) => [...prev, userMsg]);

    // TODO: replace with real API call
    setTimeout(() => {
      const reply: ChatMessage = {
        id: uid(),
        role: 'assistant',
        content: buildMockReply(text),
        timestamp: now(),
      };
      setMessages((prev) => [...prev, reply]);
    }, 700);
  }

  return (
    <div className="la-root">
      {/* ── Top bar ── */}
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
            <button
              className="la-path-browse"
              onClick={handlePickDirectory}
              title="폴더 선택"
            >
              <FolderSearch size={15} />
            </button>
          </div>
          <button
            className="la-analyze-btn"
            onClick={handleAnalyze}
            disabled={!codePath.trim() || status === 'analyzing'}
          >
            {status === 'analyzing' ? (
              <><Loader2 size={13} className="animate-spin" /> 분석 중...</>
            ) : (
              <><Play size={13} /> 분석 시작</>
            )}
          </button>
        </div>
      </div>

      {/* ── Body: analysis | chat ── */}
      <div className="la-body">
        {/* Analysis result */}
        <div className="la-result-panel">
          <div className="la-panel-header">
            <FileCode2 size={13} />
            <span>분석 결과</span>
          </div>
          <div className="la-result-scroll">
            {status === 'analyzing' ? (
              <div className="la-empty">
                <Loader2 size={32} className="animate-spin" style={{ opacity: 0.3 }} />
                <p>코드를 분석하는 중입니다...</p>
              </div>
            ) : (
              <AnalysisResultPanel sections={sections} />
            )}
          </div>
        </div>

        {/* Chat panel */}
        <div className="la-chat-panel">
          <ChatPanel
            messages={messages}
            onSend={handleChatSend}
            disabled={status !== 'done'}
          />
        </div>
      </div>
    </div>
  );
}
