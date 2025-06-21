"""애플리케이션의 의존성 주입(DI) 컨테이너

이 모듈은 애플리케이션의 모든 서비스(유스케이스, 어댑터 등)의
인스턴스를 생성하고 필요한 의존성을 주입하는 역할을 중앙에서 관리합니다.
"""

from dependency_injector import containers, providers
from src.infrastructure.embedding.gemini_http_adapter import GeminiHttpEmbeddingAdapter
from src.infrastructure.embedding.bge_m3_adapter import BgeM3EmbeddingAdapter

from src.config import settings, SUPPORTED_LLM_TYPES, SUPPORTED_EMBEDDING_TYPES
from src.domain.prompts import PromptType
from src.application.use_cases import RunEvaluationUseCase
from src.application.services.data_validator import DataContentValidator
from src.application.services.generation_service import GenerationService
from src.application.services.result_conversion_service import ResultConversionService
from src.infrastructure.evaluation import RagasEvalAdapter
from src.infrastructure.repository import FileRepositoryFactory
from src.infrastructure.llm.gemini_adapter import GeminiAdapter
from src.infrastructure.llm.hcx_adapter import HcxAdapter
from src.infrastructure.embedding.hcx_adapter import HcxEmbeddingAdapter


class Container(containers.DeclarativeContainer):
    """애플리케이션의 의존성 주입(DI) 컨테이너"""
    config = providers.Configuration()
    config.from_dict(settings.model_dump())

    # --- 어댑터 프로바이더 ---
    llm_providers = providers.Dict(
        gemini=providers.Singleton(
            GeminiAdapter,
            api_key=config.GEMINI_API_KEY,
            model_name=config.GEMINI_MODEL_NAME,
        ),
        hcx=providers.Singleton(
            HcxAdapter,
            api_key=config.CLOVA_STUDIO_API_KEY,
            model_name=config.HCX_MODEL_NAME,
        ),
    )

    embedding_providers = providers.Dict(
        gemini=providers.Singleton(
            GeminiHttpEmbeddingAdapter,
            api_key=config.GEMINI_API_KEY,
            model_name=config.GEMINI_EMBEDDING_MODEL_NAME,
        ),
        hcx=providers.Singleton(
            HcxEmbeddingAdapter,
            api_key=config.CLOVA_STUDIO_API_KEY,
        ),
        bge_m3=providers.Singleton(
            BgeM3EmbeddingAdapter,
            model_path=config.BGE_M3_MODEL_PATH,
            device=config.BGE_M3_DEVICE,  # None이면 자동 감지
        ),
    )
    
    repository_factory = providers.Singleton(FileRepositoryFactory)
    
    # --- 서비스 프로바이더 ---
    data_validator = providers.Singleton(DataContentValidator)
    result_conversion_service = providers.Singleton(ResultConversionService)
    
    # GenerationService는 LLM 어댑터에 의존하므로 Factory로 만들고, 외부에서 주입받음
    generation_service = providers.Factory(
        GenerationService,
        # answer_generator는 외부에서 주입
    )

    # 평가 어댑터는 LLM과 Embedding 모델에 모두 의존하므로 Factory로 만들고, 외부에서 주입받음
    ragas_eval_adapter = providers.Factory(
        RagasEvalAdapter,
        # llm과 embeddings는 외부에서 주입
    )

    # --- 유스케이스 프로바이더 ---
    run_evaluation_use_case = providers.Factory(
        RunEvaluationUseCase,
        # llm_port, evaluation_runner, generation_service 등은 외부에서 주입
        repository_factory=repository_factory,
        data_validator=data_validator,
        result_conversion_service=result_conversion_service,
    )

# 전역 컨테이너 인스턴스
container = Container()


def get_evaluation_use_case_with_llm(llm_type: str = None, embedding_type: str = None, prompt_type: PromptType = None):
    """런타임에 특정 LLM과 Embedding을 선택하여 평가 유스케이스를 생성"""
    if llm_type is None:
        llm_type = settings.DEFAULT_LLM
    
    if embedding_type is None:
        embedding_type = settings.DEFAULT_EMBEDDING
    
    # LLM 어댑터 선택
    if llm_type not in SUPPORTED_LLM_TYPES:
        raise ValueError(f"지원하지 않는 LLM 타입: {llm_type}. 지원되는 타입: {SUPPORTED_LLM_TYPES}")
    
    llm_adapter = container.llm_providers()[llm_type]
    
    # Embedding 어댑터 선택  
    if embedding_type not in SUPPORTED_EMBEDDING_TYPES:
        raise ValueError(f"지원하지 않는 Embedding 타입: {embedding_type}. 지원되는 타입: {SUPPORTED_EMBEDDING_TYPES}")
    
    embedding_adapter = container.embedding_providers()[embedding_type]       
    
    # 선택된 LLM과 Embedding으로 유스케이스 생성 (모든 의존성 주입)
    from src.application.use_cases import RunEvaluationUseCase
    from src.application.services.generation_service import GenerationService
    
    # 선택된 LLM으로 GenerationService 생성
    generation_service = GenerationService(answer_generator=llm_adapter)
    
    # 선택된 LLM과 Embedding으로 RagasEvalAdapter 생성
    ragas_adapter = container.ragas_eval_adapter(
        llm=llm_adapter,
        embeddings=embedding_adapter,
        prompt_type=prompt_type
    )
    
    return RunEvaluationUseCase(
        llm_port=llm_adapter,
        evaluation_runner_factory=ragas_adapter,
        repository_factory=container.repository_factory(),
        data_validator=container.data_validator(),
        generation_service=generation_service,
        result_conversion_service=container.result_conversion_service(),
    ), llm_adapter, embedding_adapter
