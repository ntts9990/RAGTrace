from unittest.mock import patch, MagicMock
from datasets import Dataset
from ragas.metrics.base import Metric
import pytest
import pandas as pd

from src.infrastructure.evaluation.ragas_adapter import (
    RagasEvalAdapter, RateLimitedEmbeddings
)


class TestRagasEvalAdapter:
    """RagasEvalAdapter 테스트"""

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    def test_evaluate_success(self, mock_evaluate):
        """평가 성공 테스트"""
        # Mock dataset
        dataset = Dataset.from_dict({
            'question': ['질문1', '질문2'],
            'answer': ['답변1', '답변2'],
            'contexts': [['컨텍스트1'], ['컨텍스트2']],
            'ground_truth': ['정답1', '정답2']
        })
        
        # Mock LLM
        mock_llm = MagicMock()
        mock_llm.model = "test-model"
        mock_llm.temperature = 0.1
        
        # Mock evaluation result
        mock_result = MagicMock()
        mock_result._scores_dict = {
            'faithfulness': [0.8, 0.9],
            'answer_relevancy': [0.7, 0.8],
            'context_recall': [0.6, 0.7],
            'context_precision': [0.9, 0.8]
        }
        mock_evaluate.return_value = mock_result
        
        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
            embedding_requests_per_minute=10
        )
        result = adapter.evaluate(dataset, mock_llm)
        
        # 결과 검증
        assert isinstance(result, dict)
        assert 'faithfulness' in result
        assert 'answer_relevancy' in result
        assert 'context_recall' in result
        assert 'context_precision' in result
        assert 'ragas_score' in result
        assert 'individual_scores' in result
        assert 'metadata' in result
        
        # Mock이 올바른 인자로 호출되었는지 확인
        mock_evaluate.assert_called_once()
        call_args = mock_evaluate.call_args
        assert call_args[1]['dataset'] == dataset
        assert call_args[1]['llm'] == mock_llm
        assert call_args[1]['raise_exceptions'] is False

    def test_get_metrics_returns_correct_metrics(self):
        """메트릭 반환 테스트"""
        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
            embedding_requests_per_minute=10
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


class TestRateLimitedEmbeddings:
    """RateLimitedEmbeddings 클래스 테스트"""
    
    def test_init(self):
        """초기화 테스트"""
        embeddings = RateLimitedEmbeddings(
            model="test-model",
            google_api_key="test-key",
            requests_per_minute=5
        )
        assert embeddings.requests_per_minute == 5
        # min_request_interval은 60.0/5 = 12.0으로 계산됨
        assert embeddings.min_request_interval == 12.0
        assert embeddings.last_request_time == 0

    @patch('time.time')
    @patch('time.sleep')
    def test_rate_limit_no_sleep_needed(self, mock_sleep, mock_time):
        """Rate limiting - 대기가 필요하지 않은 경우"""
        # 충분한 시간이 지난 경우 (6초 이상)
        # time.time()이 두 번 호출됨: current_time과 last_request_time 설정
        mock_time.side_effect = [10, 10]  # 10초 시점에서 호출
        
        embeddings = RateLimitedEmbeddings(
            model="test-model",
            google_api_key="test-key",
            requests_per_minute=10  # 6초 간격
        )
        embeddings.last_request_time = 0  # 0초에 마지막 요청
        embeddings._rate_limit()
        
        # 10초가 지났으므로 6초 간격보다 충분히 길어서 대기 불필요
        mock_sleep.assert_not_called()
        assert embeddings.last_request_time == 10

    @patch('time.time')
    @patch('time.sleep')
    def test_rate_limit_with_sleep(self, mock_sleep, mock_time):
        """Rate limiting - 대기가 필요한 경우"""
        # 3초만 지났지만 6초 간격 필요
        # time.time()이 두 번 호출됨: current_time과 last_request_time 설정
        mock_time.side_effect = [8, 8]  # 8초 시점에서 호출
        
        embeddings = RateLimitedEmbeddings(
            model="test-model",
            google_api_key="test-key",
            requests_per_minute=10  # 6초 간격
        )
        embeddings.last_request_time = 5  # 5초에 마지막 요청
        embeddings._rate_limit()
        
        # 6.0 - 3.0 = 3.0초 대기
        mock_sleep.assert_called_once_with(3.0)
        assert embeddings.last_request_time == 8

    @patch('src.infrastructure.evaluation.ragas_adapter.'
           'GoogleGenerativeAIEmbeddings.embed_documents')
    def test_embed_documents_with_rate_limiting(self, mock_embed):
        """문서 임베딩 시 rate limiting 적용 테스트"""
        mock_embed.return_value = [[0.1, 0.2, 0.3]]
        
        embeddings = RateLimitedEmbeddings(
            model="test-model",
            google_api_key="test-key"
        )
        
        with patch.object(embeddings, '_rate_limit') as mock_rate_limit:
            result = embeddings.embed_documents(["test text"])
            
            mock_rate_limit.assert_called_once()
            mock_embed.assert_called_once_with(["test text"])
            assert result == [[0.1, 0.2, 0.3]]

    @patch('src.infrastructure.evaluation.ragas_adapter.'
           'GoogleGenerativeAIEmbeddings.embed_query')
    def test_embed_query_with_rate_limiting(self, mock_embed):
        """쿼리 임베딩 시 rate limiting 적용 테스트"""
        mock_embed.return_value = [0.1, 0.2, 0.3]
        
        embeddings = RateLimitedEmbeddings(
            model="test-model",
            google_api_key="test-key"
        )
        
        with patch.object(embeddings, '_rate_limit') as mock_rate_limit:
            result = embeddings.embed_query("test query")
            
            mock_rate_limit.assert_called_once()
            mock_embed.assert_called_once_with("test query")
            assert result == [0.1, 0.2, 0.3]


