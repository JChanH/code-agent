"""설계 에이전트 — Spec을 분석하여 Task 목록으로 분해합니다."""

from __future__ import annotations

import json
import logging
from typing import Any

from claude_agent_sdk import query, ClaudeAgentOptions

from app.models import Spec, Project, Task
from app.repositories import spec_repository, project_repository
from app.websocket import ws_manager
from app.utils.db_handler_sqlalchemy import db_conn

logger = logging.getLogger(__name__)

# Structured Output — 설계 에이전트가 반환해야 하는 JSON 스키마
TASK_LIST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "analysis_summary": {
            "type": "string",
            "description": "스펙 전체에 대한 분석 요약",
        },
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "acceptance_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "complexity": {
                        "type": "string",
                        "enum": ["trivial", "low", "medium", "high", "very_high"],
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "의존하는 다른 Task의 title 목록",
                    },
                },
                "required": [
                    "title",
                    "description",
                    "acceptance_criteria",
                    "priority",
                    "complexity",
                ],
            },
        },
    },
    "required": ["analysis_summary", "tasks"],
}


def _get_stack_context(project: Project) -> str:
    """프로젝트 스택에 맞는 추가 컨텍스트를 반환합니다."""
    if project.project_stack == "python" and project.framework == "fastapi":
        return (
            "- FastAPI 프로젝트 구조를 따릅니다\n"
            "- 라우터는 app/api/ 하위에 배치\n"
            "- 모델은 app/models/, 스키마는 app/schemas/\n"
            "- 비즈니스 로직은 app/services/\n"
        )
    if project.project_stack == "java":
        return (
            "- 기존 사내 프레임워크 위에서 작업합니다\n"
            "- 기존 패키지 구조와 명명 규칙을 따르세요\n"
            "- 먼저 프로젝트 구조를 파악한 후 Task를 설계하세요"
        )
    return ""


def _build_prompt(spec_content: str, project: Project) -> str:
    stack_context = _get_stack_context(project)

    codebase_section = ""
    if project.local_repo_path:
        codebase_section = f"""
            ## 코드베이스 탐색 (필수)
            로컬 경로: `{project.local_repo_path}`
            Task 설계 전에 반드시 아래 절차를 따르세요:
            1. Glob 툴로 전체 파일 구조 파악 (예: `{project.local_repo_path}/**/*.py`)
            2. 핵심 파일(모델, 라우터, 서비스 등) Read로 확인
            3. 기존 패턴/네이밍 규칙을 Task 설계에 반영
            4. 이미 구현된 기능은 Task에서 제외하거나 수정 Task로만 포함
        """

    return f"""당신은 소프트웨어 설계 전문가입니다.
        아래 스펙 문서를 분석하여 개발 Task 목록으로 분해해주세요.

        ## 프로젝트 컨텍스트
        - 이름: {project.name}
        - 스택: {project.project_stack} / {project.framework or "미지정"}
        - 저장소: {project.repo_url or "미설정"}
        {stack_context}
        {codebase_section}
        ## Spec 내용
        {spec_content}

        ## 규칙
        1. 각 Task는 1-4시간 내 완료 가능한 단위로 분해
        2. Task 간 의존성을 명확히 기술
        3. acceptance_criteria는 검증 가능한 구체적 조건으로 작성
        4. 기존 코드베이스 구조를 먼저 파악한 후 Task 설계
        5. 프레임워크 규칙({project.framework or "해당없음"})을 따를 것
        6. 결과는 반드시 JSON 형식으로만 반환
    """


async def _load_spec_content(spec: Spec) -> str:
    """Spec에서 분석할 텍스트 내용을 추출합니다."""
    if spec.raw_content:
        return spec.raw_content

    if spec.source_path:
        # TODO: 파일에서 텍스트 추출 (PDF/DOCX는 별도 라이브러리 필요, 여기서는 텍스트 파일 처리)
        try:
            with open(spec.source_path, encoding="utf-8", errors="ignore") as f:
                return f.read()
        except OSError as e:
            logger.warning("Spec 파일 읽기 실패: %s", e)
            return f"[파일 읽기 실패: {spec.source_path}]"

    return "[Spec 내용 없음]"


async def _update_spec_status(spec_id: str, status: str, analysis_result: str | None = None) -> None:
    """Spec 상태와 분석 결과를 업데이트합니다."""
    async with db_conn.transaction() as session:
        spec = await spec_repository.find_by_id(spec_id, session)
        if spec:
            spec.status = status
            if analysis_result is not None:
                spec.analysis_result = analysis_result
            await session.flush()


