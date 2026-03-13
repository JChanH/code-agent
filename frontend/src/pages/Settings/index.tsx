import { useAppStore } from '../../stores';
import { generateGuidemap } from '../../api/project/projectApis';

interface Props { projectId: string; }

export default function Settings({ projectId }: Props) {
  const projects = useAppStore((s) => s.projects);
  const guidemapGeneratingProjectIds = useAppStore((s) => s.guidemapGeneratingProjectIds);
  const project = projects.find((p) => p.id === projectId);
  const isExisting = project?.project_type === 'existing';
  const isGenerating = guidemapGeneratingProjectIds.has(projectId);

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
      {isExisting && (
        <div className="settings-card" style={{ marginTop: 16 }}>
          <h3>가이드맵</h3>
          <p className="text-muted" style={{ fontSize: 13, marginBottom: 12 }}>
            코드베이스를 분석하여 가이드맵 파일을 생성합니다.
            생성된 가이드맵은 Design Agent가 Spec 분석 시 참조하여 토큰 사용량을 줄입니다.
          </p>
          <button
            className="modal-submit"
            disabled={isGenerating}
            onClick={() => generateGuidemap(projectId)}
          >
            {isGenerating ? '생성 중...' : '가이드맵 재생성'}
          </button>
        </div>
      )}
      <p className="text-muted" style={{ marginTop: 24, fontSize: 13 }}>
        상세 설정은 Phase 2에서 구현 예정입니다.
      </p>
    </div>
  );
}
