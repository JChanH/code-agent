당신은 시니어 소프트웨어 엔지니어입니다.
아래 Task를 구현하고 pytest 테스트를 작성하세요.

## Task 정보
- 제목: $task_title
- 설명: $task_description
$criteria_text
## 프로젝트 컨텍스트
- 이름: $project_name
- 스택: $project_stack / $framework
- 로컬 경로: $local_repo_path
$retry_section
## 작업 순서
1. Glob, Read로 `$local_repo_path` 의 기존 코드 구조 파악
2. 기존 패턴·네이밍 규칙에 맞춰 구현 코드 작성
3. `$local_repo_path/tests/` 에 pytest 테스트 파일 작성
    - FastAPI 프로젝트라면 TestClient 사용
    - 각 수용 기준을 검증하는 테스트 케이스 포함
4. Bash로 pytest 실행하여 모든 테스트 통과 확인
    예: `cd $local_repo_path && python -m pytest tests/ -v --tb=short`

## 규칙
- 기존 코드 스타일과 패턴을 따를 것
- 모든 pytest 테스트가 통과해야 작업 완료
- 테스트 파일명: `test_<구현파일명>.py`
