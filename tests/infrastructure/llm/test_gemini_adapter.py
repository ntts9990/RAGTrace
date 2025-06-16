import pytest
from src.infrastructure.llm import GeminiAdapter
from unittest.mock import patch
from src.infrastructure.llm.gemini_adapter import RateLimitedGeminiLLM
from langchain_google_genai import ChatGoogleGenerativeAI


def test_gemini_adapter_raises_error_if_api_key_is_missing():
    """API 키가 없을 때 ValueError가 발생하는지 테스트"""
    with pytest.raises(ValueError, match="GEMINI_API_KEY가 설정되지 않았습니다"):
        GeminiAdapter(api_key="", model_name="test", requests_per_minute=1)


def test_gemini_adapter_creation_success():
    """GeminiAdapter가 성공적으로 생성되는지 테스트"""
    adapter = GeminiAdapter(
        api_key="fake-api-key",
        model_name="test-model",
        requests_per_minute=8
    )
    assert adapter.model_name == "test-model"
    assert adapter.requests_per_minute == 8


def test_get_llm_returns_correct_instance():
    """get_llm이 올바른 인스턴스를 반환하는지 테스트"""
    adapter = GeminiAdapter(
        api_key="fake-api-key",
        model_name="test-model",
        requests_per_minute=8
    )
    llm = adapter.get_llm()
    assert isinstance(llm, RateLimitedGeminiLLM)
    # ChatGoogleGenerativeAI가 모델명에 "models/" 접두사를 자동으로 추가함
    assert llm.model == "models/test-model" or llm.model == "test-model"
    assert llm.requests_per_minute == 8


@pytest.mark.parametrize("time_diff,should_sleep", [
    (0.5, True),   # 0.5초만 지났으므로 대기 필요
    (7.0, False),  # 7초 지났으므로 대기 불필요 (6초 간격 기준)
])
def test_rate_limiter_logic(time_diff, should_sleep):
    """Rate limiter 로직이 올바르게 작동하는지 테스트"""
    with patch('time.time') as mock_time, \
         patch('time.sleep') as mock_sleep:

        # 시간 설정: _rate_limit에서 time.time()이 두 번 호출됨
        # 첫 번째: current_time 계산용, 두 번째: last_request_time 업데이트용
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

    def test_init_success(self):
        """초기화 성공 테스트"""
        adapter = GeminiAdapter(
            api_key="test-key",
            model_name="test-model",
            requests_per_minute=8
        )
        assert adapter.model_name == "test-model"
        assert adapter.requests_per_minute == 8

    def test_init_with_custom_params(self):
        """커스텀 파라미터로 초기화 테스트"""
        adapter = GeminiAdapter(api_key="test-key", model_name="custom-model", requests_per_minute=5)
        assert adapter.model_name == "custom-model"
        assert adapter.requests_per_minute == 5

    def test_init_missing_api_key(self):
        """API 키 누락 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="GEMINI_API_KEY가 설정되지 않았습니다"):
            GeminiAdapter(api_key="", model_name="test", requests_per_minute=1)

    def test_get_llm(self):
        """LLM 객체 반환 테스트"""
        adapter = GeminiAdapter(
            api_key="test-key",
            model_name="test-model",
            requests_per_minute=8
        )
        llm = adapter.get_llm()
        
        assert isinstance(llm, RateLimitedGeminiLLM)
        # ChatGoogleGenerativeAI가 모델명에 "models/" 접두사를 자동으로 추가함
        assert llm.model == "models/test-model" or llm.model == "test-model"
        assert llm.requests_per_minute == 8


class TestRateLimitedGeminiLLM:
    """RateLimitedGeminiLLM 테스트"""

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
    def test_rate_limit_with_sleep(self, mock_sleep, mock_time):
        """Rate limiting - 대기가 필요한 경우"""
        # 3초만 지났지만 6초 간격 필요
        # time.time()이 두 번 호출됨: current_time 계산용, last_request_time 업데이트용
        mock_time.side_effect = [8, 8]

        llm = RateLimitedGeminiLLM(
            model="test-model",
            google_api_key="test-key",
            requests_per_minute=10  # 6초 간격
        )
        llm.last_request_time = 5
        llm._rate_limit()

        # 6.0 - 3.0 = 3.0초 대기
        mock_sleep.assert_called_once_with(3.0)
        assert llm.last_request_time == 8

    @patch('src.infrastructure.llm.gemini_adapter.ChatGoogleGenerativeAI.invoke')
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