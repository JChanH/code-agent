"""Legacy code analysis API router."""

from pathlib import Path as FsPath

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.agents.legacy_analysis_agent import analyze_legacy_code, chat_with_legacy_code
from app.schemas.common import ApiResponse

_EXCLUDED_DIRS = frozenset({
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".tox",
    ".next", ".nuxt", "coverage", ".cache", "target",
})
_EXCLUDED_EXTS = frozenset({
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin",
    ".jpg", ".jpeg", ".png", ".gif", ".ico",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".db", ".sqlite", ".sqlite3",
})
_MAX_DEPTH = 6
_MAX_FILE_SIZE = 1024 * 1024  # 1 MB


def _build_file_tree(path: FsPath, depth: int = 0) -> dict:
    node: dict = {
        "name": path.name,
        "path": path.as_posix(),
        "type": "directory" if path.is_dir() else "file",
    }
    if path.is_dir() and depth < _MAX_DEPTH:
        children: list[dict] = []
        try:
            items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
            for item in items:
                if item.is_dir() and item.name in _EXCLUDED_DIRS:
                    continue
                if item.is_file() and item.suffix.lower() in _EXCLUDED_EXTS:
                    continue
                children.append(_build_file_tree(item, depth + 1))
        except PermissionError:
            pass
        node["children"] = children
    return node


legacy_router = APIRouter(prefix="/legacy", tags=["legacy"])


class AnalyzeRequest(BaseModel):
    session_id: str
    code_path: str


class ChatRequest(BaseModel):
    code_path: str
    question: str
    focused_file: str | None = None


@legacy_router.post("/analyze", response_model=ApiResponse[dict])
async def start_analysis(body: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    레거시 코드 경로를 받아 API 목록 분석을 시작합니다.
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


@legacy_router.get("/files", response_model=ApiResponse[dict])
async def list_files(path: str):
    """디렉토리 경로를 받아 파일 트리를 반환합니다."""
    root = FsPath(path)
    if not root.exists():
        raise HTTPException(status_code=404, detail="경로가 존재하지 않습니다.")
    if not root.is_dir():
        raise HTTPException(status_code=400, detail="디렉토리 경로를 입력하세요.")
    return ApiResponse.ok({"tree": _build_file_tree(root)})


@legacy_router.get("/file", response_model=ApiResponse[dict])
async def read_file(path: str):
    """파일 내용을 반환합니다."""
    file_path = FsPath(path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다.")
    if file_path.stat().st_size > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="파일이 너무 큽니다 (1MB 초과).")
    for enc in ("utf-8", "cp949", "latin-1"):
        try:
            content = file_path.read_text(encoding=enc)
            return ApiResponse.ok({"path": path, "content": content})
        except (UnicodeDecodeError, ValueError):
            continue
    raise HTTPException(status_code=415, detail="텍스트 파일만 지원합니다.")


@legacy_router.post("/chat", response_model=ApiResponse[dict])
async def chat(body: ChatRequest):
    """
    소스코드에 대해 직접 질문합니다.
    사전 분석 없이 code_path와 question만 있으면 사용할 수 있습니다.
    """
    if not body.code_path.strip():
        raise HTTPException(status_code=400, detail="code_path는 필수입니다.")

    answer = await chat_with_legacy_code(body.code_path, body.question, body.focused_file)

    return ApiResponse.ok({
        "code_path": body.code_path,
        "answer": answer,
    })
