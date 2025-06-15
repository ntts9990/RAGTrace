import pytest
from src.domain.exceptions.evaluation_exceptions import (
    EvaluationError, 
    InvalidEvaluationDataError, 
    EvaluationTimeoutError, 
    LLMConnectionError
)

def test_evaluation_error_can_be_raised():
    """EvaluationError가 기본 예외로 잘 동작하는지 테스트합니다."""
    with pytest.raises(EvaluationError, match="A standard evaluation error"):
        raise EvaluationError("A standard evaluation error")

def test_invalid_evaluation_data_error():
    """InvalidEvaluationDataError가 메시지와 필드 정보를 포함하는지 테스트합니다."""
    with pytest.raises(InvalidEvaluationDataError) as excinfo:
        raise InvalidEvaluationDataError("Question is empty", field="question")
    
    assert excinfo.value.field == "question"
    assert "Question is empty" in str(excinfo.value)

def test_evaluation_timeout_error():
    """EvaluationTimeoutError가 시간 초과 정보를 포함하는지 테스트합니다."""
    with pytest.raises(EvaluationTimeoutError) as excinfo:
        raise EvaluationTimeoutError(timeout_seconds=60)
        
    assert excinfo.value.timeout_seconds == 60
    assert "timed out after 60 seconds" in str(excinfo.value)

def test_llm_connection_error():
    """LLMConnectionError가 메시지와 에러 코드 정보를 포함하는지 테스트합니다."""
    with pytest.raises(LLMConnectionError) as excinfo:
        raise LLMConnectionError("Connection failed", error_code="503")

    assert excinfo.value.error_code == "503"
    assert "Connection failed" in str(excinfo.value)

def test_exceptions_inherit_from_evaluation_error():
    """모든 커스텀 예외가 EvaluationError를 상속하는지 테스트합니다."""
    assert issubclass(InvalidEvaluationDataError, EvaluationError)
    assert issubclass(EvaluationTimeoutError, EvaluationError)
    assert issubclass(LLMConnectionError, EvaluationError) 