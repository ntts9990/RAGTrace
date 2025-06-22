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
    
    def get_evaluation_use_case_with_llm(self, llm_type: str = None, embedding_type: str = None, 
                                        prompt_type: PromptType = None) -> Tuple[RunEvaluationUseCase, LlmPort, Embeddings]:
        """평가 유스케이스 생성 (backward compatibility)"""
        return self.use_case_factory.create_use_case_with_types(llm_type, embedding_type, prompt_type)
    
    def create_evaluation_use_case(self, request: EvaluationRequest) -> Tuple[RunEvaluationUseCase, LlmPort, Embeddings]:
        """평가 유스케이스 생성 (새로운 인터페이스)"""
        return self.use_case_factory.create_use_case(request)
    
    # Backward compatibility methods
    def llm_providers(self):
        """LLM 제공자 딕셔너리 반환 (backward compatibility)"""
        providers = {}
        for llm_type in self.llm_factory.get_supported_types():
            try:
                providers[llm_type] = self.llm_factory.create_provider(llm_type)
            except ValueError:
                # API 키가 없는 경우 등은 건너뛰기
                continue
        return providers
    
    def embedding_providers(self):
        """임베딩 제공자 딕셔너리 반환 (backward compatibility)"""
        providers = {}
        for embedding_type in self.embedding_factory.get_supported_types():
            try:
                providers[embedding_type] = self.embedding_factory.create_provider(embedding_type)
            except ValueError:
                # API 키가 없는 경우 등은 건너뛰기
                continue
        return providers
    
    def repository_factory(self):
        """리포지토리 팩토리 반환 (backward compatibility)"""
        return self.service_registry.get_repository_factory()
    
    def data_validator(self):
        """데이터 검증기 반환 (backward compatibility)"""
        return self.service_registry.get_data_validator()
    
    def result_conversion_service(self):
        """결과 변환 서비스 반환 (backward compatibility)"""
        return self.service_registry.get_result_conversion_service()
    
    def ragas_eval_adapter(self, llm=None, embeddings=None, prompt_type=None):
        """RAGAS 평가 어댑터 반환 (backward compatibility)"""
        from src.infrastructure.evaluation import RagasEvalAdapter
        return RagasEvalAdapter(llm=llm, embeddings=embeddings, prompt_type=prompt_type)
    
    def run_evaluation_use_case(self, **kwargs):
        """평가 유스케이스 반환 (backward compatibility)"""
        from src.application.use_cases import RunEvaluationUseCase
        return RunEvaluationUseCase(**kwargs)


# 전역 컨테이너 인스턴스 (backward compatibility)
container = MainContainer()


# Backward compatibility function
def get_evaluation_use_case_with_llm(llm_type: str = None, embedding_type: str = None, prompt_type: PromptType = None):
    """런타임에 특정 LLM과 Embedding을 선택하여 평가 유스케이스를 생성 (backward compatibility)"""
    return container.get_evaluation_use_case_with_llm(llm_type, embedding_type, prompt_type)