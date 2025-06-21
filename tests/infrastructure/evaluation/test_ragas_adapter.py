from unittest.mock import MagicMock, patch

import pytest
from datasets import Dataset
from ragas.metrics.base import Metric

from src.infrastructure.evaluation.ragas_adapter import RagasEvalAdapter


class TestRagasEvalAdapter:
    """RagasEvalAdapter 테스트"""

    @patch("src.infrastructure.evaluation.ragas_adapter.evaluate")
    def test_evaluate_success(self, mock_evaluate):
        """평가 성공 테스트"""
        # Mock dataset
        dataset = Dataset.from_dict(
            {
                "question": ["질문1", "질문2"],
                "answer": ["답변1", "답변2"],
                "contexts": [["컨텍스트1"], ["컨텍스트2"]],
                "ground_truth": ["정답1", "정답2"],
            }
        )

        # Mock LLM
        mock_llm = MagicMock()
        mock_llm.model = "test-model"
        mock_llm.temperature = 0.1

        # Mock evaluation result
        mock_result = MagicMock()
        mock_result._scores_dict = {
            "faithfulness": [0.8, 0.9],
            "answer_relevancy": [0.7, 0.8],
            "context_recall": [0.6, 0.7],
            "context_precision": [0.9, 0.8],
        }
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
        )
        result = adapter.evaluate(dataset, mock_llm)

        # 결과 검증
        assert isinstance(result, dict)
        assert "faithfulness" in result
        assert "answer_relevancy" in result
        assert "context_recall" in result
        assert "context_precision" in result
        assert "ragas_score" in result
        assert "individual_scores" in result
        assert "metadata" in result

        # Mock이 올바른 인자로 호출되었는지 확인
        mock_evaluate.assert_called_once()
        call_args = mock_evaluate.call_args
        assert call_args[1]["dataset"] == dataset
        assert call_args[1]["llm"] == mock_llm
        assert call_args[1]["raise_exceptions"] is False

    def test_get_metrics_returns_correct_metrics(self):
        """메트릭 반환 테스트"""
        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
        )
        metrics = adapter.metrics

        # 메트릭 개수 확인
        assert len(metrics) == 4

        # 메트릭 이름 확인
        metric_names = [m.name for m in metrics]
        assert "faithfulness" in metric_names
        assert "answer_relevancy" in metric_names
        assert "context_recall" in metric_names
        assert "context_precision" in metric_names
        assert all(isinstance(m, Metric) for m in metrics)

    @patch("src.infrastructure.evaluation.ragas_adapter.evaluate")
    def test_evaluate_success_with_scores_dict(self, mock_evaluate):
        """_scores_dict를 사용한 평가 성공 테스트"""
        # Mock 설정
        mock_result = MagicMock()
        mock_result._scores_dict = {
            "faithfulness": [0.8, 0.9],
            "answer_relevancy": [0.7, 0.8],
            "context_recall": [0.6, 0.7],
            "context_precision": [0.9, 0.8],
        }
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
        )
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=2)
        llm = MagicMock()
        llm.model = "test-model"
        llm.temperature = 0.1

        result = adapter.evaluate(dataset, llm)

        assert result["faithfulness"] == pytest.approx(0.85, rel=1e-9)
        assert result["answer_relevancy"] == pytest.approx(0.75, rel=1e-9)
        assert result["context_recall"] == pytest.approx(0.65, rel=1e-9)
        assert result["context_precision"] == pytest.approx(0.85, rel=1e-9)
        assert "ragas_score" in result
        assert "individual_scores" in result
        assert len(result["individual_scores"]) == 2

    @patch("src.infrastructure.evaluation.ragas_adapter.evaluate")
    def test_evaluate_with_missing_metrics(self, mock_evaluate):
        """_scores_dict에 일부 메트릭이 없는 경우 테스트"""
        # Mock 설정
        mock_result = MagicMock()
        mock_result._scores_dict = {
            "faithfulness": [0.8],
            # 'answer_relevancy' 누락
            "context_recall": [0.6],
        }
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
        )
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=1)
        llm = MagicMock()
        llm.model = "test-model"

        result = adapter.evaluate(dataset, llm)

        assert result["faithfulness"] == 0.8
        assert result["answer_relevancy"] == 0.0
        assert result["context_recall"] == 0.6

    @patch("src.infrastructure.evaluation.ragas_adapter.evaluate")
    def test_evaluate_exception_handling(self, mock_evaluate):
        """평가 중 예외 발생 시 처리 테스트"""
        mock_evaluate.side_effect = Exception("Test exception")

        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
        )
        dataset = MagicMock()
        llm = MagicMock()

        result = adapter.evaluate(dataset, llm)

        assert result["ragas_score"] == 0.0
        assert "faithfulness" in result
        assert result["faithfulness"] == 0.0
        assert result["individual_scores"] == []