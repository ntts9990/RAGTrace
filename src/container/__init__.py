"""
Dependency Injection Container Package

이 패키지는 RAGTrace 애플리케이션의 모든 의존성을 관리합니다.
"""

from .configuration_container import ConfigurationContainer
from .service_registry import ServiceRegistry
from .providers.llm_provider_factory import LlmProviderFactory
from .providers.embedding_provider_factory import EmbeddingProviderFactory
from .factories.evaluation_use_case_factory import EvaluationUseCaseFactory
from .main_container import MainContainer, get_container

# 전역 컨테이너 인스턴스 (지연 초기화)
container = get_container()

__all__ = [
    'ConfigurationContainer',
    'ServiceRegistry', 
    'LlmProviderFactory',
    'EmbeddingProviderFactory',
    'EvaluationUseCaseFactory',
    'MainContainer',
    'container',
    'get_container'
]