from unittest.mock import patch, MagicMock

import pytest

from src.infrastructure.llm import GeminiAdapter


def test_gemini_adapter_raises_error_if_api_key_is_missing():
    """API 키가 없을 때 ValueError가 발생하는지 테스트"""
    with pytest.raises(ValueError, match="GEMINI_API_KEY가 설정되지 않았습니다"):
        GeminiAdapter(api_key="", model_name="test")


def test_gemini_adapter_creation_success():
    """GeminiAdapter가 성공적으로 생성되는지 테스트"""
    adapter = GeminiAdapter(
        api_key="fake-api-key", 
        model_name="test-model"
    )
    assert adapter.model_name == "test-model"
    assert adapter.api_key == "fake-api-key"


def test_get_llm_returns_correct_instance():
    """get_llm이 올바른 인스턴스를 반환하는지 테스트"""
    adapter = GeminiAdapter(
        api_key="fake-api-key", 
        model_name="test-model"
    )
    llm = adapter.get_llm()
    # HttpGeminiWrapper 인스턴스 확인
    from src.infrastructure.llm.http_gemini_wrapper import HttpGeminiWrapper
    assert isinstance(llm, HttpGeminiWrapper)


class TestGeminiAdapter:
    """GeminiAdapter 테스트"""

    def test_init_success(self):
        """초기화 성공 테스트"""
        adapter = GeminiAdapter(
            api_key="test-key", 
            model_name="test-model"
        )
        assert adapter.model_name == "test-model"
        assert adapter.api_key == "test-key"

    def test_init_with_custom_params(self):
        """커스텀 파라미터로 초기화 테스트"""
        adapter = GeminiAdapter(
            api_key="test-key", 
            model_name="custom-model"
        )
        assert adapter.model_name == "custom-model"

    def test_init_missing_api_key(self):
        """API 키 누락 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="GEMINI_API_KEY가 설정되지 않았습니다"):
            GeminiAdapter(api_key="", model_name="test")

    def test_get_llm(self):
        """LLM 객체 반환 테스트"""
        adapter = GeminiAdapter(
            api_key="test-key", 
            model_name="test-model"
        )
        llm = adapter.get_llm()

        from src.infrastructure.llm.http_gemini_wrapper import HttpGeminiWrapper
        assert isinstance(llm, HttpGeminiWrapper)
        assert llm.model_name == "test-model"

    @patch('src.infrastructure.llm.http_gemini_wrapper.HttpGeminiWrapper.invoke')
    def test_llm_invoke(self, mock_invoke):
        """LLM invoke 메서드 테스트"""
        mock_invoke.return_value = "test response"
        
        adapter = GeminiAdapter(
            api_key="test-key", 
            model_name="test-model"
        )
        llm = adapter.get_llm()
        
        result = llm.invoke("test prompt")
        assert result == "test response"
        mock_invoke.assert_called_once_with("test prompt")