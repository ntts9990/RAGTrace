"""
Evaluation Use Case Factory

평가 유스케이스 생성을 담당하는 팩토리입니다.
"""

from typing import Optional, Tuple
from dataclasses import dataclass

from src.config import settings
from src.domain.prompts import PromptType
from src.application.use_cases import RunEvaluationUseCase
from src.application.services.generation_service import GenerationService
from src.infrastructure.evaluation import RagasEvalAdapter
from src.application.ports.llm import LlmPort
from langchain_core.embeddings import Embeddings


@dataclass
class EvaluationRequest:
    """평가 요청 데이터"""
    llm_type: Optional[str] = None
    embedding_type: Optional[str] = None
    prompt_type: Optional[PromptType] = None


class EvaluationUseCaseFactory:
    """평가 유스케이스 생성 팩토리"""
    
    def __init__(self, llm_factory, embedding_factory, service_registry):
        self._llm_factory = llm_factory
        self._embedding_factory = embedding_factory
        self._service_registry = service_registry
    
    def create_use_case(self, request: EvaluationRequest) -> Tuple[RunEvaluationUseCase, LlmPort, Embeddings]:
        """평가 유스케이스 생성
        
        Args:
            request: 평가 요청 정보
            
        Returns:
            (use_case, llm_adapter, embedding_adapter) 튜플
        """
        # 기본값 설정
        llm_type = request.llm_type or settings.DEFAULT_LLM
        embedding_type = request.embedding_type or settings.DEFAULT_EMBEDDING
        prompt_type = request.prompt_type
        
        # LLM 어댑터 생성
        llm_adapter = self._llm_factory.create_provider(llm_type)
        
        # 임베딩 어댑터 생성
        embedding_adapter = self._embedding_factory.create_provider(embedding_type)
        
        # GenerationService 생성
        generation_service = GenerationService(answer_generator=llm_adapter)
        
        # RagasEvalAdapter 생성
        ragas_adapter = RagasEvalAdapter(
            llm=llm_adapter,
            embeddings=embedding_adapter,
            prompt_type=prompt_type
        )
        
        # RunEvaluationUseCase 생성
        use_case = RunEvaluationUseCase(
            llm_port=llm_adapter,
            evaluation_runner_factory=ragas_adapter,
            repository_factory=self._service_registry.get_repository_factory(),
            data_validator=self._service_registry.get_data_validator(),
            generation_service=generation_service,
            result_conversion_service=self._service_registry.get_result_conversion_service(),
        )
        
        return use_case, llm_adapter, embedding_adapter
    
    def create_use_case_with_types(self, llm_type: str = None, embedding_type: str = None, 
                                  prompt_type: PromptType = None) -> Tuple[RunEvaluationUseCase, LlmPort, Embeddings]:
        """타입별 평가 유스케이스 생성 (backward compatibility)"""
        request = EvaluationRequest(
            llm_type=llm_type,
            embedding_type=embedding_type,
            prompt_type=prompt_type
        )
        return self.create_use_case(request)