"""웹소켓 메시지 타입 중앙 관리"""

from __future__ import annotations

from typing import Any, Callable, Awaitable

# 공통 타입
BroadcastFn = Callable[[dict[str, Any]], Awaitable[None]]


# 메시지 타입
class WsMsgType:
    # 설계 agent
    SPEC_ANALYZING = "spec_analyzing"
    SPEC_ANALYZED = "spec_analyzed"
    SPEC_ANALYZE_FAILED = "spec_analyze_failed"

    # Task / Orchestrator
    TASK_UPDATE = "task_update"
    REVIEW_RESULT = "review_result"

    # Agent streaming (shared across agents)
    AGENT_MESSAGE = "agent_message"

    # Guidemap 에이전트 메시지 타입
    GUIDEMAP_GENERATING = "guidemap_generating"
    GUIDEMAP_GENERATED = "guidemap_generated"
    GUIDEMAP_FAILED = "guidemap_failed"

    # 코드 분석 타입
    LEGACY_ANALYZING = "legacy_analyzing"
    LEGACY_ANALYZED = "legacy_analyzed"
    LEGACY_ANALYZE_FAILED = "legacy_analyze_failed"

    # 런타임 에러 타입
    RUNTIME_ERROR = "runtime_error"
    RUNTIME_ERROR_UPDATE = "runtime_error_update"
    RUNTIME_ERROR_AGENT_MESSAGE = "runtime_error_agent_message"


# 메시지 직열화 (전체 덤프 — 내부 디버깅용)
def extract_agent_msg_data(message: Any) -> Any:
    try:
        return message.model_dump() if hasattr(message, "model_dump") else str(message)
    except Exception:
        return str(message)


# 의미 있는 메시지만 추출 — None 반환 시 브로드캐스트 생략
# TODO: key - valude 메핑으로 바꾸기
def extract_meaningful_message(message: Any) -> dict | None:
    """
    클라이언트에 표시할 의미 있는 메시지만 추출합니다.

    반환 형식:
      {"kind": "text", "text": "..."}                           — 에이전트 텍스트
      {"kind": "progress", "tool": "...", "desc": "..."}        — 툴 사용 진행 상황
      {"kind": "task_done", "status": "...", "summary": "..."}  — 서브태스크 완료
      {"kind": "result", "text": "..."}                         — 전체 분석 최종 결과
    None 반환 시 브로드캐스트 하지 않습니다.
    """
    cls_name = type(message).__name__

    if cls_name == "AssistantMessage":
        items = []
        for block in getattr(message, "content", []):
            block_type = type(block).__name__
            if block_type == "TextBlock":
                text = getattr(block, "text", "").strip()
                if text:
                    items.append({"type": "text", "text": text})
            elif block_type == "ToolUseBlock":
                items.append({
                    "type": "tool_use",
                    "name": getattr(block, "name", ""),
                    "input": getattr(block, "input", {}),
                })
            elif block_type == "ThinkingBlock":
                thinking = getattr(block, "thinking", "").strip()
                if thinking:
                    items.append({"type": "thinking", "thinking": thinking})
        if not items:
            return None
        return {"kind": "assistant", "content": items}

    if cls_name == "TaskProgressMessage":
        tool = getattr(message, "last_tool_name", None)
        desc = getattr(message, "description", "")
        return {"kind": "progress", "tool": tool, "desc": desc}

    if cls_name == "TaskNotificationMessage":
        summary = getattr(message, "summary", None)
        status = getattr(message, "status", "")
        if not summary or not str(summary).strip():
            return None
        return {"kind": "task_done", "status": status, "summary": str(summary).strip()}

    if cls_name == "ResultMessage":
        result = getattr(message, "result", None)
        if not result or not str(result).strip():
            return None
        return {"kind": "result", "text": str(result).strip()}

    return None


# 스펙서 분석 메시지 
def msg_spec_analyzing(spec_id: str) -> dict:
    return {"type": WsMsgType.SPEC_ANALYZING, "spec_id": spec_id}


# 스펙서 분석 완료 메시지
def msg_spec_analyzed(spec_id: str, analysis_summary: str, tasks: list[dict]) -> dict:
    return {
        "type": WsMsgType.SPEC_ANALYZED,
        "spec_id": spec_id,
        "analysis_summary": analysis_summary,
        "tasks": tasks,
    }


# 스펙서 문석 실패 메시지
def msg_spec_analyze_failed(spec_id: str, error: str) -> dict:
    return {"type": WsMsgType.SPEC_ANALYZE_FAILED, "spec_id": spec_id, "error": error}


# 태스트 업데이트 메시지
def msg_task_update(task_id: str, status: str, **kwargs: Any) -> dict:
    return {"type": WsMsgType.TASK_UPDATE, "task_id": task_id, "status": status, **kwargs}


# 검토 및 테스트 메시지
def msg_review_result(
    task_id: str,
    attempt: int,
    passed: bool,
    test_output: str,
    feedback: str,
) -> dict:
    return {
        "type": WsMsgType.REVIEW_RESULT,
        "task_id": task_id,
        "attempt": attempt,
        "passed": passed,
        "test_output": test_output,
        "feedback": feedback,
    }


# 에이전트 메시지
def msg_agent_message(message: Any, **context: Any) -> dict:
    return {"type": WsMsgType.AGENT_MESSAGE, "message": message, **context}


# guidemap 생성중 메시지
def msg_guidemap_generating(project_id: str) -> dict:
    return {"type": WsMsgType.GUIDEMAP_GENERATING, "project_id": project_id}


# guidemap 생성 완료 메시지
def msg_guidemap_generated(project_id: str) -> dict:
    return {"type": WsMsgType.GUIDEMAP_GENERATED, "project_id": project_id}


# guidemap 생성 실패 메시지
def msg_guidemap_failed(project_id: str, error: str) -> dict:
    return {"type": WsMsgType.GUIDEMAP_FAILED, "project_id": project_id, "error": error}


# 코드 분석중 메시지
def msg_legacy_analyzing(session_id: str) -> dict:
    return {"type": WsMsgType.LEGACY_ANALYZING, "session_id": session_id}


# 코드 분석 완료 메시지
def msg_legacy_analyzed(session_id: str, sections: list[dict]) -> dict:
    return {"type": WsMsgType.LEGACY_ANALYZED, "session_id": session_id, "sections": sections}


# 코드 분석 실패 메시지
def msg_legacy_analyze_failed(session_id: str, error: str) -> dict:
    return {"type": WsMsgType.LEGACY_ANALYZE_FAILED, "session_id": session_id, "error": error}


# 런타임 에러 메시지()
def msg_runtime_error(data: dict) -> dict:
    return {"type": WsMsgType.RUNTIME_ERROR, "data": data}


# 런타임 에서 업데이트 메시지
def msg_runtime_error_update(id: str, status: str, fix_suggestion: str | None = None) -> dict:
    return {
        "type": WsMsgType.RUNTIME_ERROR_UPDATE,
        "data": {"id": id, "status": status, "fix_suggestion": fix_suggestion},
    }


# 런타임 에러 에이전트 메시지 
def msg_runtime_error_agent_message(error_id: str, message: str) -> dict:
    return {
        "type": WsMsgType.RUNTIME_ERROR_AGENT_MESSAGE,
        "data": {"error_id": error_id, "message": message},
    }
