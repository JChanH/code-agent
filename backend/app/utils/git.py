"""Git operations service."""

import subprocess
import os


class GitService:
    """Git operations for the Git Management tab."""

    def __init__(self, worktree_path: str):
        self.worktree_path = worktree_path
        if not os.path.isdir(worktree_path):
            raise ValueError(f"Worktree path does not exist: {worktree_path}")

    def _run(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command in the worktree directory."""
        return subprocess.run(
            ["git"] + args,
            cwd=self.worktree_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=check,
        )

    def get_status(self) -> list[dict]:
        """Return list of changed files (git status --porcelain)."""
        result = self._run(["status", "--porcelain"])
        files = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                status_code = line[:2].strip()
                file_path = line[3:]
                files.append({"status": status_code, "path": file_path})
        return files

    def get_diff(self, file_path: str, staged: bool = False) -> str:
        """Return the diff for a specific file."""
        args = ["diff"]
        if staged:
            args.append("--staged")
        args.append("--")
        args.append(file_path)
        result = self._run(args, check=False)
        return result.stdout

    def stage_files(self, file_paths: list[str]) -> None:
        """Stage selected files."""
        self._run(["add"] + file_paths)

    def stage_all(self) -> None:
        """Stage all changed files."""
        self._run(["add", "."])

    def unstage_files(self, file_paths: list[str]) -> None:
        """Unstage selected files."""
        self._run(["reset", "HEAD", "--"] + file_paths)

    def commit(self, message: str) -> str:
        """Commit staged changes. Returns the commit hash."""
        self._run([
            "-c", "user.email=agent@code-agent.local",
            "-c", "user.name=Code Agent",
            "commit", "-m", message,
        ])
        result = self._run(["rev-parse", "HEAD"])
        return result.stdout.strip()

    def has_staged_changes(self) -> bool:
        """Return True if there are staged changes ready to commit."""
        result = self._run(["diff", "--cached", "--quiet"], check=False)
        return result.returncode != 0

    def pull(self, remote: str = "origin", branch: str = "main",
             strategy: str = "rebase") -> str:
        """Pull changes from remote. Returns output."""
        args = ["pull", remote, branch]
        if strategy == "rebase":
            args.append("--rebase")
        result = self._run(args, check=False)
        return result.stdout + result.stderr

    def push(self) -> str:
        """Push current branch to origin. Returns output."""
        result = self._run(["push", "-u", "origin", "HEAD"], check=False)
        return result.stdout + result.stderr

    def get_log(self, count: int = 20) -> list[dict]:
        """Return recent commit log entries."""
        result = self._run([
            "log", f"--max-count={count}",
            "--format=%H|%h|%s|%an|%ar",
        ])
        logs = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|", 4)
                if len(parts) == 5:
                    logs.append({
                        "hash": parts[0],
                        "short_hash": parts[1],
                        "message": parts[2],
                        "author": parts[3],
                        "relative_date": parts[4],
                    })
        return logs

    def revert_file(self, file_path: str) -> None:
        """Discard changes to a specific file."""
        self._run(["checkout", "--", file_path])

    def get_current_branch(self) -> str:
        """Return the current branch name."""
        result = self._run(["branch", "--show-current"])
        return result.stdout.strip()

    def get_commit_diff(self, commit_hash: str) -> str:
        """Return the full diff for a specific commit."""
        result = self._run(["diff", f"{commit_hash}~1", commit_hash], check=False)
        return result.stdout

    def get_commit_files(self, commit_hash: str) -> list[dict]:
        """Return list of files changed in a specific commit."""
        result = self._run(
            ["diff-tree", "--no-commit-id", "-r", "--name-status", commit_hash],
            check=False,
        )
        files = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    files.append({"status": parts[0].strip(), "path": parts[1].strip()})
        return files

    def revert_commit(self, commit_hash: str) -> str:
        """Create a revert commit for the given hash. Returns new commit hash."""
        self._run(["revert", commit_hash, "--no-edit"])
        result = self._run(["rev-parse", "HEAD"])
        return result.stdout.strip()
