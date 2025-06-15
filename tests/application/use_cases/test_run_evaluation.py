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

def test_run_evaluation_missing_metric(mock_ports):
    """평가 결과에 필수 메트릭이 누락되었을 때 EvaluationError가 발생하는지 테스트합니다."""
    # Arrange
    mock_data = [EvaluationData("q", ["c"], "a", "g")]
    mock_ports["repository_port"].load_data.return_value = mock_data
    
    # "faithfulness"가 누락된 결과
    mock_result_dict = {
        "answer_relevancy": 1.0,
        "context_recall": 1.0, "context_precision": 1.0,
        "ragas_score": 1.0
    }
    mock_ports["evaluation_runner"].evaluate.return_value = mock_result_dict

    use_case = RunEvaluationUseCase(**mock_ports)

    # Act & Assert
    with pytest.raises(EvaluationError, match="필수 메트릭이 누락되었습니다: faithfulness"):
        use_case.execute()

def test_run_evaluation_all_scores_zero(mock_ports, capsys):
    """모든 평가 점수가 0일 때 경고 메시지가 출력되는지 테스트합니다."""
    # Arrange
    mock_data = [EvaluationData("q", ["c"], "a", "g")]
    mock_ports["repository_port"].load_data.return_value = mock_data
    
    mock_result_dict = {
        "faithfulness": 0.0, "answer_relevancy": 0.0,
        "context_recall": 0.0, "context_precision": 0.0,
        "ragas_score": 0.0
    }
    mock_ports["evaluation_runner"].evaluate.return_value = mock_result_dict

    use_case = RunEvaluationUseCase(**mock_ports)

    # Act
    use_case.execute()

    # Assert
    captured = capsys.readouterr()
    assert "경고: 모든 평가 점수가 0입니다." in captured.out 

def test_execute_with_evaluation_error_reraise(mock_ports):
    """EvaluationError가 발생했을 때 재발생시키는 테스트 (73번 라인)"""
    # Mock 설정
    mock_evaluation_data = [
        EvaluationData(
            question="테스트 질문",
            contexts=["테스트 컨텍스트"],
            answer="테스트 답변",
            ground_truth="정답"
        )
    ]
    
    mock_ports["repository_port"].load_data.return_value = mock_evaluation_data
    mock_ports["llm_port"].get_llm.return_value = MagicMock()
    
    # EvaluationError 발생 시뮬레이션
    evaluation_error = EvaluationError("평가 실행 중 오류")
    mock_ports["evaluation_runner"].evaluate.side_effect = evaluation_error
    
    # 테스트 실행 및 검증
    with pytest.raises(EvaluationError) as exc_info:
        use_case = RunEvaluationUseCase(**mock_ports)
        use_case.execute()
    
    # 원래 EvaluationError가 그대로 재발생되는지 확인 (73번 라인)
    assert exc_info.value is evaluation_error
    assert str(exc_info.value) == "평가 실행 중 오류"


def test_validate_and_convert_result_empty_dict(mock_ports):
    """빈 결과 딕셔너리 검증 테스트 (73번 라인 커버)"""
    # Given
    use_case = RunEvaluationUseCase(**mock_ports)
    
    # When & Then: 빈 딕셔너리로 _validate_and_convert_result 호출 시 예외 발생
    with pytest.raises(EvaluationError, match="평가 결과가 비어있습니다"):
        use_case._validate_and_convert_result({}) 