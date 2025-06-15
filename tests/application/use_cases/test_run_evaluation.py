import pytest
from unittest.mock import MagicMock
from datasets import Dataset

from src.application.use_cases import RunEvaluationUseCase
from src.domain import EvaluationData, EvaluationResult, EvaluationError

@pytest.fixture
def mock_ports():
    """유스케이스가 의존하는 포트들의 모의 객체를 생성합니다."""
    return {
        "llm_port": MagicMock(),
        "repository_port": MagicMock(),
        "evaluation_runner": MagicMock(),
    }

def test_run_evaluation_success(mock_ports):
    """평가 유스케이스가 성공적으로 실행되는 시나리오를 테스트합니다."""
    # Arrange: 모의 객체 설정
    mock_data = [EvaluationData("q", ["c"], "a", "g")]
    mock_ports["repository_port"].load_data.return_value = mock_data
    
    mock_llm = MagicMock()
    mock_ports["llm_port"].get_llm.return_value = mock_llm
    
    mock_result_dict = {
        "faithfulness": 1.0, "answer_relevancy": 1.0,
        "context_recall": 1.0, "context_precision": 1.0,
        "ragas_score": 1.0
    }
    mock_ports["evaluation_runner"].evaluate.return_value = mock_result_dict

    use_case = RunEvaluationUseCase(**mock_ports)

    # Act: 유스케이스 실행
    result = use_case.execute()

    # Assert: 결과 및 호출 확인
    assert isinstance(result, EvaluationResult)
    assert result.ragas_score == 1.0
    
    mock_ports["repository_port"].load_data.assert_called_once()
    mock_ports["llm_port"].get_llm.assert_called_once()
    
    # evaluate 메소드가 Dataset과 llm 객체로 호출되었는지 확인
    call_args, call_kwargs = mock_ports["evaluation_runner"].evaluate.call_args
    assert isinstance(call_kwargs.get("dataset"), Dataset)
    assert call_kwargs.get("llm") == mock_llm


def test_run_evaluation_no_data(mock_ports):
    """데이터가 없을 때 EvaluationError가 발생하는지 테스트합니다."""
    # Arrange
    mock_ports["repository_port"].load_data.return_value = []
    use_case = RunEvaluationUseCase(**mock_ports)

    # Act & Assert
    with pytest.raises(EvaluationError, match="평가 데이터가 없습니다."):
        use_case.execute()

def test_run_evaluation_runner_fails(mock_ports):
    """EvaluationRunner에서 예외 발생 시 EvaluationError로 래핑되는지 테스트합니다."""
    # Arrange
    mock_data = [EvaluationData("q", ["c"], "a", "g")]
    mock_ports["repository_port"].load_data.return_value = mock_data
    mock_ports["evaluation_runner"].evaluate.side_effect = Exception("Ragas API error")
    
    use_case = RunEvaluationUseCase(**mock_ports)
    
    # Act & Assert
    with pytest.raises(EvaluationError, match="평가 실행 중 오류 발생: Ragas API error"):
        use_case.execute() 