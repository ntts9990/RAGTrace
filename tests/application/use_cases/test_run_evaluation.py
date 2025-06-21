from unittest.mock import MagicMock

import pytest
from datasets import Dataset

from src.application.use_cases import RunEvaluationUseCase
from src.domain import EvaluationData, EvaluationError, EvaluationResult
from src.domain.prompts import PromptType


@pytest.fixture
def mock_dependencies():
    """유스케이스가 의존하는 객체들의 모의 객체를 생성합니다."""
    return {
        "llm_port": MagicMock(),
        "evaluation_runner_factory": MagicMock(),
        "repository_factory": MagicMock(),
        "data_validator": MagicMock(),
        "generation_service": MagicMock(),
        "result_conversion_service": MagicMock(),
    }


def test_run_evaluation_success(mock_dependencies):
    """평가 유스케이스가 성공적으로 실행되는 시나리오를 테스트합니다."""
    # Arrange: 모의 객체 설정
    mock_data = [EvaluationData("q", ["c"], "a", "g")]
    mock_repository = MagicMock()
    mock_repository.load_data.return_value = mock_data
    mock_dependencies["repository_factory"].create_repository.return_value = mock_repository

    mock_llm = MagicMock()
    mock_dependencies["llm_port"].get_llm.return_value = mock_llm
    mock_dependencies["llm_port"].generate_answer.return_value = "generated answer"

    # Set up data validator
    mock_dependencies["data_validator"].validate.return_value = None

    # Set up generation service
    mock_dependencies["generation_service"].enhance_answer.return_value = "enhanced answer"

    # Set up result conversion service
    mock_result = EvaluationResult(
        faithfulness=1.0,
        answer_relevancy=1.0,
        context_recall=1.0,
        context_precision=1.0,
        ragas_score=1.0
    )
    mock_dependencies["result_conversion_service"].convert_to_result.return_value = mock_result

    mock_evaluator = MagicMock()
    mock_result_dict = {
        "faithfulness": 1.0,
        "answer_relevancy": 1.0,
        "context_recall": 1.0,
        "context_precision": 1.0,
        "ragas_score": 1.0,
    }
    mock_evaluator.evaluate.return_value = mock_result_dict
    mock_dependencies["evaluation_runner_factory"].create_evaluator.return_value = mock_evaluator

    use_case = RunEvaluationUseCase(**mock_dependencies)

    # Act: 유스케이스 실행
    result = use_case.execute(dataset_name="test_dataset", prompt_type=PromptType.DEFAULT)

    # Assert: 결과 확인
    assert isinstance(result, EvaluationResult)
    assert result.ragas_score == 1.0


def test_run_evaluation_no_data(mock_dependencies):
    """데이터가 없을 때 EvaluationError가 발생하는지 테스트합니다."""
    # Arrange
    mock_repository = MagicMock()
    mock_repository.load_data.return_value = []
    mock_dependencies["repository_factory"].create_repository.return_value = mock_repository
    
    use_case = RunEvaluationUseCase(**mock_dependencies)

    # Act & Assert
    with pytest.raises(EvaluationError):
        use_case.execute(dataset_name="test_dataset")


def test_run_evaluation_runner_fails(mock_dependencies):
    """EvaluationRunner에서 예외 발생 시 EvaluationError로 래핑되는지 테스트합니다."""
    # Arrange
    mock_data = [EvaluationData("q", ["c"], "a", "g")]
    mock_repository = MagicMock()
    mock_repository.load_data.return_value = mock_data
    mock_dependencies["repository_factory"].create_repository.return_value = mock_repository
    
    mock_evaluator = MagicMock()
    mock_evaluator.evaluate.side_effect = Exception("Ragas API error")
    mock_dependencies["evaluation_runner_factory"].create_evaluator.return_value = mock_evaluator
    
    mock_dependencies["llm_port"].generate_answer.return_value = "generated answer"
    mock_dependencies["data_validator"].validate.return_value = None

    use_case = RunEvaluationUseCase(**mock_dependencies)

    # Act & Assert
    with pytest.raises(EvaluationError):
        use_case.execute(dataset_name="test_dataset")