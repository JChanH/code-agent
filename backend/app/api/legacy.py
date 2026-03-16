"""Legacy code analysis API router."""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.agents.legacy_analysis_agent import analyze_legacy_code, chat_with_legacy_code, ANALYSIS_SESSIONS
from app.schemas.common import ApiResponse

legacy_router = APIRouter(prefix="/legacy", tags=["legacy"])


class AnalyzeRequest(BaseModel):
    session_id: str
    code_path: str


class ChatRequest(BaseModel):
    session_id: str
    question: str


@legacy_router.post("/analyze", response_model=ApiResponse[dict])
async def start_analysis(body: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    레거시 코드 경로를 받아 분석을 시작합니다.
    즉시 queued 상태를 반환하고, 진행 상황은 WebSocket(/ws/{session_id})으로 전송됩니다.
    """
    if not body.code_path.strip():
        raise HTTPException(status_code=400, detail="code_path는 필수입니다.")

    background_tasks.add_task(analyze_legacy_code, body.session_id, body.code_path)

    return ApiResponse.ok({
        "session_id": body.session_id,
        "status": "queued",
        "message": "분석이 시작되었습니다. WebSocket으로 진행상황을 확인하세요.",
    })


@legacy_router.post("/chat", response_model=ApiResponse[dict])
async def chat(body: ChatRequest):
    """
    분석된 코드베이스에 대해 질문합니다.
    분석이 완료된 session_id가 필요합니다.
    """
    if body.session_id not in ANALYSIS_SESSIONS:
        raise HTTPException(status_code=404, detail="분석 세션을 찾을 수 없습니다. 먼저 분석을 실행하세요.")

    answer = await chat_with_legacy_code(body.session_id, body.question)

    return ApiResponse.ok({
        "session_id": body.session_id,
        "answer": answer,
    })
