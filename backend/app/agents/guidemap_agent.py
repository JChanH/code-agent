"""Guidemap Agent — analyzes an existing codebase and writes EXISTING_PROJECT_GUIDE.md."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions

from app.models import Project
from app.websocket import ws_manager
from app.agents.prompts import load_prompt

logger = logging.getLogger(__name__)

_GUIDEMAP_DIR = Path(__file__).parent / "guidemaps"


def _get_guidemap_path(project_name: str) -> Path:
    return _GUIDEMAP_DIR / f"{project_name}_guidemap.md"


def guidemap_exists(project_name: str) -> bool:
    return _get_guidemap_path(project_name).exists()


_DESIGN_SECTIONS = {"## Directory Guide", "## Naming Conventions"}


def get_design_context(project_name: str) -> str | None:
    """design agent용 섹션(Directory Guide, Naming Conventions)만 추출해서 반환."""
    path = _get_guidemap_path(project_name)
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    parts = re.split(r"^(## .+)$", content, flags=re.MULTILINE)
    result = [parts[0]]  # h1 title
    for i in range(1, len(parts) - 1, 2):
        if parts[i].strip() in _DESIGN_SECTIONS:
            result.append(parts[i] + parts[i + 1])
    return "".join(result)


def _build_prompt(project: Project) -> str:
    return load_prompt(
        "guidemap_agent.md",
        local_repo_path=project.local_repo_path,
        project_stack=project.project_stack,
        framework=project.framework or "unspecified",
    )


def _save_guidemap(project_name: str, content: str) -> Path:
    path = _get_guidemap_path(project_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info("Guidemap written to %s", path)
    return path


async def generate_guidemap(project: Project) -> None:
    """
    * 기존 프로젝트에 대해서 guidemap을 생성하여 로컬에 저장합니다.
    * 내용은 websocket을 통해서 전달합니다.
    """
    project_id = project.id

    async def broadcast(msg: dict) -> None:
        await ws_manager.broadcast(project_id, msg)

    await broadcast({"type": "guidemap_generating", "project_id": project_id})

    try:
        prompt = _build_prompt(project)
        
        logging.info("프롬프트", prompt)

        options = ClaudeAgentOptions(
            model="claude-sonnet-4-6",
            # model="claude-haiku-4-5-20251001",
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="bypassPermissions",
            max_turns=30,
        )

        result_text: str | None = None

        async for message in query(prompt=prompt, options=options):
            try:
                msg_data = message.model_dump() if hasattr(message, "model_dump") else str(message)
            except Exception:
                msg_data = str(message)
            await broadcast({"type": "agent_message", "project_id": project_id, "message": msg_data})

            if hasattr(message, "result") and message.result:
                result_text = message.result

        if not result_text:
            raise ValueError("Guidemap agent returned no content.")

        _save_guidemap(project.name, result_text)

        await broadcast({
            "type": "guidemap_generated",
            "project_id": project_id,
            "path": str(_get_guidemap_path(project.name)),
        })

    except Exception as exc:
        logger.exception("Guidemap generation failed (project_id=%s): %s", project_id, exc)
        await broadcast({
            "type": "guidemap_failed",
            "project_id": project_id,
            "error": str(exc),
        })
