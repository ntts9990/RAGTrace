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
        
        adapter = RagasEvalAdapter()
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
        adapter = RagasEvalAdapter()
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
        with patch('src.infrastructure.evaluation.ragas_adapter.config.'
                   'GEMINI_API_KEY', 'test-key'):
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
        
        with patch('src.infrastructure.evaluation.ragas_adapter.config.'
                   'GEMINI_API_KEY', 'test-key'):
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
        
        with patch('src.infrastructure.evaluation.ragas_adapter.config.'
                   'GEMINI_API_KEY', 'test-key'):
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
        
        with patch('src.infrastructure.evaluation.ragas_adapter.config.'
                   'GEMINI_API_KEY', 'test-key'):
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
        
        with patch('src.infrastructure.evaluation.ragas_adapter.config.'
                   'GEMINI_API_KEY', 'test-key'):
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
    
    @patch('src.infrastructure.evaluation.ragas_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_init(self):
        """초기화 테스트"""
        adapter = RagasEvalAdapter()
        assert len(adapter.metrics) == 4
        assert adapter.metrics[0].name == "faithfulness"

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    @patch('src.infrastructure.evaluation.ragas_adapter.config.GEMINI_API_KEY', 'test-key')
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

        adapter = RagasEvalAdapter()
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
    @patch('src.infrastructure.evaluation.ragas_adapter.config.GEMINI_API_KEY', 'test-key')
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

        adapter = RagasEvalAdapter()
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
    @patch('src.infrastructure.evaluation.ragas_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_evaluate_with_attribute_access(self, mock_evaluate):
        """속성 접근을 통한 평가 테스트"""
        # Mock 설정
        mock_result = MagicMock()
        mock_result._scores_dict = None
        mock_result._repr_dict = None
        mock_result.faithfulness = 0.8
        mock_result.answer_relevancy = 0.7
        mock_result.context_recall = 0.6
        mock_result.context_precision = 0.9
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter()
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=1)
        llm = MagicMock()
        llm.model = "test-model"

        result = adapter.evaluate(dataset, llm)

        assert result['faithfulness'] == 0.8
        assert result['answer_relevancy'] == 0.7
        assert result['context_recall'] == 0.6
        assert result['context_precision'] == 0.9

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    @patch('src.infrastructure.evaluation.ragas_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_evaluate_with_missing_metrics(self, mock_evaluate):
        """누락된 메트릭이 있는 경우 테스트"""
        # Mock 설정
        mock_result = MagicMock()
        mock_result._scores_dict = {
            'faithfulness': [0.8],
            'answer_relevancy': [0.7]
            # context_recall, context_precision 누락
        }
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter()
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=1)
        llm = MagicMock()
        llm.model = "test-model"

        result = adapter.evaluate(dataset, llm)

        assert result['faithfulness'] == 0.8
        assert result['answer_relevancy'] == 0.7
        assert result['context_recall'] == 0.0  # 누락된 메트릭은 0.0
        assert result['context_precision'] == 0.0

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    @patch('src.infrastructure.evaluation.ragas_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_evaluate_with_non_list_scores(self, mock_evaluate):
        """리스트가 아닌 점수 형태 테스트"""
        # Mock 설정
        mock_result = MagicMock()
        mock_result._scores_dict = {
            'faithfulness': 0.8,  # 리스트가 아닌 단일 값
            'answer_relevancy': 0.7,
            'context_recall': 0.6,
            'context_precision': 0.9
        }
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter()
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=1)
        llm = MagicMock()
        llm.model = "test-model"

        result = adapter.evaluate(dataset, llm)

        assert result['faithfulness'] == 0.8
        assert result['answer_relevancy'] == 0.7
        assert result['context_recall'] == 0.6
        assert result['context_precision'] == 0.9

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    @patch('src.infrastructure.evaluation.ragas_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_evaluate_exception_handling(self, mock_evaluate):
        """예외 처리 테스트"""
        # Mock 설정 - 예외 발생
        mock_evaluate.side_effect = Exception("평가 실패")

        adapter = RagasEvalAdapter()
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=1)
        llm = MagicMock()
        llm.model = "test-model"

        result = adapter.evaluate(dataset, llm)

        # 예외 발생 시 모든 메트릭이 0.0으로 설정
        assert result['faithfulness'] == 0.0
        assert result['answer_relevancy'] == 0.0
        assert result['context_recall'] == 0.0
        assert result['context_precision'] == 0.0
        assert result['ragas_score'] == 0.0
        assert result['individual_scores'] == []

    @patch('src.infrastructure.evaluation.ragas_adapter.evaluate')
    @patch('src.infrastructure.evaluation.ragas_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_evaluate_empty_result_dict(self, mock_evaluate):
        """빈 결과 딕셔너리 테스트 (206번 라인 커버)"""
        # Mock 설정
        mock_result = MagicMock()
        mock_result._scores_dict = None
        mock_result._repr_dict = None
        # 모든 속성을 None으로 설정하여 result_dict가 비어있게 만듦
        for metric_name in ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']:
            setattr(mock_result, metric_name, None)
        mock_evaluate.return_value = mock_result

        adapter = RagasEvalAdapter()
        dataset = MagicMock()
        dataset.__len__ = MagicMock(return_value=1)
        llm = MagicMock()
        llm.model = "test-model"

        result = adapter.evaluate(dataset, llm)

        # 빈 result_dict인 경우 ragas_score는 0.0 (206번 라인)
        assert result['ragas_score'] == 0.0
        assert result['faithfulness'] == 0.0
        assert result['answer_relevancy'] == 0.0
        assert result['context_recall'] == 0.0
        assert result['context_precision'] == 0.0

    def test_evaluate_with_attribute_access_fallback_missing_metric(self):
        """속성 접근 방식에서 메트릭이 누락된 경우 테스트 (189번 라인)"""
        # Mock 데이터셋
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=2)
        
        # Mock LLM
        mock_llm = MagicMock()
        mock_llm.model = "test-model"
        
        # Mock result - _scores_dict와 _repr_dict가 모두 None이고, 
        # hasattr는 True이지만 getattr에서 None을 반환하는 경우
        mock_result = MagicMock()
        mock_result._scores_dict = None
        mock_result._repr_dict = None
        
        # hasattr는 True를 반환하지만 실제 속성값은 None
        mock_result.faithfulness = None  # 189번 라인을 실행시키기 위함
        mock_result.answer_relevancy = 0.5
        mock_result.context_recall = 0.5
        mock_result.context_precision = 0.5
        
        with patch('src.infrastructure.evaluation.ragas_adapter.evaluate', return_value=mock_result), \
             patch('src.infrastructure.evaluation.ragas_adapter.RateLimitedEmbeddings'), \
             patch('builtins.print') as mock_print:
            
            adapter = RagasEvalAdapter()
            result = adapter.evaluate(mock_dataset, mock_llm)
            
            # 결과 검증
            assert result['faithfulness'] == 0.0  # None이므로 0.0으로 설정됨
            assert result['answer_relevancy'] == 0.5
            assert result['context_recall'] == 0.5
            assert result['context_precision'] == 0.5
            
            # 189번 라인의 경고 메시지가 출력되었는지 확인
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            # 실제로는 hasattr가 True이므로 189번 라인이 아닌 다른 라인이 실행됨
            # 189번 라인을 실행하려면 hasattr가 False여야 함
            # 테스트 로직을 수정하여 정확한 조건을 만족시킴
            assert result is not None  # 일단 결과가 반환되는지만 확인


    def test_evaluate_with_missing_attribute_189_line(self):
        """189번 라인을 정확히 실행하는 테스트 - hasattr가 False인 경우"""
        # Mock 데이터셋
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=1)
        
        # Mock LLM
        mock_llm = MagicMock()
        mock_llm.model = "test-model"
        
        # Mock result - _scores_dict와 _repr_dict가 모두 None
        mock_result = MagicMock()
        mock_result._scores_dict = None
        mock_result._repr_dict = None
        
        # hasattr가 특정 메트릭에 대해 False를 반환하도록 설정
        original_hasattr = hasattr
        def mock_hasattr(obj, name):
            if obj is mock_result and name == 'faithfulness':
                return False  # 이 경우 189번 라인이 실행됨
            return original_hasattr(obj, name)
        
        with patch('src.infrastructure.evaluation.ragas_adapter.evaluate', return_value=mock_result), \
             patch('src.infrastructure.evaluation.ragas_adapter.RateLimitedEmbeddings'), \
             patch('builtins.hasattr', side_effect=mock_hasattr), \
             patch('builtins.print') as mock_print:
            
            adapter = RagasEvalAdapter()
            result = adapter.evaluate(mock_dataset, mock_llm)
            
            # 결과 검증
            assert result['faithfulness'] == 0.0  # hasattr가 False이므로 0.0으로 설정됨
            
            # 189번 라인의 경고 메시지가 출력되었는지 확인
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("경고: faithfulness 결과를 찾을 수 없습니다." in call for call in print_calls)