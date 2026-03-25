"""Legacy Analysis Agent — supports Q&A chat about an existing codebase."""

from __future__ import annotations

import json
import logging

from claude_agent_sdk import query, ClaudeAgentOptions

from app.agents.prompts import load_prompt

logger = logging.getLogger(__name__)


async def chat_with_legacy_code(code_path: str, question: str, focused_file: str | None = None) -> dict:
    """
    분석 없이 소스코드를 직접 탐색하며 질문에 답합니다.
    에이전트는 Glob/Grep으로 관련 파일을 찾고 Read로 내용을 확인합니다.
    JSON 형식({ summary, sections })으로 반환합니다.
    """
    prompt = load_prompt(
        "legacy_chat_agent.md",
        code_path=code_path,
        question=question,
        focused_file=focused_file or "없음",
    )

    options = ClaudeAgentOptions(
        model="claude-haiku-4-5-20251001",
        allowed_tools=["Read", "Glob", "Grep"],
        permission_mode="bypassPermissions",
        max_turns=15,
    )

    result_text: str | None = None
    last_assistant_text: str | None = None

    async for message in query(prompt=prompt, options=options):
        # ResultMessage: 최종 결과
        if hasattr(message, "result") and message.result:
            result_text = message.result
            continue

        # AssistantMessage: content 블록에서 텍스트 추출 (fallback용)
        if hasattr(message, "role") and message.role == "assistant":
            content = getattr(message, "content", []) or []
            parts = [
                block.get("text", "") if isinstance(block, dict) else getattr(block, "text", "")
                for block in content
                if (isinstance(block, dict) and block.get("type") == "text")
                or (hasattr(block, "type") and block.type == "text")
            ]
            text = "\n".join(p for p in parts if p).strip()
            if text:
                last_assistant_text = text

    raw = result_text or last_assistant_text or ""
    return _parse_chat_response(raw)


def _parse_chat_response(raw: str) -> dict:
    """에이전트 응답 텍스트에서 JSON을 추출합니다. 실패 시 fallback 구조로 반환."""
    # 마크다운 코드블록 제거
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[: text.rfind("```")]
        text = text.strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict) and "summary" in data:
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # JSON 파싱 실패 → 텍스트를 summary로 감싸서 반환
    return {"summary": raw or "답변을 생성하지 못했습니다.", "flow": []}
