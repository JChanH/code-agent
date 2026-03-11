interface Props { projectId: string; }

export default function Settings({ projectId }: Props) {
  return (
    <div className="page-container">
      <div className="page-header">
        <h2>프로젝트 설정</h2>
      </div>
      <div className="settings-grid">
        <div className="settings-card">
          <h3>기본 정보</h3>
          <div className="settings-row">
            <span className="settings-label">프로젝트 ID</span>
            <span className="settings-value">{projectId}</span>
          </div>
          <div className="settings-row">
            <span className="settings-label">스택</span>
            <span className="settings-value">Python / FastAPI</span>
          </div>
          <div className="settings-row">
            <span className="settings-label">메인 브랜치</span>
            <span className="settings-value">main</span>
          </div>
          <div className="settings-row">
            <span className="settings-label">상태</span>
            <span className="settings-value">developing</span>
          </div>
        </div>
        <div className="settings-card">
          <h3>에이전트 설정</h3>
          <div className="settings-row">
            <span className="settings-label">자동 승인</span>
            <span className="settings-value">비활성화</span>
          </div>
          <div className="settings-row">
            <span className="settings-label">Worktree 전략</span>
            <span className="settings-value">사용자별</span>
          </div>
          <div className="settings-row">
            <span className="settings-label">Permission Mode</span>
            <span className="settings-value">default</span>
          </div>
          <div className="settings-row">
            <span className="settings-label">모델</span>
            <span className="settings-value">claude-sonnet-4-6</span>
          </div>
        </div>
      </div>
      <p className="text-muted" style={{ marginTop: 24, fontSize: 13 }}>
        상세 설정은 Phase 2에서 구현 예정입니다.
      </p>
    </div>
  );
}
