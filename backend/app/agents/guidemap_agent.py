"""Guidemap Agent — 현재의 코드베이스를 기준으로 agent에서 참고하는 guidemap을 생성"""

from __future__ import annotations

import logging
from pathlib import Path

import anthropic

from app.models import Project
from app.websocket import make_broadcaster
from app.websocket.messages import (
    msg_agent_message,
    msg_guidemap_failed,
    msg_guidemap_generated,
    msg_guidemap_generating,
)
from app.agents.prompts import load_prompt
from app.agents.tools.agent_loop import run_agent_loop
from app.config import get_settings

logger = logging.getLogger(__name__)

# 임시 경로
_GUIDEMAP_DIR = Path(__file__).parent / "guidemaps"


def _get_guidemap_path(project_name: str) -> Path:
    return _GUIDEMAP_DIR / f"{project_name}_guidemap.md"


def guidemap_exists(project_name: str) -> bool:
    return _get_guidemap_path(project_name).exists()


def get_guidemap_context(project_name: str) -> str | None:
    path = _get_guidemap_path(project_name)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _save_guidemap(project_name: str, result_text: str) -> None:
    path = _get_guidemap_path(project_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result_text.strip(), encoding="utf-8")
    logger.info("Guidemap 경로 %s", path)
        

def _build_prompt(project: Project) -> str:
    # 프롬프트 조합
    return load_prompt(
        "guidemap_agent.md",
        project_root=project.local_repo_path,
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

        settings = get_settings()
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        async def on_message(payload: dict) -> None:
            await broadcast(msg_agent_message(payload, project_id=project_id))

        result_text, _ = await run_agent_loop(
            client=client,
            model="claude-haiku-4-5-20251001",
            messages=[{"role": "user", "content": prompt}],
            tool_names=["read_file", "glob_files", "grep_search"],
            max_turns=20,
            working_dir=project.local_repo_path,
            on_message=on_message,
            turn_delay=1.5,
        )

        if not result_text:
            raise ValueError("Guidemap agent returned no content.")

        # 내용 저장
        _save_guidemap(
            project_name=project.name,
            result_text=result_text
        )

        await broadcast(
            msg_guidemap_generated(project_id)
        )

    except Exception as exc:
        logger.exception("Guidemap generation failed (project_id=%s): %s", project_id, exc)
        await broadcast(msg_guidemap_failed(project_id, str(exc)))
