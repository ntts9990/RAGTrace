import pytest
from src.infrastructure.llm import GeminiAdapter
import config
from unittest.mock import MagicMock, patch, AsyncMock
import time
from src.infrastructure.llm.gemini_adapter import RateLimitedGeminiLLM
from langchain_google_genai import ChatGoogleGenerativeAI

@patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', None)
def test_gemini_adapter_raises_error_if_api_key_is_missing():
    """API 키가 없을 때 ValueError가 발생하는지 테스트"""
    with pytest.raises(ValueError, match="GEMINI_API_KEY가 설정되지 않았습니다"):
        GeminiAdapter()

@patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', 'fake-api-key')
def test_gemini_adapter_creation_success():
    """GeminiAdapter가 성공적으로 생성되는지 테스트"""
    adapter = GeminiAdapter()
    assert adapter.model_name == "gemini-2.5-flash-preview-05-20"
    assert adapter.requests_per_minute == 10

@patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', 'fake-api-key')
def test_get_llm_returns_correct_instance():
    """get_llm이 올바른 인스턴스를 반환하는지 테스트"""
    adapter = GeminiAdapter()
    llm = adapter.get_llm()
    assert isinstance(llm, RateLimitedGeminiLLM)

@pytest.mark.parametrize("time_diff,should_sleep", [
    (0.5, True),   # 0.5초만 지났으므로 대기 필요
    (7.0, False),  # 7초 지났으므로 대기 불필요 (6초 간격 기준)
])
@patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', 'fake-api-key')
def test_rate_limiter_logic(time_diff, should_sleep):
    """Rate limiter 로직이 올바르게 작동하는지 테스트"""
    with patch('time.time') as mock_time, \
         patch('time.sleep') as mock_sleep:

        # 시간 설정: _rate_limit에서 time.time()이 두 번 호출됨
        # 첫 번째: current_time 계산용, 두 번째: last_request_time 업데이트용
        if should_sleep:
            mock_time.side_effect = [time_diff, time_diff + 6.0]  # sleep 후 시간 업데이트
        else:
            mock_time.side_effect = [time_diff, time_diff]

        llm = RateLimitedGeminiLLM(
            model="test-model",
            google_api_key="fake-api-key",
            requests_per_minute=10  # 6초 간격
        )
        llm.last_request_time = 0
        llm._rate_limit()

        if should_sleep:
            # 6초 간격이므로 6 - time_diff만큼 대기
            expected_sleep = 6.0 - time_diff
            mock_sleep.assert_called_once_with(expected_sleep)
        else:
            mock_sleep.assert_not_called()

@patch('src.infrastructure.llm.gemini_adapter.ChatGoogleGenerativeAI.invoke')
@patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', 'fake-api-key')
def test_invoke_calls_rate_limiter_and_super_method(mock_super_invoke):
    """invoke 메서드가 rate limiter와 부모 클래스 메서드를 호출하는지 테스트"""
    mock_super_invoke.return_value = "Success"
    
    llm = RateLimitedGeminiLLM(
        model="test-model",
        google_api_key="fake-api-key"
    )
    
    with patch.object(llm, '_rate_limit') as mock_rate_limit:
        result = llm.invoke("test prompt")
        
        mock_rate_limit.assert_called_once()
        mock_super_invoke.assert_called_once()
        assert mock_super_invoke.call_args[0][0] == "test prompt"
        assert result == "Success"

class TestGeminiAdapter:
    """GeminiAdapter 테스트"""

    @patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_init_success(self):
        """초기화 성공 테스트"""
        adapter = GeminiAdapter()
        assert adapter.model_name == "gemini-2.5-flash-preview-05-20"
        assert adapter.requests_per_minute == 10

    @patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_init_with_custom_params(self):
        """커스텀 파라미터로 초기화 테스트"""
        adapter = GeminiAdapter(model_name="custom-model", requests_per_minute=5)
        assert adapter.model_name == "custom-model"
        assert adapter.requests_per_minute == 5

    @patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', None)
    def test_init_missing_api_key(self):
        """API 키 누락 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="GEMINI_API_KEY가 설정되지 않았습니다"):
            GeminiAdapter()

    @patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_get_llm(self):
        """LLM 객체 반환 테스트"""
        adapter = GeminiAdapter()
        llm = adapter.get_llm()
        
        assert isinstance(llm, RateLimitedGeminiLLM)
        # 실제로는 "models/" 접두사가 붙음
        assert llm.model == "models/gemini-2.5-flash-preview-05-20"
        assert llm.temperature == 0.1
        assert llm.requests_per_minute == 10

class TestRateLimitedGeminiLLM:
    """RateLimitedGeminiLLM 테스트"""

    @patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_init(self):
        """초기화 테스트"""
        llm = RateLimitedGeminiLLM(
            model="test-model",
            google_api_key="test-key",
            requests_per_minute=5
        )
        assert llm.requests_per_minute == 5
        assert llm.min_request_interval == 12.0  # 60/5
        assert llm.last_request_time == 0

    @patch('time.time')
    @patch('time.sleep')
    @patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_rate_limit_with_sleep(self, mock_sleep, mock_time):
        """Rate limiting - 대기가 필요한 경우"""
        # 3초만 지났지만 6초 간격 필요
        # time.time()이 두 번 호출됨: current_time 계산용, last_request_time 업데이트용
        mock_time.side_effect = [8, 11]  # 8-5=3초 지남, sleep 후 11로 업데이트

        llm = RateLimitedGeminiLLM(
            model="test-model",
            google_api_key="test-key",
            requests_per_minute=10  # 6초 간격
        )
        llm.last_request_time = 5
        llm._rate_limit()

        # 6.0 - 3.0 = 3.0초 대기
        mock_sleep.assert_called_once_with(3.0)
        assert llm.last_request_time == 11

    @patch('src.infrastructure.llm.gemini_adapter.ChatGoogleGenerativeAI.invoke')
    @patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', 'test-key')
    def test_invoke_with_rate_limiting(self, mock_invoke):
        """동기 호출 시 rate limiting 적용 테스트"""
        mock_invoke.return_value = "test response"
        
        llm = RateLimitedGeminiLLM(
            model="test-model",
            google_api_key="test-key"
        )
        
        with patch.object(llm, '_rate_limit') as mock_rate_limit:
            result = llm.invoke("test input")
            
            mock_rate_limit.assert_called_once()
            mock_invoke.assert_called_once_with("test input")
            assert result == "test response"

    @pytest.mark.asyncio
    @patch('src.infrastructure.llm.gemini_adapter.ChatGoogleGenerativeAI.ainvoke')
    @patch('src.infrastructure.llm.gemini_adapter.config.GEMINI_API_KEY', 'test-key')
    async def test_ainvoke_with_rate_limiting(self, mock_ainvoke):
        """비동기 호출 시 rate limiting 적용 테스트"""
        mock_ainvoke.return_value = "test async response"
        
        llm = RateLimitedGeminiLLM(
            model="test-model",
            google_api_key="test-key"
        )
        
        with patch.object(llm, '_rate_limit') as mock_rate_limit:
            result = await llm.ainvoke("test async input")
            
            mock_rate_limit.assert_called_once()
            mock_ainvoke.assert_called_once_with("test async input")
            assert result == "test async response" 