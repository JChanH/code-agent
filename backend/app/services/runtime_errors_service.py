"""Runtime errors service — business logic layer."""

from app.models.runtime_error import RuntimeErrorRecord
from app.repositories import runtime_error_repository


async def list_errors_by_project(
    project_id: str, limit: int = 50, offset: int = 0
) -> tuple[list[RuntimeErrorRecord], int]:
    records = await runtime_error_repository.find_by_project(project_id, limit, offset)
    total = await runtime_error_repository.count_by_project(project_id)
    return records, total


async def list_all_errors(
    limit: int = 50, offset: int = 0
) -> tuple[list[RuntimeErrorRecord], int]:
    records = await runtime_error_repository.find_all(limit, offset)
    total = await runtime_error_repository.count_all()
    return records, total
