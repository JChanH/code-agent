"""Unit tests for the development orchestrator (orchestrator.py).

Covers:
- Early exit when task / project not found
- Successful completion on the first attempt
- Retry logic when review fails, then passes
- Max-retries exceeded → task marked failed
- code_agent exception → task marked failed
- review_agent exception → task marked failed
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import app.agents.orchestrator  # ensures module is loaded before patch() resolves it
from app.agents.review_agent import ReviewResult


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_task(task_id: str = "task-001", project_id: str = "proj-001") -> MagicMock:
    task = MagicMock()
    task.id = task_id
    task.project_id = project_id
    task.title = "Implement feature X"
    task.status = "confirmed"
    task.started_at = None
    task.git_commit_hash = None
    return task


def _make_project(project_id: str = "proj-001") -> MagicMock:
    project = MagicMock()
    project.id = project_id
    project.local_repo_path = "/tmp/repo"
    return project


@asynccontextmanager
async def _noop_transaction(*args, **kwargs):
    """Async context manager that yields a no-op session mock."""
    session = AsyncMock()
    yield session


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestRunTaskInner:

    async def test_task_not_found_returns_early(self):
        """Should log and return early without touching any other dependency."""
        with patch("app.agents.orchestrator.task_repository") as mock_task_repo:
            mock_task_repo.find_by_id = AsyncMock(return_value=None)

            from app.agents.orchestrator import _run_task_inner

            await _run_task_inner("nonexistent-id")

            mock_task_repo.find_by_id.assert_called_once_with("nonexistent-id")

    async def test_project_not_found_returns_early(self):
        """Should log and return early when the task's project is missing."""
        task = _make_task()

        with (
            patch("app.agents.orchestrator.task_repository") as mock_task_repo,
            patch("app.agents.orchestrator.project_repository") as mock_proj_repo,
        ):
            mock_task_repo.find_by_id = AsyncMock(return_value=task)
            mock_proj_repo.find_by_id = AsyncMock(return_value=None)

            from app.agents.orchestrator import _run_task_inner

            await _run_task_inner(task.id)

            mock_proj_repo.find_by_id.assert_called_once_with(task.project_id)

    async def test_success_on_first_attempt(self):
        """Task should reach 'done' when code_agent and review_agent both pass."""
        task = _make_task()
        project = _make_project()
        passed_result = ReviewResult(
            passed=True,
            test_output="All tests passed.",
            overall_feedback="",
        )

        with (
            patch("app.agents.orchestrator.task_repository") as mock_task_repo,
            patch("app.agents.orchestrator.project_repository") as mock_proj_repo,
            patch("app.agents.orchestrator._update_task_status", new_callable=AsyncMock) as mock_update,
            patch("app.agents.orchestrator.ws_manager") as mock_ws,
            patch("app.agents.orchestrator.run_code_agent", new_callable=AsyncMock),
            patch("app.agents.orchestrator.run_review_agent", return_value=passed_result),
            patch("app.agents.orchestrator.GitService") as mock_git_cls,
            patch("app.agents.orchestrator.db_conn") as mock_db,
        ):
            mock_task_repo.find_by_id = AsyncMock(return_value=task)
            mock_proj_repo.find_by_id = AsyncMock(return_value=project)
            mock_ws.broadcast = AsyncMock()
            mock_db.transaction = _noop_transaction

            git_svc = MagicMock()
            git_svc.has_staged_changes.return_value = True
            git_svc.commit.return_value = "abc1234"
            mock_git_cls.return_value = git_svc

            from app.agents.orchestrator import _run_task_inner

            await _run_task_inner(task.id)

            status_calls = [c.args[1] for c in mock_update.call_args_list]
            assert "coding" in status_calls
            assert "reviewing" in status_calls
            # Final _update_task_status calls should NOT include "failed"
            assert "failed" not in status_calls

    async def test_review_fails_then_retries_and_passes(self):
        """Task should retry and succeed on the second attempt after one review failure."""
        task = _make_task()
        project = _make_project()
        fail_result = ReviewResult(
            passed=False,
            test_output="1 test failed.",
            overall_feedback="Fix the edge case.",
        )
        pass_result = ReviewResult(
            passed=True,
            test_output="All tests passed.",
            overall_feedback="",
        )

        with (
            patch("app.agents.orchestrator.task_repository") as mock_task_repo,
            patch("app.agents.orchestrator.project_repository") as mock_proj_repo,
            patch("app.agents.orchestrator._update_task_status", new_callable=AsyncMock),
            patch("app.agents.orchestrator.ws_manager") as mock_ws,
            patch("app.agents.orchestrator.run_code_agent", new_callable=AsyncMock) as mock_code,
            patch("app.agents.orchestrator.run_review_agent", new_callable=AsyncMock) as mock_review,
            patch("app.agents.orchestrator.GitService") as mock_git_cls,
            patch("app.agents.orchestrator.db_conn") as mock_db,
        ):
            mock_task_repo.find_by_id = AsyncMock(return_value=task)
            mock_proj_repo.find_by_id = AsyncMock(return_value=project)
            mock_ws.broadcast = AsyncMock()
            mock_db.transaction = _noop_transaction

            # Fail on attempt 1, pass on attempt 2
            mock_review.side_effect = [fail_result, pass_result]

            git_svc = MagicMock()
            git_svc.has_staged_changes.return_value = False
            mock_git_cls.return_value = git_svc

            from app.agents.orchestrator import _run_task_inner

            await _run_task_inner(task.id)

            # code_agent must have been called twice
            assert mock_code.call_count == 2

            # The second call should carry the review feedback from attempt 1
            _, second_kwargs = mock_code.call_args_list[1]
            review_ctx = second_kwargs.get("review_context")
            assert review_ctx is not None
            assert review_ctx["attempt"] == 1
            assert review_ctx["overall_feedback"] == "Fix the edge case."

    async def test_max_retries_exceeded_marks_task_failed(self):
        """Task should be marked 'failed' after all retry attempts are exhausted."""
        task = _make_task()
        project = _make_project()
        fail_result = ReviewResult(
            passed=False,
            test_output="Tests failed.",
            overall_feedback="Still broken.",
        )

        with (
            patch("app.agents.orchestrator.task_repository") as mock_task_repo,
            patch("app.agents.orchestrator.project_repository") as mock_proj_repo,
            patch("app.agents.orchestrator._update_task_status", new_callable=AsyncMock) as mock_update,
            patch("app.agents.orchestrator.ws_manager") as mock_ws,
            patch("app.agents.orchestrator.run_code_agent", new_callable=AsyncMock) as mock_code,
            patch("app.agents.orchestrator.run_review_agent", return_value=fail_result),
            patch("app.agents.orchestrator.db_conn") as mock_db,
        ):
            mock_task_repo.find_by_id = AsyncMock(return_value=task)
            mock_proj_repo.find_by_id = AsyncMock(return_value=project)
            mock_ws.broadcast = AsyncMock()
            mock_db.transaction = _noop_transaction

            from app.agents.orchestrator import _run_task_inner, MAX_RETRIES

            await _run_task_inner(task.id)

            # code_agent should have been called MAX_RETRIES times
            assert mock_code.call_count == MAX_RETRIES

            # Final status update must be "failed"
            last_status = mock_update.call_args_list[-1].args[1]
            assert last_status == "failed"

    async def test_code_agent_exception_marks_task_failed(self):
        """Task should be marked 'failed' immediately when code_agent raises an exception."""
        task = _make_task()
        project = _make_project()

        with (
            patch("app.agents.orchestrator.task_repository") as mock_task_repo,
            patch("app.agents.orchestrator.project_repository") as mock_proj_repo,
            patch("app.agents.orchestrator._update_task_status", new_callable=AsyncMock) as mock_update,
            patch("app.agents.orchestrator.ws_manager") as mock_ws,
            patch(
                "app.agents.orchestrator.run_code_agent",
                new_callable=AsyncMock,
                side_effect=RuntimeError("agent crashed"),
            ),
            patch("app.agents.orchestrator.db_conn") as mock_db,
        ):
            mock_task_repo.find_by_id = AsyncMock(return_value=task)
            mock_proj_repo.find_by_id = AsyncMock(return_value=project)
            mock_ws.broadcast = AsyncMock()
            mock_db.transaction = _noop_transaction

            from app.agents.orchestrator import _run_task_inner

            await _run_task_inner(task.id)

            status_calls = [c.args[1] for c in mock_update.call_args_list]
            assert "failed" in status_calls

    async def test_review_agent_exception_marks_task_failed(self):
        """Task should be marked 'failed' immediately when review_agent raises an exception."""
        task = _make_task()
        project = _make_project()

        with (
            patch("app.agents.orchestrator.task_repository") as mock_task_repo,
            patch("app.agents.orchestrator.project_repository") as mock_proj_repo,
            patch("app.agents.orchestrator._update_task_status", new_callable=AsyncMock) as mock_update,
            patch("app.agents.orchestrator.ws_manager") as mock_ws,
            patch("app.agents.orchestrator.run_code_agent", new_callable=AsyncMock),
            patch(
                "app.agents.orchestrator.run_review_agent",
                new_callable=AsyncMock,
                side_effect=RuntimeError("review crashed"),
            ),
            patch("app.agents.orchestrator.db_conn") as mock_db,
        ):
            mock_task_repo.find_by_id = AsyncMock(return_value=task)
            mock_proj_repo.find_by_id = AsyncMock(return_value=project)
            mock_ws.broadcast = AsyncMock()
            mock_db.transaction = _noop_transaction

            from app.agents.orchestrator import _run_task_inner

            await _run_task_inner(task.id)

            status_calls = [c.args[1] for c in mock_update.call_args_list]
            assert "failed" in status_calls