async def _save_tasks(project_id: str, spec_id: str, task_items: list[dict]) -> list[Task]:
    """분해된 Task 목록을 DB에 저장합니다."""
    saved: list[Task] = []
    async with db_conn.transaction() as session:
        for idx, item in enumerate(task_items):
            task = Task(
                project_id=project_id,
                spec_id=spec_id,
                title=item["title"],
                description=item["description"],
                acceptance_criteria=item.get("acceptance_criteria"),
                priority=item.get("priority", "medium"),
                complexity=item.get("complexity", "medium"),
                dependencies=None,  # 제목 기반 의존성은 저장 후 별도 매핑 필요
                status="plan_reviewing",
                sort_order=idx,
            )
            session.add(task)
            await session.flush()
            await session.refresh(task)
            saved.append(task)
    return saved


async def analyze_spec_and_create_tasks(spec_id: str) -> None:
    """
    Spec을 분석하여 Task 목록을 자동 생성합니다.

    1. Spec 로드 → 상태 'analyzing'으로 변경
    2. Design Agent 실행 (claude-code-sdk query)
    3. 분석 결과 DB 저장, Spec 상태 'analyzed'로 변경
    4. 각 단계마다 WebSocket으로 진행상황 브로드캐스트
    """
    # 1. Spec / Project 로드
    spec = await spec_repository.find_by_id(spec_id)
    if not spec:
        logger.error("Spec not found: %s", spec_id)
        return

    project = await project_repository.find_by_id(spec.project_id)
    if not project:
        logger.error("Project not found: %s", spec.project_id)
        return

    project_id = project.id

    async def broadcast(msg: dict) -> None:
        await ws_manager.broadcast(project_id, msg)

    # 2. 상태 → analyzing
    await _update_spec_status(spec_id, "analyzing")
    await broadcast({"type": "spec_analyzing", "spec_id": spec_id})

    try:
        spec_content = await _load_spec_content(spec)
        prompt = _build_prompt(spec_content, project)

        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="bypassPermissions",
            max_turns=30,
            output_format={"type": "json_schema", "schema": TASK_LIST_SCHEMA},
        )

        parsed: dict | None = None

        print("에이전트 시작")
        async for message in query(prompt=prompt, options=options):
            # 에이전트 메시지를 WebSocket으로 전달
            try:
                msg_data = message.model_dump() if hasattr(message, "model_dump") else str(message)
            except Exception:
                msg_data = str(message)

            await broadcast({"type": "agent_message", "spec_id": spec_id, "message": msg_data})

            # ResultMessage에서 structured_output 추출 (output_format=json_schema 사용 시)
            if hasattr(message, "structured_output") and message.structured_output is not None:
                parsed = message.structured_output
                
            # fallback: AssistantMessage content에서 텍스트 추출 후 JSON 파싱
            elif hasattr(message, "result") and message.result:
                try:
                    parsed = json.loads(message.result)
                except (json.JSONDecodeError, TypeError):
                    pass

        # 3. 결과 파싱
        if not parsed:
            raise ValueError("에이전트가 결과를 반환하지 않았습니다.")
        task_items: list[dict] = (parsed or {}).get("tasks", [])
        analysis_summary: str = (parsed or {}).get("analysis_summary", "")

        # 4. Task DB 저장
        saved_tasks = await _save_tasks(project_id, spec_id, task_items)

        # 5. Spec 상태 → analyzed (분석 완료)
        await _update_spec_status(
            spec_id,
            "analyzed",
            analysis_result=json.dumps(parsed or {}, ensure_ascii=False),
        )
        print("스펙 업데이트")

        # 6. 완료 브로드캐스트
        await broadcast(
            {
                "type": "spec_analyzed",
                "spec_id": spec_id,
                "analysis_summary": analysis_summary,
                "tasks": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "description": t.description,
                        "priority": t.priority,
                        "complexity": t.complexity,
                        "status": t.status,
                    }
                    for t in saved_tasks
                ],
            }
        )

    except Exception as exc:
        logger.exception("Design Agent 실행 실패 (spec_id=%s): %s", spec_id, exc)
        await _update_spec_status(spec_id, "uploaded")  # 실패 시 원복
        await broadcast(
            {
                "type": "spec_analyze_failed",
                "spec_id": spec_id,
                "error": str(exc),
            }
        )
