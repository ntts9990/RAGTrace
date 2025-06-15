"""Evaluation-related domain exceptions"""


class EvaluationError(Exception):
    """평가 관련 기본 예외"""
    pass


class InvalidEvaluationDataError(EvaluationError):
    """평가 데이터가 유효하지 않을 때 발생하는 예외"""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message)


class EvaluationTimeoutError(EvaluationError):
    """평가 시간 초과 시 발생하는 예외"""
    
    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Evaluation timed out after {timeout_seconds} seconds")


class LLMConnectionError(EvaluationError):
    """LLM 연결 오류 시 발생하는 예외"""
    
    def __init__(self, message: str, error_code: str = None):
        self.error_code = error_code
        super().__init__(message)