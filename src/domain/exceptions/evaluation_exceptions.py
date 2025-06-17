"""Evaluation-related domain exceptions"""


class EvaluationError(Exception):
    """평가 관련 기본 예외"""

    pass


class InvalidEvaluationDataError(EvaluationError):
    """평가 데이터가 유효하지 않을 때 발생하는 예외"""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


class EvaluationTimeoutError(EvaluationError):
    """평가 시간 초과 시 발생하는 예외"""

    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Evaluation timed out after {timeout_seconds} seconds")


class LLMConnectionError(EvaluationError):
    """LLM 연결 오류 시 발생하는 예외"""

    def __init__(self, message: str, error_code: str | None = None):
        self.error_code = error_code
        super().__init__(message)


class InvalidDataFormatError(EvaluationError):
    """데이터 형식이 잘못되었을 때 발생하는 예외"""

    def __init__(self, message: str, file_path: str | None = None, line_number: int | None = None):
        self.file_path = file_path
        self.line_number = line_number
        super().__init__(message)


class DataValidationError(EvaluationError):
    """데이터 내용 검증 실패 시 발생하는 예외"""

    def __init__(self, message: str, validation_issues: list[dict] | None = None):
        self.validation_issues = validation_issues or []
        super().__init__(message)


class APIFailureError(EvaluationError):
    """API 호출 실패 시 발생하는 예외"""

    def __init__(self, message: str, failed_count: int = 0, total_count: int = 0, 
                 api_type: str = "Unknown"):
        self.failed_count = failed_count
        self.total_count = total_count
        self.api_type = api_type
        super().__init__(message)
