"""
LLM Provider Factory

LLM 제공자 생성을 담당하는 팩토리입니다.
"""

from typing import Dict, Any

from src.config import SUPPORTED_LLM_TYPES
from src.infrastructure.llm.gemini_adapter import GeminiAdapter
from src.infrastructure.llm.hcx_adapter import HcxAdapter
from src.application.ports.llm import LlmPort
from .base_provider_factory import BaseProviderFactory


class LlmProviderFactory(BaseProviderFactory):
    """LLM 제공자 생성 팩토리"""
    
    def __init__(self, configuration_container):
        super().__init__(configuration_container)
        self._instances = {}  # Singleton 인스턴스 캐시
    
    def create_provider(self, llm_type: str) -> LlmPort:
        """LLM 제공자 생성"""
        if llm_type not in SUPPORTED_LLM_TYPES:
            raise ValueError(f"지원하지 않는 LLM 타입: {llm_type}. 지원되는 타입: {SUPPORTED_LLM_TYPES}")
        
        if not self._config_container.validate_llm_config(llm_type):
            raise ValueError(f"LLM '{llm_type}'의 설정이 유효하지 않습니다. API 키를 확인하세요.")
        
        # Singleton 패턴 적용
        if llm_type in self._instances:
            return self._instances[llm_type]
        
        config = self._config_container.get_llm_config(llm_type)
        
        if llm_type == "gemini":
            instance = GeminiAdapter(
                api_key=config["api_key"],
                model_name=config["model_name"]
            )
        elif llm_type == "hcx":
            instance = HcxAdapter(
                api_key=config["api_key"],
                model_name=config["model_name"]
            )
        else:
            raise ValueError(f"지원하지 않는 LLM 타입: {llm_type}")
        
        self._instances[llm_type] = instance
        return instance
    
    def get_supported_types(self) -> list:
        """지원되는 LLM 타입 목록 반환"""
        return list(SUPPORTED_LLM_TYPES)
    
    def is_supported(self, llm_type: str) -> bool:
        """LLM 타입 지원 여부 확인"""
        return llm_type in SUPPORTED_LLM_TYPES