"""Git management request/response schemas."""

from pydantic import BaseModel


class GitFileStatus(BaseModel):
    status: str
    path: str


class GitCommitRequest(BaseModel):
    message: str


class GitStageRequest(BaseModel):
    file_paths: list[str]


class GitPullRequest(BaseModel):
    strategy: str = "rebase"


class GitLogEntry(BaseModel):
    hash: str
    short_hash: str
    message: str
    author: str
    relative_date: str
