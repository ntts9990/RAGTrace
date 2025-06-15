import pytest
from src.domain.entities import EvaluationResult

def test_create_evaluation_result_success():
    """정상적인 점수로 EvaluationResult 객체가 성공적으로 생성되는지 테스트"""
    result = EvaluationResult(
        faithfulness=0.9,
        answer_relevancy=0.8,
        context_recall=0.7,
        context_precision=0.6,
        ragas_score=0.75
    )
    assert result.ragas_score == 0.75

@pytest.mark.parametrize(
    "metric, invalid_score",
    [
        ("faithfulness", -0.1),
        ("faithfulness", 1.1),
        ("answer_relevancy", -0.5),
        ("answer_relevancy", 1.5),
        ("context_recall", -1.0),
        ("context_recall", 2.0),
        ("context_precision", -0.2),
        ("context_precision", 1.2),
        ("ragas_score", -0.3),
        ("ragas_score", 1.3),
    ]
)
def test_create_evaluation_result_with_invalid_score(metric, invalid_score):
    """유효하지 않은 점수(0.0-1.0 범위 밖)로 객체 생성 시 예외가 발생하는지 테스트"""
    with pytest.raises(ValueError) as excinfo:
        params = {
            "faithfulness": 0.5,
            "answer_relevancy": 0.5,
            "context_recall": 0.5,
            "context_precision": 0.5,
            "ragas_score": 0.5
        }
        params[metric] = invalid_score
        EvaluationResult(**params)
    
    assert f"{metric} must be between 0.0 and 1.0" in str(excinfo.value)

def test_to_dict_method():
    """to_dict 메소드가 올바른 딕셔너리를 반환하는지 테스트"""
    result = EvaluationResult(
        faithfulness=1.0,
        answer_relevancy=1.0,
        context_recall=1.0,
        context_precision=1.0,
        ragas_score=1.0,
        metadata={"key": "value"}
    )
    
    expected_dict = {
        "faithfulness": 1.0,
        "answer_relevancy": 1.0,
        "context_recall": 1.0,
        "context_precision": 1.0,
        "ragas_score": 1.0,
        "metadata": {"key": "value"}
    }
    
    assert result.to_dict() == expected_dict 

def test_to_dict_with_none_individual_scores_and_metadata():
    """individual_scores와 metadata가 None일 때 to_dict 테스트 (40번 라인)"""
    result = EvaluationResult(
        faithfulness=0.8,
        answer_relevancy=0.9,
        context_recall=0.7,
        context_precision=0.85,
        ragas_score=0.825,
        individual_scores=None,  # None으로 설정
        metadata=None  # None으로 설정
    )
    
    result_dict = result.to_dict()
    
    # 기본 메트릭들은 포함되어야 함
    assert result_dict["faithfulness"] == 0.8
    assert result_dict["answer_relevancy"] == 0.9
    assert result_dict["context_recall"] == 0.7
    assert result_dict["context_precision"] == 0.85
    assert result_dict["ragas_score"] == 0.825
    
    # None인 필드들은 포함되지 않아야 함 (40번 라인 이후의 조건)
    assert "individual_scores" not in result_dict
    assert "metadata" not in result_dict


def test_to_dict_with_individual_scores():
    """individual_scores가 있는 경우 to_dict 테스트 (40번 라인 커버)"""
    # Given: individual_scores가 포함된 EvaluationResult
    individual_scores = [
        {"faithfulness": 0.8, "answer_relevancy": 0.9},
        {"faithfulness": 0.9, "answer_relevancy": 0.8}
    ]
    
    result = EvaluationResult(
        faithfulness=0.85,
        answer_relevancy=0.85,
        context_recall=0.9,
        context_precision=0.8,
        ragas_score=0.85,
        individual_scores=individual_scores
    )
    
    # When
    result_dict = result.to_dict()
    
    # Then: individual_scores가 포함되어야 함 (40번 라인)
    assert "individual_scores" in result_dict
    assert result_dict["individual_scores"] == individual_scores 