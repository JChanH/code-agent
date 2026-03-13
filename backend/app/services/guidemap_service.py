"""Guidemap 서비스 — 기존 프로젝트 코드베이스 분석 및 guidemap 생성."""

import logging

from app.exceptions.business import NotFoundException
from app.repositories import project_repository
from app.agents.guidemap_agent import generate_guidemap

logger = logging.getLogger(__name__)


async def trigger_guidemap_generation(project_id: str) -> None:
    """프로젝트를 조회한 뒤 guidemap 에이전트를 실행합니다.
    existing 프로젝트에만 적용되며, local_repo_path가 없으면 스킵합니다.
    """
    project = await project_repository.find_by_id(project_id)
    if not project:
        raise NotFoundException("Project not found")
    if project.project_type != "existing":
        logger.info("Skipping guidemap generation for non-existing project: %s", project_id)
        return
    if not project.local_repo_path:
        logger.warning("Skipping guidemap generation: no local_repo_path for project %s", project_id)
        return
    await generate_guidemap(project)
