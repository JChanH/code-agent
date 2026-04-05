"""Unit tests for the design agent (design_agent.py).

Covers:
- _get_stack_context: all project type / stack combinations
- _load_spec_content: raw content, file path, docx, missing file, no content
- analyze_spec_and_create_tasks: spec/project not found, success, agent failure
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import app.agents.design_agent


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_project(**kwargs) -> MagicMock:
    project = MagicMock()
    project.id = kwargs.get("id", "proj-001")
    project.name = kwargs.get("name", "my-project")
    project.project_stack = kwargs.get("project_stack", "python")
    project.framework = kwargs.get("framework", "fastapi")
    project.project_type = kwargs.get("project_type", "new")
    project.local_repo_path = kwargs.get("local_repo_path", "/tmp/my-project")
    project.repo_url = kwargs.get("repo_url", None)
    return project


def _make_spec(**kwargs) -> MagicMock:
    spec = MagicMock()
    spec.id = kwargs.get("id", "spec-001")
    spec.project_id = kwargs.get("project_id", "proj-001")
    spec.raw_content = kwargs.get("raw_content", None)
    spec.source_path = kwargs.get("source_path", None)
    return spec


# ── _get_stack_context ─────────────────────────────────────────────────────────

class TestGetStackContext:

    def test_new_fastapi_project_includes_summary(self):
        """New FastAPI projects should receive the fastapi_new_project.md summary."""
        project = _make_project(project_type="new", project_stack="python", framework="fastapi")

        with patch("app.agents.design_agent.load_text", return_value="## Rules\n...") as mock_load:
            from app.agents.design_agent import _get_stack_context

            result = _get_stack_context(project)

            mock_load.assert_called_once_with("fastapi_new_project.md")
            assert "new FastAPI project" in result

    def test_existing_fastapi_with_guidemap_includes_design_context(self):
        """Existing FastAPI projects with a guidemap should receive project-specific context."""
        project = _make_project(project_type="existing", project_stack="python", framework="fastapi")

        with (
            patch("app.agents.design_agent.guidemap_exists", return_value=True),
            patch("app.agents.design_agent.get_guidemap_context", return_value="# Guidelines\n...") as mock_ctx,
        ):
            from app.agents.design_agent import _get_stack_context

            result = _get_stack_context(project)

            mock_ctx.assert_called_once_with(project.name)
            assert "existing FastAPI project" in result
            assert "# Guidelines" in result

    def test_existing_fastapi_without_guidemap_uses_defaults(self):
        """Existing FastAPI projects without a guidemap should fall back to default conventions."""
        project = _make_project(project_type="existing", project_stack="python", framework="fastapi")

        with patch("app.agents.design_agent.guidemap_exists", return_value=False):
            from app.agents.design_agent import _get_stack_context

            result = _get_stack_context(project)

            assert "router → service → repository" in result

    def test_java_project_returns_java_context(self):
        """Java projects should receive Java-specific guidance."""
        project = _make_project(project_stack="java", framework=None)

        from app.agents.design_agent import _get_stack_context

        result = _get_stack_context(project)

        assert "java" in result.lower() or "package" in result.lower()

    def test_unknown_stack_returns_empty_string(self):
        """Projects with an unsupported stack should receive an empty context string."""
        project = _make_project(project_stack="other", framework=None)

        from app.agents.design_agent import _get_stack_context

        result = _get_stack_context(project)

        assert result == ""


# ── _load_spec_content ─────────────────────────────────────────────────────────

class TestLoadSpecContent:

    async def test_returns_raw_content_when_available(self):
        """Should return raw_content directly without touching the filesystem."""
        spec = _make_spec(raw_content="User story: as a user...")

        from app.agents.design_agent import _load_spec_content

        result = await _load_spec_content(spec)

        assert result == "User story: as a user..."

    async def test_reads_plain_text_file(self, tmp_path: Path):
        """Should read and return the contents of a plain text spec file."""
        content = "# Spec\nBuild a REST API."
        spec_file = tmp_path / "spec.txt"
        spec_file.write_text(content, encoding="utf-8")

        spec = _make_spec(raw_content=None, source_path=str(spec_file))

        from app.agents.design_agent import _load_spec_content

        result = await _load_spec_content(spec)

        assert result == content

    async def test_returns_error_message_for_missing_file(self):
        """Should return a descriptive error string when the file cannot be read."""
        spec = _make_spec(raw_content=None, source_path="/nonexistent/path/spec.txt")

        from app.agents.design_agent import _load_spec_content

        result = await _load_spec_content(spec)

        assert "[File read error:" in result

    async def test_returns_placeholder_when_no_content(self):
        """Should return a placeholder when neither raw_content nor source_path is set."""
        spec = _make_spec(raw_content=None, source_path=None)

        from app.agents.design_agent import _load_spec_content

        result = await _load_spec_content(spec)

        assert result == "[No spec content]"

    async def test_reads_docx_via_extract_helper(self):
        """Should delegate .docx files to _extract_docx_text."""
        spec = _make_spec(raw_content=None, source_path="/docs/spec.docx")

        with patch(
            "app.agents.design_agent._extract_docx_text",
            return_value="Extracted paragraph.",
        ) as mock_extract:
            from app.agents.design_agent import _load_spec_content

            result = await _load_spec_content(spec)

            mock_extract.assert_called_once_with(spec.source_path)
            assert result == "Extracted paragraph."


# ── analyze_spec_and_create_tasks ──────────────────────────────────────────────

class TestAnalyzeSpecAndCreateTasks:

    async def test_spec_not_found_returns_early(self):
        """Should log and return early when the spec does not exist."""
        with patch("app.agents.design_agent.spec_repository") as mock_spec_repo:
            mock_spec_repo.find_by_id = AsyncMock(return_value=None)

            from app.agents.design_agent import analyze_spec_and_create_tasks

            await analyze_spec_and_create_tasks("nonexistent-spec-id")

            mock_spec_repo.find_by_id.assert_called_once_with("nonexistent-spec-id")

    async def test_project_not_found_returns_early(self):
        """Should log and return early when the spec's project does not exist."""
        spec = _make_spec()

        with (
            patch("app.agents.design_agent.spec_repository") as mock_spec_repo,
            patch("app.agents.design_agent.project_repository") as mock_proj_repo,
        ):
            mock_spec_repo.find_by_id = AsyncMock(return_value=spec)
            mock_proj_repo.find_by_id = AsyncMock(return_value=None)

            from app.agents.design_agent import analyze_spec_and_create_tasks

            await analyze_spec_and_create_tasks(spec.id)

            mock_proj_repo.find_by_id.assert_called_once_with(spec.project_id)

    async def test_success_saves_tasks_and_broadcasts(self):
        """Should save tasks and broadcast spec_analyzed on a successful agent run."""
        spec = _make_spec(raw_content="Build a TODO API.")
        project = _make_project(project_type="new")

        agent_output = {
            "tasks": [
                {
                    "title": "POST /todos",
                    "description": "Create a new todo item",
                    "acceptance_criteria": ["POST /todos with valid body → 201 + todo object"],
                    "implementation_steps": [
                        "Read app/api/ to understand router pattern",
                        "Add POST /todos router in app/api/todos.py",
                        "Add TodoRepository.create in app/repositories/todo_repository.py",
                    ],
                }
            ],
        }

        mock_message = MagicMock()
        mock_message.structured_output = agent_output
        mock_message.result = None

        async def mock_query(*args, **kwargs):
            yield mock_message

        saved_task = MagicMock(
            id="task-001",
            project_id=project.id,
            spec_id=spec.id,
            title="POST /todos",
            description="Create a new todo item",
            status="plan_reviewing",
        )

        mock_broadcast = AsyncMock()

        with (
            patch("app.agents.design_agent.spec_repository") as mock_spec_repo,
            patch("app.agents.design_agent.project_repository") as mock_proj_repo,
            patch("app.agents.design_agent._update_spec_status", new_callable=AsyncMock),
            patch("app.agents.design_agent.make_broadcaster", return_value=mock_broadcast),
            patch("app.agents.design_agent.query", new=mock_query),
            patch("app.agents.design_agent._save_tasks", new_callable=AsyncMock, return_value=[saved_task]),
            patch("app.agents.design_agent._build_prompt", return_value="test prompt"),
            patch("app.agents.design_agent._load_spec_content", new_callable=AsyncMock, return_value="Build a TODO API."),
        ):
            mock_spec_repo.find_by_id = AsyncMock(return_value=spec)
            mock_proj_repo.find_by_id = AsyncMock(return_value=project)

            from app.agents.design_agent import analyze_spec_and_create_tasks

            await analyze_spec_and_create_tasks(spec.id)

            # 마지막 broadcast가 spec_analyzed이고 tasks를 포함해야 함
            all_broadcast_args = [call.args[0] for call in mock_broadcast.call_args_list]
            spec_analyzed_msg = next(m for m in all_broadcast_args if m.get("type") == "spec_analyzed")
            assert len(spec_analyzed_msg["tasks"]) == 1
            assert spec_analyzed_msg["tasks"][0]["title"] == "POST /todos"

    async def test_agent_failure_reverts_spec_status_to_uploaded(self):
        """Should revert spec status to 'uploaded' and broadcast failure when agent raises."""
        spec = _make_spec(raw_content="Build something.")
        project = _make_project()

        async def mock_query_error(**_):
            if False:
                yield
            raise RuntimeError("Claude API unreachable")

        mock_broadcast = AsyncMock()

        with (
            patch("app.agents.design_agent.spec_repository") as mock_spec_repo,
            patch("app.agents.design_agent.project_repository") as mock_proj_repo,
            patch("app.agents.design_agent._update_spec_status", new_callable=AsyncMock) as mock_update_status,
            patch("app.agents.design_agent.make_broadcaster", return_value=mock_broadcast),
            patch("app.agents.design_agent.query", new=mock_query_error),
            patch("app.agents.design_agent._build_prompt", return_value="test prompt"),
            patch("app.agents.design_agent._load_spec_content", new_callable=AsyncMock, return_value="Build something."),
        ):
            mock_spec_repo.find_by_id = AsyncMock(return_value=spec)
            mock_proj_repo.find_by_id = AsyncMock(return_value=project)

            from app.agents.design_agent import analyze_spec_and_create_tasks

            await analyze_spec_and_create_tasks(spec.id)

            status_calls = [c.args[1] for c in mock_update_status.call_args_list]
            assert "uploaded" in status_calls

            all_broadcast_args = [call.args[0] for call in mock_broadcast.call_args_list]
            broadcast_types = [m.get("type") for m in all_broadcast_args]
            assert "spec_analyze_failed" in broadcast_types

    async def test_agent_returns_no_result_reverts_spec_status(self):
        """Should revert spec status when agent completes without returning a parsed result."""
        spec = _make_spec(raw_content="Build something.")
        project = _make_project()

        mock_message = MagicMock()
        mock_message.structured_output = None
        mock_message.result = None

        async def mock_query_empty(*args, **kwargs):
            yield mock_message

        mock_broadcast = AsyncMock()

        with (
            patch("app.agents.design_agent.spec_repository") as mock_spec_repo,
            patch("app.agents.design_agent.project_repository") as mock_proj_repo,
            patch("app.agents.design_agent._update_spec_status", new_callable=AsyncMock) as mock_update_status,
            patch("app.agents.design_agent.make_broadcaster", return_value=mock_broadcast),
            patch("app.agents.design_agent.query", new=mock_query_empty),
            patch("app.agents.design_agent._build_prompt", return_value="test prompt"),
            patch("app.agents.design_agent._load_spec_content", new_callable=AsyncMock, return_value="Build something."),
        ):
            mock_spec_repo.find_by_id = AsyncMock(return_value=spec)
            mock_proj_repo.find_by_id = AsyncMock(return_value=project)

            from app.agents.design_agent import analyze_spec_and_create_tasks

            await analyze_spec_and_create_tasks(spec.id)

            status_calls = [c.args[1] for c in mock_update_status.call_args_list]
            assert "uploaded" in status_calls
