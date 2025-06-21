"""애플리케이션의 의존성 주입(DI) 컨테이너

이 모듈은 애플리케이션의 모든 서비스(유스케이스, 어댑터 등)의
인스턴스를 생성하고 필요한 의존성을 주입하는 역할을 중앙에서 관리합니다.
"""

from dependency_injector import containers, providers

from src.config import settings
from src.application.use_cases import RunEvaluationUseCase
from src.application.services.data_validator import DataContentValidator
from src.application.services.generation_service import GenerationService
from src.application.services.result_conversion_service import ResultConversionService
from src.infrastructure.evaluation import RagasEvalAdapterFactory
from src.infrastructure.repository import FileRepositoryFactory
from src.infrastructure.llm.gemini_adapter import GeminiAdapter
from src.infrastructure.llm.hcx_adapter import HcxAdapter


class Container(containers.DeclarativeContainer):
    """
    애플리케이션의 의존성 주입(DI) 컨테이너
    """
    config = providers.Configuration()
    config.from_dict(settings.model_dump())

    # --- 어댑터(Adapter) 프로바이더 ---

    # LLM 어댑터
    # 필요 시 컨테이너 외부에서 선택하여 사용할 수 있도록 각 어댑터를 등록
    gemini_adapter = providers.Singleton(
        GeminiAdapter,
        api_key=config.GEMINI_API_KEY,
        model_name=config.GEMINI_MODEL_NAME,
        requests_per_minute=config.GEMINI_REQUESTS_PER_MINUTE,
    )

    hcx_adapter = providers.Singleton(
        HcxAdapter,
        api_key=config.CLOVA_STUDIO_API_KEY,
        model_name=config.HCX_MODEL_NAME,
        requests_per_minute=config.HCX_REQUESTS_PER_MINUTE,
    )

    # 평가 어댑터 팩토리
    ragas_eval_adapter_factory = providers.Factory(
        RagasEvalAdapterFactory,
        embedding_model_name=config.GEMINI_EMBEDDING_MODEL_NAME,
        api_key=config.GEMINI_API_KEY,
        embedding_requests_per_minute=config.EMBEDDING_REQUESTS_PER_MINUTE,
    )

    # 리포지토리 팩토리
    repository_factory = providers.Singleton(FileRepositoryFactory)

    # LLM 선택기 (설정에 따라 기본 LLM 선택)
    default_llm_adapter = providers.Selector(
        config.DEFAULT_LLM,
        gemini=gemini_adapter,
        hcx=hcx_adapter,
    )

    # --- 서비스(Service) 프로바이더 ---
    
    # 데이터 검증 서비스
    data_validator = providers.Singleton(DataContentValidator)
    
    # 결과 변환 서비스
    result_conversion_service = providers.Singleton(ResultConversionService)
    
    # 답변 생성 서비스 (LLM에 의존)
    generation_service = providers.Factory(
        GenerationService,
        answer_generator=default_llm_adapter
    )

    # --- 유스케이스(Use Case) 프로바이더 ---
    
    run_evaluation_use_case = providers.Factory(
        RunEvaluationUseCase,
        llm_port=default_llm_adapter,  # 기본 LLM 어댑터 주입
        evaluation_runner_factory=ragas_eval_adapter_factory,
        repository_factory=repository_factory,
        data_validator=data_validator,
        generation_service=generation_service,
        result_conversion_service=result_conversion_service,
    )

# 전역 컨테이너 인스턴스
container = Container()


def get_evaluation_use_case_with_llm(llm_type: str = None):
    """런타임에 특정 LLM을 선택하여 평가 유스케이스를 생성"""
    if llm_type is None:
        # 기본 LLM 사용
        return container.run_evaluation_use_case()
    
    # 특정 LLM 선택
    if llm_type == "gemini":
        llm_adapter = container.gemini_adapter()
    elif llm_type == "hcx":
        llm_adapter = container.hcx_adapter()
    else:
        raise ValueError(f"지원하지 않는 LLM 타입: {llm_type}")
    
    # 선택된 LLM으로 유스케이스 생성 (모든 의존성 주입)
    from src.application.use_cases import RunEvaluationUseCase
    from src.application.services.generation_service import GenerationService
    
    # 선택된 LLM으로 GenerationService 생성
    generation_service = GenerationService(answer_generator=llm_adapter)
    
    return RunEvaluationUseCase(
        llm_port=llm_adapter,
        evaluation_runner_factory=container.ragas_eval_adapter_factory(),
        repository_factory=container.repository_factory(),
        data_validator=container.data_validator(),
        generation_service=generation_service,
        result_conversion_service=container.result_conversion_service(),
    )
