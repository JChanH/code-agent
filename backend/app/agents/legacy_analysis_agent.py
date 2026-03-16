"""Legacy Analysis Agent — analyzes an existing codebase and supports Q&A chat."""

from __future__ import annotations

import json
import logging
from typing import Callable, Awaitable

from claude_agent_sdk import query, ClaudeAgentOptions

from app.websocket import ws_manager
from app.agents.prompts import load_prompt

logger = logging.getLogger(__name__)

# In-memory session store: session_id → { code_path, summary, sections }
ANALYSIS_SESSIONS: dict[str, dict] = {}


async def analyze_legacy_code(session_id: str, code_path: str) -> None:
    """
    Analyzes a legacy codebase at code_path.
    Broadcasts progress via WebSocket channel keyed by session_id.
    Stores the result in ANALYSIS_SESSIONS for follow-up chat.
    """

    async def broadcast(msg: dict) -> None:
        await ws_manager.broadcast(session_id, msg)

    await broadcast({"type": "legacy_analyzing", "session_id": session_id})

    try:
        prompt = load_prompt("legacy_analysis_agent.md", code_path=code_path)

        options = ClaudeAgentOptions(
            model="claude-sonnet-4-6",
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="bypassPermissions",
            max_turns=20,
        )

        result_text: str | None = None

        async for message in query(prompt=prompt, options=options):
            try:
                msg_data = message.model_dump() if hasattr(message, "model_dump") else str(message)
            except Exception:
                msg_data = str(message)
            await broadcast({"type": "agent_message", "session_id": session_id, "message": msg_data})

            if hasattr(message, "result") and message.result:
                result_text = message.result

        if not result_text:
            raise ValueError("Agent returned no content.")

        parsed = _parse_result(result_text)
        sections = parsed.get("sections", [])
        summary = parsed.get("summary", result_text[:500])

        ANALYSIS_SESSIONS[session_id] = {
            "code_path": code_path,
            "summary": summary,
            "sections": sections,
        }

        await broadcast({
            "type": "legacy_analyzed",
            "session_id": session_id,
            "sections": sections,
        })

    except Exception as exc:
        logger.exception("Legacy analysis failed (session_id=%s): %s", session_id, exc)
        await broadcast({
            "type": "legacy_analyze_failed",
            "session_id": session_id,
            "error": str(exc),
        })


def _parse_result(text: str) -> dict:
    """JSON 파싱 시도 — 실패 시 raw 텍스트를 단일 섹션으로 래핑."""
    text = text.strip()
    # strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "sections": [{"title": "📋 분석 결과", "content": text}],
            "summary": text[:500],
        }


async def chat_with_legacy_code(session_id: str, question: str) -> str:
    """
    Answers a question about the previously analyzed codebase.
    Returns the answer as a plain string.
    """
    session = ANALYSIS_SESSIONS.get(session_id)
    if not session:
        return "분석 세션을 찾을 수 없습니다. 먼저 코드 분석을 실행해 주세요."

    code_path = session["code_path"]
    analysis_summary = session.get("summary", "")

    prompt = load_prompt(
        "legacy_chat_agent.md",
        code_path=code_path,
        analysis_summary=analysis_summary,
        question=question,
    )

    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        allowed_tools=["Read", "Glob", "Grep"],
        permission_mode="bypassPermissions",
        max_turns=5,
    )

    result_text: str | None = None

    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result") and message.result:
            result_text = message.result

    return result_text or "답변을 생성하지 못했습니다."
