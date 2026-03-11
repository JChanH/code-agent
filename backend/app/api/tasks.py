"""Task API router."""

from fastapi import APIRouter

from app.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.schemas.common import ApiResponse
from app.services import tasks_service

# GET /api/projects/{project_id}/tasks, POST /api/projects/{project_id}/tasks
project_tasks_router = APIRouter(
    prefix="/projects/{project_id}/tasks",
    tags=["tasks"],
)

# GET /api/tasks/{task_id}, PATCH /api/tasks/{task_id}, DELETE /api/tasks/{task_id}
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@project_tasks_router.get("", response_model=ApiResponse[list[TaskResponse]])
async def list_tasks(project_id: str):
    return ApiResponse.ok(await tasks_service.list_tasks(project_id))


@project_tasks_router.post("", response_model=ApiResponse[TaskResponse], status_code=201)
async def create_task(project_id: str, body: TaskCreate):
    return ApiResponse.ok(await tasks_service.create_task(project_id, body))


@tasks_router.get("/{task_id}", response_model=ApiResponse[TaskResponse])
async def get_task(task_id: str):
    return ApiResponse.ok(await tasks_service.get_task(task_id))


@tasks_router.patch("/{task_id}", response_model=ApiResponse[TaskResponse])
async def update_task(task_id: str, body: TaskUpdate):
    return ApiResponse.ok(await tasks_service.update_task(task_id, body))


@tasks_router.delete("/{task_id}", response_model=ApiResponse[None])
async def delete_task(task_id: str):
    await tasks_service.delete_task(task_id)
    return ApiResponse.ok(None)
