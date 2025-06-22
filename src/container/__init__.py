"""
Container 패키지

의존성 주입 컨테이너를 여러 개의 작은, 집중된 컴포넌트로 분해합니다.
"""

from .configuration_container import ConfigurationContainer
from .service_registry import ServiceRegistry
from .providers.llm_provider_factory import LlmProviderFactory
from .providers.embedding_provider_factory import EmbeddingProviderFactory
from .factories.evaluation_use_case_factory import EvaluationUseCaseFactory
from .main_container import MainContainer

# 전역 컨테이너 인스턴스 및 함수 (backward compatibility)
from .main_container import container, get_evaluation_use_case_with_llm

__all__ = [
    'ConfigurationContainer',
    'ServiceRegistry', 
    'LlmProviderFactory',
    'EmbeddingProviderFactory',
    'EvaluationUseCaseFactory',
    'MainContainer',
    'container',
    'get_evaluation_use_case_with_llm'
]