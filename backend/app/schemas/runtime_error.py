"""Pydantic schemas for runtime error API."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel

RuntimeErrorStatus = Literal["pending", "analyzing", "analyzed", "resolved", "ignored"]


class RuntimeErrorResponse(BaseModel):
    id: str
    error_code: str
    message: str
    project_id: str
    level: str
    error_timestamp: Optional[datetime] = None
    metadata: Optional[Any] = None
    fix_suggestion: Optional[str] = None
    status: RuntimeErrorStatus = "pending"
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        if hasattr(obj, "metadata_"):
            data = {
                "id": obj.id,
                "error_code": obj.error_code,
                "message": obj.message,
                "project_id": obj.project_id,
                "level": obj.level,
                "error_timestamp": obj.error_timestamp,
                "metadata": obj.metadata_,
                "fix_suggestion": obj.fix_suggestion,
                "status": obj.status,
                "created_at": obj.created_at,
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)


class RuntimeErrorStatusUpdate(BaseModel):
    status: RuntimeErrorStatus


class RuntimeErrorListResponse(BaseModel):
    items: list[RuntimeErrorResponse]
    total: int
    limit: int
    offset: int
