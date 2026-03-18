import { useState, useRef, useEffect } from 'react';
import {
  FolderSearch,
  Send,
  FileCode2,
  MessageSquare,
  ChevronRight,
  ChevronLeft,
  Loader2,
  AlertCircle,
  Bot,
  User,
  Folder,
  FolderOpen,
  File as FileIcon,
} from 'lucide-react';
import { sendChat, listFiles, type FileNode } from '../../api/legacy/legacyApis';
import './LegacyAnalysis.css';

// ── Types ─────────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function nowStr() {
  return new Date().toLocaleTimeString('ko-KR', { hour12: false });
}

function uid() {
  return Math.random().toString(36).slice(2);
}

function resolvePath(filePath: string, codePath: string): string {
  if (/^[A-Za-z]:/.test(filePath) || filePath.startsWith('/')) return filePath;
  return `${codePath.replace(/[/\\]+$/, '')}/${filePath}`;
}

// ── MessageContent: 마크다운 렌더링 + 파일 경로 클릭 ─────────────────────────

function isFilePath(s: string): boolean {
  return /\.\w{1,10}$/.test(s);
}

function renderInline(
  text: string,
  keyPrefix: string,
  onOpenFile: (path: string, line?: number) => void,
): React.ReactNode {
  const segments: React.ReactNode[] = [];
  const re = /(\*\*[^*\n]+\*\*)|(`[^`\n]+`)/g;
  let last = 0;
  let match: RegExpExecArray | null;

  re.lastIndex = 0;
  while ((match = re.exec(text)) !== null) {
    if (match.index > last) segments.push(text.slice(last, match.index));
    const part = match[0];

    if (part.startsWith('**')) {
      segments.push(<strong key={`${keyPrefix}b${match.index}`}>{part.slice(2, -2)}</strong>);
    } else {
      const inner = part.slice(1, -1);
      const rangeMatch = inner.match(/^(.+?):(\d+)(?:-\d+)?$/);
      const filePath = rangeMatch ? rangeMatch[1] : inner;
      const line = rangeMatch ? parseInt(rangeMatch[2]) : undefined;

      if (isFilePath(filePath)) {
        segments.push(
          <button
            key={`${keyPrefix}f${match.index}`}
            className="msg-file-link"
            onClick={() => onOpenFile(filePath, line)}
            title={`파일 트리에서 보기: ${inner}`}
          >
            {part}
          </button>
        );
      } else {
        segments.push(<code key={`${keyPrefix}c${match.index}`} className="msg-inline-code">{inner}</code>);
      }
    }
    last = match.index + part.length;
  }
  if (last < text.length) segments.push(text.slice(last));
  return <>{segments}</>;
}

function MessageContent({
  content,
  onOpenFile,
}: {
  content: string;
  onOpenFile: (path: string, line?: number) => void;
}) {
  const lines = content.split('\n');

  return (
    <div className="msg-md">
      {lines.map((line, i) => {
        const k = String(i);

        const h4 = line.match(/^####\s*(.+)$/);
        if (h4) return <div key={k} className="msg-h4">{renderInline(h4[1], k, onOpenFile)}</div>;

        const h3 = line.match(/^###\s*(.+)$/);
        if (h3) return <div key={k} className="msg-h3">{renderInline(h3[1], k, onOpenFile)}</div>;

        const h2 = line.match(/^##\s*(.+)$/);
        if (h2) return <div key={k} className="msg-h2">{renderInline(h2[1], k, onOpenFile)}</div>;

        const h1 = line.match(/^#\s*(.+)$/);
        if (h1) return <div key={k} className="msg-h1">{renderInline(h1[1], k, onOpenFile)}</div>;

        const bullet = line.match(/^(\s*)[-*]\s+(.+)$/);
        if (bullet) return (
          <div key={k} className="msg-li" style={{ paddingLeft: `${bullet[1].length * 6 + 8}px` }}>
            <span className="msg-li-marker">·</span>
            {renderInline(bullet[2], k, onOpenFile)}
          </div>
        );

        const numbered = line.match(/^(\s*)(\d+)\.\s+(.+)$/);
        if (numbered) return (
          <div key={k} className="msg-li" style={{ paddingLeft: `${numbered[1].length * 6 + 8}px` }}>
            <span className="msg-li-marker">{numbered[2]}.</span>
            {renderInline(numbered[3], k, onOpenFile)}
          </div>
        );

        if (line.trim() === '') return <div key={k} className="msg-spacer" />;

        return <div key={k}>{renderInline(line, k, onOpenFile)}</div>;
      })}
    </div>
  );
}

// ── usePanelResize ────────────────────────────────────────────────────────────

function usePanelResize(initial: number, min: number, max: number) {
  const [width, setWidth] = useState(initial);
  const [dragging, setDragging] = useState(false);
  const dragRef = useRef<{ startX: number; startWidth: number; dir: 1 | -1 } | null>(null);

  useEffect(() => {
    function onMove(e: MouseEvent) {
      if (!dragRef.current) return;
      const { startX, startWidth, dir } = dragRef.current;
      setWidth(Math.max(min, Math.min(max, startWidth + (e.clientX - startX) * dir)));
    }
    function onUp() {
      if (dragRef.current) { dragRef.current = null; setDragging(false); }
    }
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    return () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };
  }, [min, max]);

  function startDrag(e: React.MouseEvent, dir: 1 | -1 = 1) {
    dragRef.current = { startX: e.clientX, startWidth: width, dir };
    setDragging(true);
    e.preventDefault();
  }

  return { width, dragging, startDrag };
}

// ── File Tree ─────────────────────────────────────────────────────────────────

function FileTreeNode({
  node, expanded, onToggle, selected, depth,
}: {
  node: FileNode;
  expanded: Set<string>;
  onToggle: (path: string) => void;
  selected: string | null;
  depth: number;
}) {
  const isDir = node.type === 'directory';
  const isOpen = expanded.has(node.path);
  const isSelected = selected === node.path;

  return (
    <div>
      <div
        className={`ft-node${isSelected ? ' ft-node--selected' : ''}`}
        style={{ paddingLeft: `${6 + depth * 14}px` }}
        onClick={() => isDir && onToggle(node.path)}
        title={node.name}
      >
        {isDir ? (
          <>
            <ChevronRight size={11} className={`ft-chevron${isOpen ? ' open' : ''}`} />
            {isOpen
              ? <FolderOpen size={13} className="ft-icon ft-icon--dir" />
              : <Folder size={13} className="ft-icon ft-icon--dir" />
            }
          </>
        ) : (
          <>
            <span className="ft-leaf-indent" />
            <FileIcon size={12} className={`ft-icon ft-icon--file${isSelected ? ' ft-icon--selected' : ''}`} />
          </>
        )}
        <span className="ft-name">{node.name}</span>
      </div>
      {isDir && isOpen && node.children?.map(child => (
        <FileTreeNode
          key={child.path}
          node={child}
          expanded={expanded}
          onToggle={onToggle}
          selected={selected}
          depth={depth + 1}
        />
      ))}
    </div>
  );
}

// ── Chat Panel ────────────────────────────────────────────────────────────────

function ChatPanel({
  messages, onSend, disabled, sending, onOpenFile,
}: {
  messages: ChatMessage[];
  onSend: (text: string) => void;
  disabled: boolean;
  sending: boolean;
  onOpenFile: (path: string, line?: number) => void;
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
            <p>경로를 입력하고 코드에 대해 질문하세요.</p>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`la-msg la-msg--${msg.role}`}>
            <div className="la-msg-avatar">
              {msg.role === 'user' ? <User size={13} /> : <Bot size={13} />}
            </div>
            <div className="la-msg-body">
              <div className="la-msg-content">
                {msg.role === 'assistant'
                  ? <MessageContent content={msg.content} onOpenFile={onOpenFile} />
                  : msg.content
                }
              </div>
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
          placeholder={disabled ? '경로를 먼저 입력하세요.' : '코드에 대해 질문하세요... (Enter 전송)'}
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

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function LegacyAnalysis() {
  const [codePath, setCodePath] = useState('');
  const [fileTree, setFileTree] = useState<FileNode | null>(null);
  const [treeLoading, setTreeLoading] = useState(false);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const treePanel = usePanelResize(220, 120, 480);
  const isResizing = treePanel.dragging;

  async function handleLoadTree(path: string) {
    if (!path.trim()) return;
    setTreeLoading(true);
    setFileTree(null);
    setSelectedFile(null);
    setExpandedNodes(new Set());
    setErrorMsg(null);

    const result = await listFiles(path);
    setTreeLoading(false);

    if (result.success && result.data) {
      const tree = result.data.tree;
      setFileTree(tree);
      setExpandedNodes(new Set([tree.path]));
    } else {
      setErrorMsg(result.error?.message ?? '디렉토리를 불러오지 못했습니다.');
    }
  }

  async function handlePickDirectory() {
    const path = await window.electronAPI?.openDirectory();
    if (path) {
      setCodePath(path);
      await handleLoadTree(path);
    }
  }

  function handleToggleNode(path: string) {
    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }

  /** 채팅 파일 링크 클릭 → 파일 트리에서 해당 파일 하이라이트 */
  function handleOpenFile(filePath: string) {
    const resolved = resolvePath(filePath, codePath).replace(/\\/g, '/');
    setSelectedFile(resolved);

    // 상위 폴더를 모두 펼쳐서 파일이 보이도록
    setExpandedNodes(prev => {
      const next = new Set(prev);
      const parts = resolved.split('/');
      for (let i = 1; i < parts.length; i++) {
        next.add(parts.slice(0, i).join('/'));
      }
      return next;
    });
  }

  async function handleChatSend(text: string) {
    const userMsg: ChatMessage = { id: uid(), role: 'user', content: text, timestamp: nowStr() };
    setMessages(prev => [...prev, userMsg]);
    setSending(true);

    const result = await sendChat(codePath, text, selectedFile);
    setSending(false);

    const replyContent = result.success && result.data
      ? result.data.answer
      : result.error?.message ?? '답변을 가져오지 못했습니다.';

    setMessages(prev => [...prev, {
      id: uid(),
      role: 'assistant',
      content: replyContent,
      timestamp: nowStr(),
    }]);
  }

  const treeColWidth = sidebarOpen ? treePanel.width : 32;
  const gridCols = `${treeColWidth}px 5px 1fr`;

  return (
    <div className={`la-root${isResizing ? ' la-root--resizing' : ''}`}>
      <div className="la-topbar">
        <div className="la-topbar-left">
          <FileCode2 size={16} style={{ color: 'var(--accent-hover)' }} />
          <h2>레거시 코드 분석</h2>
        </div>
        <div className="la-path-row">
          <div className="la-path-input-wrap">
            <input
              className="la-path-input"
              value={codePath}
              onChange={(e) => setCodePath(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleLoadTree(codePath); }}
              placeholder="코드 경로를 입력하고 Enter (예: C:/projects/legacy-app)"
            />
            <button className="la-path-browse" onClick={handlePickDirectory} title="폴더 선택">
              <FolderSearch size={15} />
            </button>
          </div>
        </div>
        {errorMsg && (
          <div className="la-error-bar">
            <AlertCircle size={13} />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      <div className="la-body" style={{ gridTemplateColumns: gridCols }}>

        {/* File Tree Panel */}
        <div className={`la-filetree-panel${sidebarOpen ? '' : ' la-filetree-panel--collapsed'}`}>
          <div className="la-panel-header" style={{ overflow: 'hidden' }}>
            {sidebarOpen && <><Folder size={13} /><span>파일 탐색기</span></>}
            {treeLoading && <Loader2 size={11} className="animate-spin" style={{ marginLeft: 'auto' }} />}
            <button
              className="la-sidebar-toggle"
              onClick={() => setSidebarOpen(v => !v)}
              title={sidebarOpen ? '사이드바 닫기' : '사이드바 열기'}
              style={{ marginLeft: sidebarOpen ? 'auto' : 0 }}
            >
              {sidebarOpen ? <ChevronLeft size={12} /> : <ChevronRight size={12} />}
            </button>
          </div>
          {sidebarOpen && (
            <div className="la-filetree-scroll">
              {!fileTree && !treeLoading && (
                <div className="la-empty" style={{ minHeight: 120, fontSize: 12 }}>
                  <Folder size={28} style={{ opacity: 0.15 }} />
                  <p>경로를 입력하고 Enter를 누르세요.</p>
                </div>
              )}
              {fileTree && (
                <div className="ft-root">
                  <FileTreeNode
                    node={fileTree}
                    expanded={expandedNodes}
                    onToggle={handleToggleNode}
                    selected={selectedFile}
                    depth={0}
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Drag Handle */}
        <div
          className="la-drag-handle"
          onMouseDown={(e) => sidebarOpen && treePanel.startDrag(e, 1)}
          style={{ cursor: sidebarOpen ? 'col-resize' : 'default' }}
        />

        {/* Chat Panel */}
        <div className="la-chat-panel">
          <ChatPanel
            messages={messages}
            onSend={handleChatSend}
            disabled={!codePath.trim()}
            sending={sending}
            onOpenFile={handleOpenFile}
          />
        </div>

      </div>
    </div>
  );
}
