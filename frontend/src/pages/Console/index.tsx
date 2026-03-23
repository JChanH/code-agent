import { useState, useRef, useEffect } from 'react';
import { Play, Square, Trash2, Info } from 'lucide-react';

interface Props { projectId: string; }

interface LogLine {
  time: string;
  level: string;
  msg: string;
}

const LEVEL_COLOR: Record<string, string> = {
  info: '#3b82f6',
  success: '#22c55e',
  warn: '#f59e0b',
  error: '#ef4444',
};

const LEVEL_LABEL: Record<string, string> = {
  info: 'INFO   ',
  success: 'OK     ',
  warn: 'WARN   ',
  error: 'ERROR  ',
};

export default function ConsolePage({ projectId: _projectId }: Props) {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [input, setInput] = useState('');
  const [running, setRunning] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  function handleRun() {
    if (!input.trim()) return;
    const now = new Date().toLocaleTimeString('ko-KR', { hour12: false });
    setLogs((prev) => [
      ...prev,
      { time: now, level: 'info', msg: `> ${input}` },
      { time: now, level: 'warn', msg: '직접 명령 실행 기능은 개발 예정입니다. Dev Phase에서 태스크를 실행하세요.' },
    ]);
    setInput('');
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleRun();
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h2>콘솔 (Claude CLI)</h2>
        <button
          className={running ? 'btn-secondary' : 'btn-primary'}
          onClick={() => setRunning((v) => !v)}
          style={{ marginLeft: 'auto' }}
        >
          {running ? <><Square size={13} /> 중단</> : <><Play size={13} /> 에이전트 실행</>}
        </button>
        <button className="icon-btn" title="로그 지우기" onClick={() => setLogs([])}>
          <Trash2 size={15} />
        </button>
      </div>

      <div className="console-notice">
        <Info size={13} />
        <span>에이전트 실행 로그는 하단 패널 <strong>로그</strong> 탭에서 실시간으로 확인할 수 있습니다. 직접 명령 실행 기능은 개발 예정입니다.</span>
      </div>

      <div className="console-output">
        {logs.map((log, i) => (
          <div key={i} style={{ display: 'flex', gap: 12, lineHeight: 1.6 }}>
            <span style={{ color: '#4b5563', flexShrink: 0 }}>{log.time}</span>
            <span style={{ color: LEVEL_COLOR[log.level] ?? '#6b7280', flexShrink: 0, minWidth: 60 }}>
              [{LEVEL_LABEL[log.level] ?? log.level}]
            </span>
            <span style={{ color: '#9ca3af' }}>{log.msg}</span>
          </div>
        ))}
        {running && (
          <div style={{ display: 'flex', gap: 12, lineHeight: 1.6 }}>
            <span style={{ color: '#4b5563' }}>
              {new Date().toLocaleTimeString('ko-KR', { hour12: false })}
            </span>
            <span style={{ color: '#6366f1' }} className="animate-pulse">에이전트 대기 중...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="console-input-row">
        <span className="console-prompt">$</span>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="에이전트에게 명령을 입력하세요 (Enter로 실행)"
        />
        <button className="btn-primary" onClick={handleRun} disabled={!input.trim()}>
          <Play size={13} /> 실행
        </button>
      </div>
    </div>
  );
}
