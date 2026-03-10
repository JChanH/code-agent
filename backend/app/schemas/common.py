from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')


class ErrorDetail(BaseModel):
    message: str
    code: str
    path: Optional[str] = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    
    @classmethod
    def ok(cls, data: T):
        return cls(
            success=True,
            data=data
        )

    @classmethod
    def fail(cls, message: str, code: str, path: str = None):
        return cls(
            success=False,
            error=ErrorDetail(message=message, code=code, path=path)
        )
