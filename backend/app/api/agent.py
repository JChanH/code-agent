"""Agent execution API router."""

from fastapi import APIRouter

agent_router = APIRouter(prefix="/agent", tags=["agent"])


@agent_router.post("/run/{task_id}")
async def run_agent(task_id: str):
    """Placeholder — will be implemented in Phase 3."""
    return {
        "status": "queued",
        "task_id": task_id,
        "message": "Agent execution will be implemented in Phase 3",
    }
