from unittest.mock import MagicMock, patch

import pytest

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


def test_run_evaluation_constructor(mock_dependencies):
    """RunEvaluationUseCase가 올바르게 생성되는지 테스트합니다."""
    # Act
    use_case = RunEvaluationUseCase(**mock_dependencies)
    
    # Assert
    assert use_case.llm_port == mock_dependencies["llm_port"]
    assert use_case.evaluation_runner_factory == mock_dependencies["evaluation_runner_factory"]
    assert use_case.repository_factory == mock_dependencies["repository_factory"]
    assert use_case.data_validator == mock_dependencies["data_validator"]
    assert use_case.generation_service == mock_dependencies["generation_service"]
    assert use_case.result_conversion_service == mock_dependencies["result_conversion_service"]


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


def test_run_evaluation_basic_flow(mock_dependencies):
    """기본적인 평가 플로우가 실행되는지 테스트합니다."""
    # Arrange
    mock_data = [EvaluationData("q", ["c"], "a", "g")]
    mock_repository = MagicMock()
    mock_repository.load_data.return_value = mock_data
    mock_dependencies["repository_factory"].create_repository.return_value = mock_repository
    
    # Mock validation
    mock_validation_report = MagicMock()
    mock_validation_report.has_errors = False
    mock_validation_report.has_warnings = False
    mock_dependencies["data_validator"].validate_data_list.return_value = mock_validation_report
    
    # Mock generation service
    mock_generation_result = MagicMock()
    mock_generation_result.successes = 1
    mock_generation_result.failures = 0
    mock_dependencies["generation_service"].generate_missing_answers.return_value = mock_generation_result
    
    # Mock conversion service
    mock_result = EvaluationResult(
        faithfulness=1.0,
        answer_relevancy=1.0,
        context_recall=1.0,
        context_precision=1.0,
        ragas_score=1.0
    )
    mock_dependencies["result_conversion_service"].convert_to_result.return_value = mock_result
    
    use_case = RunEvaluationUseCase(**mock_dependencies)

    # Act
    with patch('builtins.print'):  # Suppress print statements
        result = use_case.execute(dataset_name="test_dataset", prompt_type=PromptType.DEFAULT)

    # Assert
    assert isinstance(result, EvaluationResult)
    assert result.ragas_score == 1.0