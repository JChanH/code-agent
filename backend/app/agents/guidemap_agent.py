"""Guidemap Agent — analyzes an existing codebase and writes EXISTING_PROJECT_GUIDE.md."""

from __future__ import annotations

import logging
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions

from app.models import Project
from app.websocket import ws_manager
from app.agents.prompts import load_prompt

logger = logging.getLogger(__name__)

_GUIDEMAP_RELATIVE_PATH = Path("docs") / "guidemap" / "EXISTING_PROJECT_GUIDE.md"


def _get_guidemap_path(local_repo_path: str) -> Path:
    return Path(local_repo_path) / _GUIDEMAP_RELATIVE_PATH


def guidemap_exists(local_repo_path: str) -> bool:
    return _get_guidemap_path(local_repo_path).exists()


def _build_prompt(project: Project) -> str:
    return load_prompt(
        "guidemap_agent.md",
        local_repo_path=project.local_repo_path,
        project_stack=project.project_stack,
        framework=project.framework or "unspecified",
    )


def _save_guidemap(local_repo_path: str, content: str) -> Path:
    path = _get_guidemap_path(local_repo_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info("Guidemap written to %s", path)
    return path


async def generate_guidemap(project: Project) -> None:
    """
    Runs the guidemap agent for an existing project.
    Broadcasts guidemap_generating → guidemap_generated / guidemap_failed via WebSocket.
    """
    project_id = project.id

    async def broadcast(msg: dict) -> None:
        await ws_manager.broadcast(project_id, msg)

    await broadcast({"type": "guidemap_generating", "project_id": project_id})

    try:
        prompt = _build_prompt(project)

        options = ClaudeAgentOptions(
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

        _save_guidemap(project.local_repo_path, result_text)

        await broadcast({
            "type": "guidemap_generated",
            "project_id": project_id,
            "path": str(_get_guidemap_path(project.local_repo_path)),
        })

    except Exception as exc:
        logger.exception("Guidemap generation failed (project_id=%s): %s", project_id, exc)
        await broadcast({
            "type": "guidemap_failed",
            "project_id": project_id,
            "error": str(exc),
        })
