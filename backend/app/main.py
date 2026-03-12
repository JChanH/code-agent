"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import (
    agent_router,
    git_router,
    project_specs_router,
    project_tasks_router,
    project_worktrees_router,
    projects_router,
    specs_router,
    tasks_router,
    users_router,
    worktrees_router,
)
from app.websocket import ws_manager
from app.exceptions.business import BusinessException
from app.exceptions.handlers import (
    business_exception_handler,
    global_exception_handler,
    validation_exception_handler,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""

    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# ── Exception handlers ───────────────────────
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# CORS — allow Electron renderer (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ─────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "ws_connections": ws_manager.connection_count,
    }


# ── REST API routers ─────────────────────────
app.include_router(projects_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(project_worktrees_router, prefix="/api")
app.include_router(worktrees_router, prefix="/api")
app.include_router(project_tasks_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(project_specs_router, prefix="/api")
app.include_router(specs_router, prefix="/api")
app.include_router(git_router, prefix="/api")
app.include_router(agent_router, prefix="/api")


# ── WebSocket endpoint ───────────────────────
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await ws_manager.connect(websocket, project_id)
    try:
        while True:
            # Keep connection alive; handle incoming messages if needed
            data = await websocket.receive_text()
            # For now, echo back; agent broadcasts are one-way
            await ws_manager.send_to(websocket, {"type": "ack", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, project_id)