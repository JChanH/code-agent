"""Legacy Analysis Agent — analyzes an existing codebase and supports Q&A chat."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions

from app.websocket import make_broadcaster
from app.websocket.messages import (
    extract_agent_msg_data,
    msg_agent_message,
    msg_legacy_analyze_failed,
    msg_legacy_analyzed,
    msg_legacy_analyzing,
)
from app.agents.prompts import load_prompt

logger = logging.getLogger(__name__)

# In-memory session store: session_id → { code_path, nav_index }
ANALYSIS_SESSIONS: dict[str, dict] = {}

# Directory for persisted analysis results
_ANALYZE_RESULT_DIR = Path(__file__).parent / "analyze_result"


def _get_project_name(code_path: str) -> str:
    """코드 경로의 마지막 디렉토리명을 프로젝트 이름으로 반환."""
    return Path(code_path).name


def _save_analysis_result(project_name: str, data: dict) -> Path:
    """분석 결과를 analyze_result/{project_name}.json 파일로 저장."""
    _ANALYZE_RESULT_DIR.mkdir(parents=True, exist_ok=True)
    path = _ANALYZE_RESULT_DIR / f"{project_name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("분석 결과 저장: %s", path)
    return path


def _parse_result(text: str) -> dict:
    """JSON 파싱 시도 — 실패 시 빈 dict 반환."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("에이전트 결과를 JSON으로 파싱하지 못했습니다.")
        return {}


async def analyze_legacy_code(session_id: str, code_path: str) -> None:
    """
    API 엔드포인트 목록을 스캔하여 nav_index를 생성합니다.
    - WebSocket으로 진행상황을 브로드캐스트합니다.
    - 결과는 ANALYSIS_SESSIONS와 analyze_result/ 파일로 저장됩니다.
    """

    broadcast = make_broadcaster(session_id)

    await broadcast(msg_legacy_analyzing(session_id))

    try:
        prompt = load_prompt("legacy_analysis_api.md", code_path=code_path)

        options = ClaudeAgentOptions(
            model="claude-sonnet-4-6",
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="bypassPermissions",
            max_turns=15,
        )

        result_text: str | None = None

        async for message in query(prompt=prompt, options=options):
            await broadcast(msg_agent_message(extract_agent_msg_data(message), session_id=session_id))

            if hasattr(message, "result") and message.result:
                result_text = message.result

        if not result_text:
            raise ValueError("에이전트가 결과를 반환하지 않았습니다.")

        nav_index = _parse_result(result_text)

        # 파일 저장
        project_name = _get_project_name(code_path)
        _save_analysis_result(project_name, nav_index)

        # 세션 저장: QA에 필요한 정보만 보관
        ANALYSIS_SESSIONS[session_id] = {
            "code_path": code_path,
            "nav_index": nav_index,
        }

        sections = [
            {
                "title": "API 목록",
                "content": json.dumps(nav_index.get("apis", []), ensure_ascii=False, indent=2),
            }
        ]

        await broadcast(msg_legacy_analyzed(session_id, sections))

    except Exception as exc:
        logger.exception("Legacy analysis failed (session_id=%s): %s", session_id, exc)
        await broadcast(msg_legacy_analyze_failed(session_id, str(exc)))


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
