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


# 메시지 직열화
def extract_agent_msg_data(message: Any) -> Any:
    try:
        return message.model_dump() if hasattr(message, "model_dump") else str(message)
    except Exception:
        return str(message)


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
