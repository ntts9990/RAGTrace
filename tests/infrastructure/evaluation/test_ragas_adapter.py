from unittest.mock import MagicMock, patch

import pytest
from datasets import Dataset

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

        # Mock embeddings
        mock_embeddings = MagicMock()

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
            llm=mock_llm,
            embeddings=mock_embeddings,
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

    def test_get_metrics_returns_correct_metrics(self):
        """메트릭 반환 테스트"""
        # Mock LLM and embeddings
        mock_llm = MagicMock()
        mock_embeddings = MagicMock()
        
        adapter = RagasEvalAdapter(
            llm=mock_llm,
            embeddings=mock_embeddings,
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

    @patch("src.infrastructure.evaluation.ragas_adapter.evaluate")
    def test_evaluate_success_with_scores_dict(self, mock_evaluate):
        """scores_dict이 있는 경우 평가 성공 테스트"""
        # Mock dataset
        dataset = Dataset.from_dict({"question": ["테스트"], "answer": ["답변"], "contexts": [["컨텍스트"]], "ground_truth": ["정답"]})
        
        # Mock LLM and embeddings
        mock_llm = MagicMock()
        mock_embeddings = MagicMock()

        # Mock evaluation result with scores_dict
        mock_result = MagicMock()
        mock_result.scores_dict = {
            "faithfulness": [0.9],
            "answer_relevancy": [0.8], 
            "context_recall": [0.7],
            "context_precision": [0.95],
        }
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter(llm=mock_llm, embeddings=mock_embeddings)
        result = adapter.evaluate(dataset, mock_llm)

        assert isinstance(result, dict)
        assert "ragas_score" in result

    @patch("src.infrastructure.evaluation.ragas_adapter.evaluate")
    def test_evaluate_with_missing_metrics(self, mock_evaluate):
        """누락된 메트릭이 있을 때 기본값으로 채우는 테스트"""
        # Mock dataset
        dataset = Dataset.from_dict({"question": ["테스트"], "answer": ["답변"], "contexts": [["컨텍스트"]], "ground_truth": ["정답"]})
        
        # Mock LLM and embeddings
        mock_llm = MagicMock()
        mock_embeddings = MagicMock()

        # Mock evaluation result with missing metrics
        mock_result = MagicMock()
        mock_result._scores_dict = {
            "faithfulness": [0.8],
            # answer_relevancy 누락
        }
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter(llm=mock_llm, embeddings=mock_embeddings)
        result = adapter.evaluate(dataset, mock_llm)

        assert isinstance(result, dict)
        assert "answer_relevancy" in result  # 기본값으로 채워져야 함

    @patch("src.infrastructure.evaluation.ragas_adapter.evaluate")
    def test_evaluate_exception_handling(self, mock_evaluate):
        """평가 중 예외 발생 시 처리 테스트"""
        # Mock dataset
        dataset = Dataset.from_dict({"question": ["테스트"], "answer": ["답변"], "contexts": [["컨텍스트"]], "ground_truth": ["정답"]})
        
        # Mock LLM and embeddings
        mock_llm = MagicMock()
        mock_embeddings = MagicMock()

        # Mock evaluation exception
        mock_evaluate.side_effect = Exception("평가 실패")

        adapter = RagasEvalAdapter(llm=mock_llm, embeddings=mock_embeddings)
        
        with pytest.raises(Exception):
            adapter.evaluate(dataset, mock_llm)