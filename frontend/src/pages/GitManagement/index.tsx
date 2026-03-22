import ComingSoon from '../../components/common/ComingSoon';

interface Props { projectId: string; }

export default function GitManagement({ projectId: _projectId }: Props) {
  return (
    <ComingSoon
      title="Git 관리"
      description="워크트리 기반 변경 파일 스테이징, 커밋, Pull/Push 및 이력 확인 기능입니다. 백엔드 API와 프론트엔드 API 클라이언트는 구현 완료되어 있으며, UI 연동이 진행될 예정입니다."
      details={[
        '변경 파일 목록 및 스테이징',
        '커밋 / Pull / Push 작업',
        '커밋 이력 및 Diff 뷰어',
        '파일 되돌리기',
      ]}
    />
  );
}
