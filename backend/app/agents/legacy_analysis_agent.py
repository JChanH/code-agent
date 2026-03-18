"""Legacy Analysis Agent — analyzes an existing codebase and supports Q&A chat."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Callable, Awaitable  # noqa: F401 — used in type hint of _run_analysis_agent

from claude_agent_sdk import query, ClaudeAgentOptions

from app.websocket import ws_manager
from app.agents.prompts import load_prompt

logger = logging.getLogger(__name__)

# In-memory session store: session_id → { code_path, summary, sections }
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


async def _run_analysis_agent(
    prompt_name: str,
    code_path: str,
    session_id: str,
    broadcast: Callable[[dict], Awaitable[None]],
) -> dict:
    """단일 분석 에이전트를 실행하고 파싱된 결과 dict를 반환."""
    prompt = load_prompt(prompt_name, code_path=code_path)

    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        allowed_tools=["Read", "Glob", "Grep"],
        permission_mode="bypassPermissions",
        max_turns=10,
    )

    result_text: str | None = None

    async for message in query(prompt=prompt, options=options):
        try:
            msg_data = message.model_dump() if hasattr(message, "model_dump") else str(message)
        except Exception:
            msg_data = str(message)
        await broadcast({
            "type": "agent_message",
            "session_id": session_id,
            "agent": prompt_name,
            "message": msg_data,
        })

        if hasattr(message, "result") and message.result:
            result_text = message.result

    if not result_text:
        logger.warning("에이전트 %s가 결과를 반환하지 않았습니다.", prompt_name)
        return {}

    return _parse_result(result_text)


def _build_summary(merged: dict) -> str:
    """병합된 분석 결과에서 요약 문자열을 생성."""
    # infra agent가 summary를 포함하는 경우 우선 사용
    if merged.get("summary"):
        return merged["summary"]

    parts = []
    meta = merged.get("project_meta", {})
    if meta.get("frameworks"):
        parts.append(f"프레임워크: {', '.join(meta['frameworks'])}")
    if merged.get("external_interfaces"):
        parts.append(f"API 엔드포인트 {len(merged['external_interfaces'])}개")
    if merged.get("services"):
        parts.append(f"서비스 {len(merged['services'])}개")
    if merged.get("models"):
        parts.append(f"모델 {len(merged['models'])}개")
    return " | ".join(parts) if parts else "분석 완료"


async def analyze_legacy_code(session_id: str, code_path: str) -> None:
    """
    Analyzes a legacy codebase at code_path using 3 parallel specialized agents.
    Broadcasts progress via WebSocket channel keyed by session_id.
    Stores the result in ANALYSIS_SESSIONS and saves to analyze_result/ directory.
    """

    async def broadcast(msg: dict) -> None:
        await ws_manager.broadcast(session_id, msg)

    await broadcast({"type": "legacy_analyzing", "session_id": session_id})

    try:
        # 3개 분석 에이전트 병렬 실행
        agent_a, agent_b, agent_c = await asyncio.gather(
            _run_analysis_agent("legacy_analysis_api.md", code_path, session_id, broadcast),
            _run_analysis_agent("legacy_analysis_core.md", code_path, session_id, broadcast),
            _run_analysis_agent("legacy_analysis_infra.md", code_path, session_id, broadcast),
        )

        # 결과 병합: infra(기반) → api → core 순으로 덮어쓰기
        merged: dict = {**agent_c, **agent_a, **agent_b}
        merged["summary"] = _build_summary(merged)

        # unknowns 통합 (각 에이전트의 unknowns 합산)
        merged["unknowns"] = (
            agent_c.get("unknowns", [])
            + agent_a.get("unknowns", [])
            + agent_b.get("unknowns", [])
        )

        # 파일 저장
        project_name = _get_project_name(code_path)
        _save_analysis_result(project_name, merged)

        # sections 구성: 각 에이전트 결과를 섹션으로 분리
        sections = [
            {"title": "📡 API Surface", "content": json.dumps(agent_a, ensure_ascii=False, indent=2)},
            {"title": "⚙️ Core Logic", "content": json.dumps(agent_b, ensure_ascii=False, indent=2)},
            {"title": "🏗️ Infra / Dependency", "content": json.dumps(agent_c, ensure_ascii=False, indent=2)},
        ]

        ANALYSIS_SESSIONS[session_id] = {
            "code_path": code_path,
            "summary": merged["summary"],
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
