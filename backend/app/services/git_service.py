"""Git 서비스 레이어 — 프로젝트 경로 조회 및 Git 명령 위임."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.business import NotFoundException
from app.utils.git import GitService
from app.repositories import project_repository


async def get_git_service(project_id: str, session: AsyncSession) -> GitService:
    """프로젝트의 로컬 저장소 경로를 조회하고 GitService 인스턴스를 반환한다."""
    project = await project_repository.find_by_id(project_id, session)
    if not project:
        raise NotFoundException("Project not found")
    return GitService(project.local_repo_path)


async def get_status(project_id: str, session: AsyncSession) -> list[dict]:
    svc = await get_git_service(project_id, session)
    return svc.get_status()


async def get_diff(project_id: str, file_path: str, staged: bool, session: AsyncSession) -> dict:
    svc = await get_git_service(project_id, session)
    return {"diff": svc.get_diff(file_path, staged=staged)}


async def stage_files(project_id: str, file_paths: list[str], session: AsyncSession) -> dict:
    svc = await get_git_service(project_id, session)
    svc.stage_files(file_paths)
    return {"message": "Files staged", "files": file_paths}


async def commit(project_id: str, message: str, session: AsyncSession) -> dict:
    svc = await get_git_service(project_id, session)
    commit_hash = svc.commit(message)
    return {"message": "Committed", "hash": commit_hash}


async def pull(project_id: str, strategy: str, session: AsyncSession) -> dict:
    svc = await get_git_service(project_id, session)
    output = svc.pull(strategy=strategy)
    return {"message": "Pull completed", "output": output}


async def push(project_id: str, session: AsyncSession) -> dict:
    svc = await get_git_service(project_id, session)
    output = svc.push()
    return {"message": "Push completed", "output": output}


async def get_log(project_id: str, count: int, session: AsyncSession) -> list[dict]:
    svc = await get_git_service(project_id, session)
    return svc.get_log(count=count)


async def revert_file(project_id: str, file_path: str, session: AsyncSession) -> dict:
    svc = await get_git_service(project_id, session)
    svc.revert_file(file_path)
    return {"message": f"Reverted: {file_path}"}


async def get_current_branch(project_id: str, session: AsyncSession) -> dict:
    svc = await get_git_service(project_id, session)
    return {"branch": svc.get_current_branch()}
