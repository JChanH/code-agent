"""코드 에이전트 — Task를 구현하고 pytest 테스트를 작성합니다."""

from __future__ import annotations

import logging
from typing import Callable, Awaitable

from claude_agent_sdk import query, ClaudeAgentOptions

from app.models import Task, Project

logger = logging.getLogger(__name__)

Broadcaster = Callable[[dict], Awaitable[None]]


def _build_prompt(task: Task, project: Project, review_context: dict | None = None) -> str:
    criteria_text = ""
    if task.acceptance_criteria:
        criteria_list = "\n".join(f"  - {c}" for c in task.acceptance_criteria)
        criteria_text = f"\n## 수용 기준\n{criteria_list}\n"

    retry_section = ""
    if review_context:
        attempt = review_context.get("attempt", 1)
        retry_section = f"""
## ⚠️ 이전 리뷰 실패 결과 (시도 {attempt}회차) — 반드시 수정하세요

### 테스트 실행 결과
{review_context.get("test_output", "없음")}

### 수용 기준 검토
{review_context.get("overall_feedback", "없음")}
"""

    return f"""당신은 시니어 소프트웨어 엔지니어입니다.
아래 Task를 구현하고 pytest 테스트를 작성하세요.

## Task 정보
- 제목: {task.title}
- 설명: {task.description}
{criteria_text}
## 프로젝트 컨텍스트
- 이름: {project.name}
- 스택: {project.project_stack} / {project.framework or "미지정"}
- 로컬 경로: {project.local_repo_path}
{retry_section}
## 작업 순서
1. Glob, Read로 `{project.local_repo_path}` 의 기존 코드 구조 파악
2. 기존 패턴·네이밍 규칙에 맞춰 구현 코드 작성
3. `{project.local_repo_path}/tests/` 에 pytest 테스트 파일 작성
   - FastAPI 프로젝트라면 TestClient 사용
   - 각 수용 기준을 검증하는 테스트 케이스 포함
4. Bash로 pytest 실행하여 모든 테스트 통과 확인
   예: `cd {project.local_repo_path} && python -m pytest tests/ -v --tb=short`

## 규칙
- 기존 코드 스타일과 패턴을 따를 것
- 모든 pytest 테스트가 통과해야 작업 완료
- 테스트 파일명: `test_<구현파일명>.py`
"""


async def run_code_agent(
    task: Task,
    project: Project,
    review_context: dict | None = None,
    broadcast: Broadcaster | None = None,
) -> None:
    """
    Task를 구현하고 테스트를 작성합니다.

    :param task: 구현할 Task
    :param project: 프로젝트 정보 (local_repo_path 포함)
    :param review_context: 이전 리뷰 실패 결과 (재시도 시 주입)
    :param broadcast: WebSocket 브로드캐스트 콜백
    """
    prompt = _build_prompt(task, project, review_context)

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
        permission_mode="bypassPermissions",
        max_turns=50,
    )

    async for message in query(prompt=prompt, options=options):
        if broadcast:
            try:
                msg_data = message.model_dump() if hasattr(message, "model_dump") else str(message)
            except Exception:
                msg_data = str(message)
            await broadcast({
                "type": "agent_message",
                "task_id": task.id,
                "agent": "code",
                "message": msg_data,
            })
