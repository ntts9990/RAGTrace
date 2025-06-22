"""
Main Container

모든 컨테이너 컴포넌트를 통합하는 메인 컨테이너입니다.
"""

from typing import Tuple

from src.domain.prompts import PromptType
from src.application.use_cases import RunEvaluationUseCase
from src.application.ports.llm import LlmPort
from langchain_core.embeddings import Embeddings

from .configuration_container import ConfigurationContainer
from .service_registry import ServiceRegistry
from .providers.llm_provider_factory import LlmProviderFactory
from .providers.embedding_provider_factory import EmbeddingProviderFactory
from .factories.evaluation_use_case_factory import EvaluationUseCaseFactory, EvaluationRequest


class MainContainer:
    """메인 DI 컨테이너 - 모든 컴포넌트를 통합"""
    
    def __init__(self):
        
        # 하위 컨테이너들 초기화
        self.configuration = ConfigurationContainer()
        self.service_registry = ServiceRegistry()
        self.llm_factory = LlmProviderFactory(self.configuration)
        self.embedding_factory = EmbeddingProviderFactory(self.configuration)
        self.use_case_factory = EvaluationUseCaseFactory(
            self.llm_factory,
            self.embedding_factory,
            self.service_registry
        )
    
    def create_evaluation_use_case(self, request: EvaluationRequest) -> Tuple[RunEvaluationUseCase, LlmPort, Embeddings]:
        """평가 유스케이스 생성"""
        return self.use_case_factory.create_use_case(request)


# 전역 컨테이너 인스턴스
container = MainContainer()