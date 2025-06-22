"""
Embedding Provider Factory

임베딩 제공자 생성을 담당하는 팩토리입니다.
"""

from typing import Any
from langchain_core.embeddings import Embeddings

from src.config import SUPPORTED_EMBEDDING_TYPES
from src.infrastructure.embedding.gemini_http_adapter import GeminiHttpEmbeddingAdapter
from src.infrastructure.embedding.hcx_adapter import HcxEmbeddingAdapter
from src.infrastructure.embedding.bge_m3_adapter import BgeM3EmbeddingAdapter
from .base_provider_factory import BaseProviderFactory


class EmbeddingProviderFactory(BaseProviderFactory):
    """임베딩 제공자 생성 팩토리"""
    
    def __init__(self, configuration_container):
        super().__init__(configuration_container)
        self._instances = {}  # Singleton 인스턴스 캐시
    
    def create_provider(self, embedding_type: str) -> Embeddings:
        """임베딩 제공자 생성"""
        if embedding_type not in SUPPORTED_EMBEDDING_TYPES:
            raise ValueError(f"지원하지 않는 임베딩 타입: {embedding_type}. 지원되는 타입: {SUPPORTED_EMBEDDING_TYPES}")
        
        if not self._config_container.validate_embedding_config(embedding_type):
            raise ValueError(f"임베딩 '{embedding_type}'의 설정이 유효하지 않습니다. 설정을 확인하세요.")
        
        # Singleton 패턴 적용
        if embedding_type in self._instances:
            return self._instances[embedding_type]
        
        config = self._config_container.get_embedding_config(embedding_type)
        
        if embedding_type == "gemini":
            instance = GeminiHttpEmbeddingAdapter(
                api_key=config["api_key"],
                model_name=config["model_name"]
            )
        elif embedding_type == "hcx":
            instance = HcxEmbeddingAdapter(
                api_key=config["api_key"]
            )
        elif embedding_type == "bge_m3":
            instance = BgeM3EmbeddingAdapter(
                model_path=config["model_path"],
                device=config["device"]
            )
        else:
            raise ValueError(f"지원하지 않는 임베딩 타입: {embedding_type}")
        
        self._instances[embedding_type] = instance
        return instance
    
    def get_supported_types(self) -> list:
        """지원되는 임베딩 타입 목록 반환"""
        return list(SUPPORTED_EMBEDDING_TYPES)
    
    def is_supported(self, embedding_type: str) -> bool:
        """임베딩 타입 지원 여부 확인"""
        return embedding_type in SUPPORTED_EMBEDDING_TYPES