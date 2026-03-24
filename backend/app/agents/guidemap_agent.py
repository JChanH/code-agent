"""Guidemap Agent — analyzes an existing codebase and writes EXISTING_PROJECT_GUIDE.md."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions

from app.models import Project
from app.websocket import make_broadcaster
from app.websocket.messages import (
    extract_agent_msg_data,
    msg_agent_message,
    msg_guidemap_failed,
    msg_guidemap_generated,
    msg_guidemap_generating,
)
from app.agents.prompts import load_prompt

logger = logging.getLogger(__name__)

# 임시 경로
_GUIDEMAP_DIR = Path(__file__).parent / "guidemaps"


def _get_guidemap_path(project_name: str, kind: str) -> Path:
    # design과 code에 따라서 분기 처리
    return _GUIDEMAP_DIR / f"{project_name}_{kind}.md"


def guidemap_exists(project_name: str) -> bool:
    # design이 있다면 code도 있다고 확정
    return _get_guidemap_path(project_name, "design").exists()


def get_design_context(project_name: str) -> str | None:
    # design 파일 반환
    path = _get_guidemap_path(project_name, "design")
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _parse_and_save(project_name: str, result_text: str) -> None:
    # agent 반환 문자 구분 및 저장
    design = re.search(r"<design>(.*?)</design>", result_text, re.DOTALL)
    code = re.search(r"<code>(.*?)</code>", result_text, re.DOTALL)
    
    if not design or not code:
        raise ValueError("Guidemap 생성 실패입니다.")
        
    for kind, content in [("design", design.group(1)), ("code", code.group(1))]:
        path = _get_guidemap_path(project_name, kind)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip(), encoding="utf-8")
        
        logger.info("Guidemap 경로 %s", path)
        

def _build_prompt(project: Project) -> str:
    # 프롬프트 조합
    return load_prompt(
        "guidemap_agent.md",
        local_repo_path=project.local_repo_path,
        project_stack=project.project_stack,
        framework=project.framework or "unspecified",
    )


async def generate_guidemap(project: Project) -> None:
    """
    * 기존 프로젝트에 대해서 guidemap을 생성하여 로컬에 저장합니다.
    * 내용은 websocket을 통해서 전달합니다.
    """
    project_id = project.id

    broadcast = make_broadcaster(project_id)

    await broadcast(msg_guidemap_generating(project_id))

    try:
        prompt = _build_prompt(project)

        options = ClaudeAgentOptions(
            model="claude-sonnet-4-6",
            # model="claude-haiku-4-5-20251001",
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="bypassPermissions",
            max_turns=30,
        )

        result_text: str | None = None

        async for message in query(prompt=prompt, options=options):
            await broadcast(
                msg_agent_message(
                    extract_agent_msg_data(message),
                    project_id=project_id
                )
            )

            if hasattr(message, "result") and message.result:
                result_text = message.result

        if not result_text:
            raise ValueError("Guidemap agent returned no content.")

        # 내용 저장
        _parse_and_save(
            project_name=project.name,
            result_text=result_text
        )

        await broadcast(
            msg_guidemap_generated(project_id)
        )

    except Exception as exc:
        logger.exception("Guidemap generation failed (project_id=%s): %s", project_id, exc)
        await broadcast(msg_guidemap_failed(project_id, str(exc)))
