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


def test_run_evaluation_basic_dependency_injection(mock_dependencies):
    """기본적인 의존성 주입이 올바르게 작동하는지 테스트합니다."""
    # Arrange
    use_case = RunEvaluationUseCase(**mock_dependencies)
    
    # Assert that all dependencies are correctly injected
    assert use_case.llm_port is not None
    assert use_case.evaluation_runner_factory is not None
    assert use_case.repository_factory is not None
    assert use_case.data_validator is not None
    assert use_case.generation_service is not None
    assert use_case.result_conversion_service is not None