interface Props {
  projectId: string;
}

export default function Settings({ projectId: _projectId }: Props) {
  return (
    <div className="page-container">
      <div className="page-header">
        <h2>설정</h2>
      </div>
      <p className="text-muted">Phase 2에서 구현 예정입니다.</p>
    </div>
  );
}
