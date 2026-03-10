"""커스텀 비즈니스 예외 클래스 정의."""


class BusinessException(Exception):
    """비즈니스 로직 예외 기본 클래스."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# ---------------------------
# 공통 HTTP 의미 Exceptions
# ---------------------------
class NotFoundException(BusinessException):
    """리소스를 찾을 수 없을 때."""

    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class ConflictException(BusinessException):
    """리소스 충돌 (이미 존재) 시."""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)


# ---------------------------
# 메인 기능 Exceptions
# ---------------------------




