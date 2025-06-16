import pytest
import os
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

from src.domain.entities import EvaluationData, EvaluationResult
from src.domain.value_objects.metrics import MetricScore, MetricThresholds
from src.application.ports.llm import LlmPort
from src.application.ports.evaluation import EvaluationRunnerPort
from src.application.ports.repository import EvaluationRepositoryPort


@pytest.fixture
def sample_evaluation_data():
    """Sample evaluation data for testing."""
    return EvaluationData(
        question="Python에서 리스트와 튜플의 차이점은 무엇인가요?",
        contexts=[
            "리스트는 가변(mutable) 데이터 타입으로 생성 후 요소를 변경할 수 있습니다.",
            "튜플은 불변(immutable) 데이터 타입으로 생성 후 요소를 변경할 수 없습니다.",
            "리스트는 대괄호 []로 표현하고, 튜플은 소괄호 ()로 표현합니다."
        ],
        answer="리스트는 가변 데이터 타입으로 요소를 변경할 수 있지만, 튜플은 불변 데이터 타입으로 요소를 변경할 수 없습니다.",
        ground_truth="리스트(list)는 가변(mutable) 객체로 생성 후 요소의 추가, 삭제, 수정이 가능합니다. 반면 튜플(tuple)은 불변(immutable) 객체로 생성 후 요소를 변경할 수 없습니다."
    )


@pytest.fixture
def sample_evaluation_data_list(sample_evaluation_data):
    """List of sample evaluation data for testing."""
    return [
        sample_evaluation_data,
        EvaluationData(
            question="클래스와 객체의 차이점을 설명해주세요.",
            contexts=[
                "클래스는 객체를 생성하기 위한 템플릿 또는 설계도입니다.",
                "객체는 클래스를 기반으로 생성된 실제 인스턴스입니다.",
                "클래스는 속성과 메서드를 정의하고, 객체는 이를 구현합니다."
            ],
            answer="클래스는 객체를 만들기 위한 템플릿이고, 객체는 클래스로부터 생성된 실제 인스턴스입니다.",
            ground_truth="클래스(class)는 객체를 생성하기 위한 템플릿으로 속성과 메서드를 정의합니다. 객체(object)는 클래스를 기반으로 생성된 실제 인스턴스로 클래스에서 정의한 속성과 메서드를 가집니다."
        )
    ]


@pytest.fixture
def sample_metric_scores():
    """Sample metric scores for testing."""
    return {
        "answer_relevancy": MetricScore(0.85),
        "faithfulness": MetricScore(0.92),
        "context_precision": MetricScore(0.78),
        "context_recall": MetricScore(0.88)
    }


@pytest.fixture
def sample_evaluation_result(sample_metric_scores):
    """Sample evaluation result for testing."""
    return EvaluationResult(scores=sample_metric_scores)


@pytest.fixture
def sample_metric_thresholds():
    """Sample metric thresholds for testing."""
    return MetricThresholds(
        excellent_threshold=0.9,
        good_threshold=0.8,
        fair_threshold=0.6
    )


@pytest.fixture
def mock_llm_port():
    """Mock LLM port for testing."""
    mock = Mock(spec=LlmPort)
    mock.generate_response.return_value = "Mock LLM response"
    mock.is_available.return_value = True
    return mock


@pytest.fixture
def mock_evaluation_runner():
    """Mock evaluation runner for testing."""
    mock = Mock(spec=EvaluationRunnerPort)
    return mock


@pytest.fixture
def mock_repository():
    """Mock repository for testing."""
    mock = Mock(spec=EvaluationRepositoryPort)
    return mock


@pytest.fixture
def temp_env_file(tmp_path):
    """Create temporary .env file for testing."""
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=test_api_key_123")
    return str(env_file)


@pytest.fixture
def sample_json_data():
    """Sample JSON data structure for file repository testing."""
    return {
        "evaluation_data": [
            {
                "question": "Python에서 리스트와 튜플의 차이점은 무엇인가요?",
                "contexts": [
                    "리스트는 가변(mutable) 데이터 타입으로 생성 후 요소를 변경할 수 있습니다.",
                    "튜플은 불변(immutable) 데이터 타입으로 생성 후 요소를 변경할 수 없습니다."
                ],
                "answer": "리스트는 가변 데이터 타입으로 요소를 변경할 수 있지만, 튜플은 불변 데이터 타입으로 요소를 변경할 수 없습니다.",
                "ground_truth": "리스트(list)는 가변(mutable) 객체로 생성 후 요소의 추가, 삭제, 수정이 가능합니다. 반면 튜플(tuple)은 불변(immutable) 객체로 생성 후 요소를 변경할 수 없습니다."
            }
        ]
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["TESTING"] = "true"
    os.environ["GEMINI_API_KEY"] = "test_api_key_for_testing"
    yield
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    if "GEMINI_API_KEY" in os.environ and os.environ["GEMINI_API_KEY"] == "test_api_key_for_testing":
        del os.environ["GEMINI_API_KEY"]
