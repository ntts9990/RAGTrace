import pytest
from src.domain.entities import EvaluationData

def test_create_evaluation_data_success():
    """정상적인 데이터로 EvaluationData 객체가 성공적으로 생성되는지 테스트"""
    data = EvaluationData(
        question="What is the capital of France?",
        contexts=["France is a country in Europe."],
        answer="Paris",
        ground_truth="The capital of France is Paris."
    )
    assert data.question == "What is the capital of France?"
    assert data.contexts == ["France is a country in Europe."]
    assert data.answer == "Paris"
    assert data.ground_truth == "The capital of France is Paris."

@pytest.mark.parametrize(
    "test_input, expected_exception, error_message",
    [
        ({"question": "", "contexts": ["context"], "answer": "ans", "ground_truth": "gt"}, ValueError, "Question cannot be empty"),
        ({"question": "  ", "contexts": ["context"], "answer": "ans", "ground_truth": "gt"}, ValueError, "Question cannot be empty"),
        ({"question": "q", "contexts": [], "answer": "ans", "ground_truth": "gt"}, ValueError, "Contexts cannot be empty"),
        ({"question": "q", "contexts": ["context"], "answer": "", "ground_truth": "gt"}, ValueError, "Answer cannot be empty"),
        ({"question": "q", "contexts": ["context"], "answer": "  ", "ground_truth": "gt"}, ValueError, "Answer cannot be empty"),
        ({"question": "q", "contexts": ["context"], "answer": "ans", "ground_truth": ""}, ValueError, "Ground truth cannot be empty"),
        ({"question": "q", "contexts": ["context"], "answer": "ans", "ground_truth": "  "}, ValueError, "Ground truth cannot be empty"),
    ]
)
def test_create_evaluation_data_with_invalid_data(test_input, expected_exception, error_message):
    """유효하지 않은 데이터로 EvaluationData 객체 생성 시 예외가 발생하는지 테스트"""
    with pytest.raises(expected_exception) as excinfo:
        EvaluationData(**test_input)
    assert error_message in str(excinfo.value) 