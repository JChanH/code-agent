"""Runtime Error Analysis Agent — analyzes a runtime error and suggests a fix."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from claude_agent_sdk import query, ClaudeAgentOptions

logger = logging.getLogger(__name__)


def _format_agent_log(msg_obj: Any) -> str | None:
    """Extract a human-readable log line from a Claude agent SDK message object."""
    if hasattr(msg_obj, "role") and msg_obj.role == "assistant":
        content = getattr(msg_obj, "content", []) or []
        parts: list[str] = []
        for block in content:
            if not hasattr(block, "type"):
                continue
            if block.type == "text" and hasattr(block, "text") and block.text:
                snippet = block.text.strip()[:100]
                if snippet:
                    parts.append(snippet)
            elif block.type == "tool_use" and hasattr(block, "name"):
                try:
                    input_str = json.dumps(getattr(block, "input", {}), ensure_ascii=False)[:80]
                except Exception:
                    input_str = ""
                parts.append(f"[{block.name}] {input_str}")
        return " | ".join(parts) if parts else None
    return None


def _build_prompt(
    error_code: str,
    message: str,
    level: str,
    project_id: str,
    local_repo_path: str,
    metadata: dict | None,
) -> str:
    meta_lines = ""
    if metadata:
        for k, v in metadata.items():
            meta_lines += f"  - {k}: {v}\n"

    return f"""당신은 백엔드 서버 런타임 오류를 분석하는 전문가입니다.
아래 오류 정보와 프로젝트 소스 코드를 분석하여 두 가지를 반드시 명확하게 답변해야 합니다.

## 오류 정보
- 프로젝트 이름: {project_id}
- 프로젝트 소스 코드 경로: {local_repo_path}
- 오류 레벨: {level}
- 오류 코드: {error_code}
- 오류 메시지: {message}
{f'- 메타데이터:{chr(10)}{meta_lines}' if meta_lines else ''}
## 분석 요청

프로젝트 소스 코드({local_repo_path})를 직접 탐색한 후, 다음 두 가지를 반드시 포함하여 한국어로 답변하세요.

### 1. 원인
이 오류가 발생한 근본 원인이 무엇인지 설명하세요.
- 어떤 상황에서 발생하는 오류인지
- 오류 메시지가 의미하는 바
- 가능한 원인 목록 (우선순위 순)

### 2. 수정 방법
소스 코드를 탐색하여 실제 수정이 필요한 파일과 코드를 찾아 구체적으로 제시하세요.
- 수정해야 할 파일의 정확한 경로 (프로젝트 내 상대경로)
- 수정이 필요한 코드 부분
- 구체적인 수정 방법 또는 수정 코드 예시

간결하고 실용적으로 작성하세요."""


async def analyze_runtime_error(
    error_id: str,
    error_code: str,
    message: str,
    level: str,
    project_id: str,
    local_repo_path: str = "",
    metadata: dict | None = None,
    on_progress: Callable[[str], Coroutine[Any, Any, None]] | None = None,
) -> str:
    """
    런타임 오류를 분석하고 fix_suggestion 텍스트를 반환합니다.
    실패 시 오류 메시지 문자열을 반환합니다.
    """
    prompt = _build_prompt(
        error_code=error_code,
        message=message,
        level=level,
        project_id=project_id,
        local_repo_path=local_repo_path,
        metadata=metadata,
    )

    options = ClaudeAgentOptions(
        model="claude-haiku-4-5-20251001",
        allowed_tools=["Read", "Glob", "Grep"],
        permission_mode="bypassPermissions",
        max_turns=15,
    )

    result_text: str | None = None
    last_assistant_text: str | None = None

    try:
        async for message_obj in query(prompt=prompt, options=options):
            if hasattr(message_obj, "result") and message_obj.result:
                result_text = message_obj.result
                continue

            if hasattr(message_obj, "role") and message_obj.role == "assistant":
                content = getattr(message_obj, "content", []) or []
                parts = [
                    block.get("text", "") if isinstance(block, dict) else getattr(block, "text", "")
                    for block in content
                    if (isinstance(block, dict) and block.get("type") == "text") or
                    (hasattr(block, "type") and block.type == "text")
                ]
                text = "\n".join(p for p in parts if p).strip()
                if text:
                    last_assistant_text = text

            if on_progress is not None:
                log_line = _format_agent_log(message_obj)
                if log_line:
                    await on_progress(log_line)

        suggestion = result_text or last_assistant_text
        if not suggestion:
            raise ValueError("에이전트가 분석 결과를 반환하지 않았습니다.")

        logger.info("Runtime error analysis complete (error_id=%s)", error_id)
        return suggestion

    except Exception as exc:
        logger.exception("Runtime error analysis failed (error_id=%s): %s", error_id, exc)
        return f"자동 분석 실패: {exc}"
