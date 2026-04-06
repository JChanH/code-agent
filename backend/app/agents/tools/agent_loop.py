"""공통 Agentic Loop.

claude_agent_sdk의 query()를 대체하는 직접 API 기반 루프입니다.
tool_use 블록을 감지하면 도구를 실행하고, end_turn이 될 때까지 반복합니다.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Awaitable

import anthropic

from app.agents.tools.registry import get_tool_definitions, dispatch_tool

logger = logging.getLogger(__name__)

# on_message 콜백 타입: (text_content, tool_name | None) → None
OnMessageFn = Callable[[dict[str, Any]], Awaitable[None] | None]


async def run_agent_loop(
    client: anthropic.AsyncAnthropic,
    model: str,
    messages: list[dict[str, Any]],
    tool_names: list[str],
    max_turns: int,
    working_dir: str | None = None,
    tool_choice: dict[str, Any] | None = None,
    system: str | None = None,
    on_message: OnMessageFn | None = None,
    turn_delay: float = 1.0,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Claude API를 반복 호출하는 agentic loop.

    Args:
        client: AsyncAnthropic 클라이언트
        model: 사용할 모델 ID
        messages: 초기 메시지 목록 (수정됨 — 호출 후 전체 대화 히스토리 포함)
        tool_names: 허용할 도구 이름 목록 (registry.py의 도구 이름)
        max_turns: 최대 턴 수 (초과 시 현재 결과 반환)
        working_dir: 도구 핸들러에 전달할 작업 디렉토리
        tool_choice: {"type": "auto"} | {"type": "tool", "name": "..."} | None → auto
        system: 시스템 프롬프트 (선택)
        on_message: 각 어시스턴트 응답마다 호출될 콜백
        turn_delay: 툴 실행 후 다음 API 호출 전 대기 시간(초). rate limit 방지용. 기본 1.0초

    Returns:
        (마지막 텍스트 출력, 최종 messages 리스트)
    """
    tools = get_tool_definitions(tool_names) if tool_names else []
    effective_tool_choice = tool_choice or {"type": "auto"}

    final_text = ""
    turns = 0

    logger.info("XXX messages: %s", messages)

    while turns < max_turns:
        turns += 1

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": 8096,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = effective_tool_choice
        if system:
            kwargs["system"] = system

        response = await client.messages.create(**kwargs)

        # 어시스턴트 응답을 메시지 히스토리에 추가
        assistant_content = _content_blocks_to_list(response.content)
        messages.append({"role": "assistant", "content": assistant_content})

        # on_message 콜백 — WebSocket broadcast 등에 활용
        if on_message:
            payload = _build_message_payload(response.content)
            result = on_message(payload)
            if result is not None:
                await result

        # 텍스트 블록 수집
        for block in response.content:
            if block.type == "text":
                final_text = block.text

        # tool_use 블록이 없으면 종료
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            break

        # 도구 실행 후 tool_result 메시지 추가
        tool_results = []
        for block in tool_use_blocks:
            tool_result = await dispatch_tool(block.name, block.input, working_dir=working_dir)
            logger.debug("Tool %s → %s chars", block.name, len(tool_result))
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": tool_result,
            })

        messages.append({"role": "user", "content": tool_results})

        if turn_delay > 0:
            await asyncio.sleep(turn_delay)

    if turns >= max_turns:
        logger.warning("Agent loop reached max_turns=%d", max_turns)

    return final_text, messages


# ---------------------------------------------------------------------------
# 내부 유틸리티
# ---------------------------------------------------------------------------

def _content_blocks_to_list(content: list[Any]) -> list[dict[str, Any]]:
    """SDK content 블록을 API 메시지 형식의 dict 리스트로 변환합니다."""
    result = []
    for block in content:
        if block.type == "text":
            result.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            result.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })
        elif block.type == "thinking":
            result.append({"type": "thinking", "thinking": getattr(block, "thinking", "")})
        else:
            # 알 수 없는 블록 타입은 그대로 저장
            result.append({"type": block.type})
    return result


def _build_message_payload(content: list[Any]) -> dict[str, Any]:
    """
    on_message 콜백에 전달할 payload를 만듭니다.
    messages.py의 extract_meaningful_message와 동일한 형식을 사용합니다.
    """
    items = []
    for block in content:
        if block.type == "text":
            text = block.text.strip()
            if text:
                items.append({"type": "text", "text": text})
        elif block.type == "tool_use":
            items.append({
                "type": "tool_use",
                "name": block.name,
                "input": block.input,
            })
        elif block.type == "thinking":
            thinking = getattr(block, "thinking", "").strip()
            if thinking:
                items.append({"type": "thinking", "thinking": thinking})
    return {"kind": "assistant", "content": items}