class TestRagasEvalAdapterExtended:
    """RagasEvalAdapter 확장 테스트"""
    
    def test_init(self):
        """초기화 테스트"""
        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
            embedding_requests_per_minute=10
        )
        assert len(adapter.metrics) == 4
        assert adapter.metrics[0].name == "faithfulness"

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    def test_evaluate_success_with_scores_dict(self, mock_evaluate):
        """_scores_dict를 사용한 평가 성공 테스트"""
        # Mock 설정
        mock_result = MagicMock()
        mock_result._scores_dict = {
            'faithfulness': [0.8, 0.9],
            'answer_relevancy': [0.7, 0.8],
            'context_recall': [0.6, 0.7],
            'context_precision': [0.9, 0.8]
        }
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
            embedding_requests_per_minute=10
        )
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=2)
        llm = MagicMock()
        llm.model = "test-model"
        llm.temperature = 0.1

        result = adapter.evaluate(dataset, llm)

        assert result['faithfulness'] == pytest.approx(0.85, rel=1e-9)
        assert result['answer_relevancy'] == pytest.approx(0.75, rel=1e-9)
        assert result['context_recall'] == pytest.approx(0.65, rel=1e-9)
        assert result['context_precision'] == pytest.approx(0.85, rel=1e-9)
        assert 'ragas_score' in result
        assert 'individual_scores' in result
        assert len(result['individual_scores']) == 2

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    def test_evaluate_with_repr_dict(self, mock_evaluate):
        """_repr_dict를 사용한 평가 테스트"""
        # Mock 설정
        mock_result = MagicMock()
        mock_result._scores_dict = None
        mock_result._repr_dict = {
            'faithfulness': 0.8,
            'answer_relevancy': 0.7,
            'context_recall': 0.6
            # context_precision 누락으로 171, 172 라인 테스트
        }
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
            embedding_requests_per_minute=10
        )
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=1)
        llm = MagicMock()
        llm.model = "test-model"

        result = adapter.evaluate(dataset, llm)

        assert result['faithfulness'] == 0.8
        assert result['answer_relevancy'] == 0.7
        assert result['context_recall'] == 0.6
        assert result['context_precision'] == 0.0  # 누락된 메트릭은 0.0

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    def test_evaluate_with_missing_metrics(self, mock_evaluate):
        """_scores_dict에 일부 메트릭이 없는 경우 테스트"""
        # Mock 설정
        mock_result = MagicMock()
        mock_result._scores_dict = {
            'faithfulness': [0.8],
            # 'answer_relevancy' 누락
            'context_recall': [0.6]
        }
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
            embedding_requests_per_minute=10
        )
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=1)
        llm = MagicMock()
        llm.model = "test-model"

        result = adapter.evaluate(dataset, llm)

        assert result['faithfulness'] == 0.8
        assert result['answer_relevancy'] == 0.0
        assert result['context_recall'] == 0.6

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    def test_evaluate_with_non_list_scores(self, mock_evaluate):
        """_scores_dict의 점수가 리스트가 아닌 경우 테스트"""
        mock_result = MagicMock()
        mock_result._scores_dict = {
            'faithfulness': 0.85,  # 리스트가 아님
            'answer_relevancy': [0.75]
        }
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
            embedding_requests_per_minute=10
        )
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=1)
        llm = MagicMock()
        llm.model = "test-model"

        result = adapter.evaluate(dataset, llm)

        assert result['faithfulness'] == 0.85
        assert result['answer_relevancy'] == 0.75

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    def test_evaluate_exception_handling(self, mock_evaluate):
        """평가 중 예외 발생 시 처리 테스트"""
        mock_evaluate.side_effect = Exception("Test exception")

        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
            embedding_requests_per_minute=10
        )
        dataset = MagicMock()
        llm = MagicMock()

        result = adapter.evaluate(dataset, llm)

        assert result['ragas_score'] == 0.0
        assert 'faithfulness' in result
        assert result['faithfulness'] == 0.0
        assert result['individual_scores'] == []

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    def test_evaluate_empty_result_dict(self, mock_evaluate):
        """
        Ragas가 빈 dict나 예상치 못한 결과를 반환했을 때의 처리 테스트.
        _scores_dict와 _repr_dict가 모두 비어있거나 없는 경우.
        """
        mock_result = MagicMock()
        # ragas 0.1.0 버전 이전에는 evaluate결과가 dict였음.
        # 하위 호환성을 위해 dict 타입도 테스트
        mock_evaluate.return_value = {}  # 빈 사전 반환

        adapter = RagasEvalAdapter(
            embedding_model_name="test-model",
            api_key="test-key",
            embedding_requests_per_minute=10
        )
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=1)
        llm = MagicMock()
        llm.model = "test-model"

        result = adapter.evaluate(dataset, llm)

        # 모든 메트릭이 0.0으로 처리되는지 확인
        assert result['faithfulness'] == 0.0
        assert result['answer_relevancy'] == 0.0
        assert result['context_recall'] == 0.0
        assert result['context_precision'] == 0.0
        assert result['ragas_score'] == 0.0
        # 개별 점수도 평균(0.0)으로 채워짐
        assert len(result['individual_scores']) == 1
        assert result['individual_scores'][0]['faithfulness'] == 0.0

    def test_evaluate_with_attribute_access_fallback_missing_metric(self):
        """
        _scores_dict와 _repr_dict가 모두 없을 때, 속성 접근으로 대체하는 로직 테스트.
        하나의 메트릭이 결과 객체에 없는 경우.
        """
        # Mock Ragas 결과 객체
        class MockResult:
            def __init__(self):
                self.faithfulness = 0.9
                self.answer_relevancy = 0.8
                # context_recall 누락
                self.context_precision = 0.7

            @property
            def _scores_dict(self):
                return None

            @property
            def _repr_dict(self):
                return None

        mock_result = MockResult()

        with patch('src.infrastructure.evaluation.ragas_adapter.evaluate', return_value=mock_result):
            adapter = RagasEvalAdapter(
                embedding_model_name="test-model",
                api_key="test-key",
                embedding_requests_per_minute=10
            )
            dataset = MagicMock()
            dataset.__len__ = MagicMock(return_value=1)
            llm = MagicMock()
            llm.model = "test-model"

            result = adapter.evaluate(dataset, llm)

            assert result['faithfulness'] == 0.9
            assert result['answer_relevancy'] == 0.8
            assert result['context_recall'] == 0.0  # 누락된 메트릭은 0.0
            assert result['context_precision'] == 0.7
            assert 'ragas_score' in result

    def test_evaluate_with_missing_attribute_189_line(self):
        """
        _scores_dict가 있고, 그 안에 메트릭이 있지만, 점수가 비어있는 경우(None) 테스트
        """
        mock_result = MagicMock()
        mock_result._scores_dict = {
            'faithfulness': [0.9],
            'answer_relevancy': None,  # 점수가 없음
        }
        with patch('src.infrastructure.evaluation.ragas_adapter.evaluate', return_value=mock_result):
            adapter = RagasEvalAdapter(
                embedding_model_name="test-model",
                api_key="test-key",
                embedding_requests_per_minute=10
            )
            dataset = MagicMock()
            dataset.__len__ = MagicMock(return_value=1)
            llm = MagicMock()
            llm.model = "test-model"

            result = adapter.evaluate(dataset, llm)

            assert result['faithfulness'] == 0.9
            assert result['answer_relevancy'] == 0.0
            assert result['context_recall'] == 0.0  # 메트릭 자체가 없음
            assert result['context_precision'] == 0.0

    def test_evaluate_with_missing_attribute_189_line_v2(self):
        """
        _scores_dict가 있고, 그 안에 메트릭이 있지만, 점수 리스트가 비어있는 경우 테스트
        """
        mock_result = MagicMock()
        mock_result._scores_dict = {
            'faithfulness': [0.9],
            'answer_relevancy': [],  # 점수 리스트가 비어 있음
        }

        with patch('src.infrastructure.evaluation.ragas_adapter.evaluate', return_value=mock_result):
            adapter = RagasEvalAdapter(
                embedding_model_name="test-model",
                api_key="test-key",
                embedding_requests_per_minute=10
            )
            dataset = MagicMock()
            dataset.__len__ = MagicMock(return_value=1)
            llm = MagicMock()
            llm.model = "test-model"

            result = adapter.evaluate(dataset, llm)

            assert result['faithfulness'] == 0.9
            assert result['answer_relevancy'] == 0.0