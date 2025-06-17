"""애플리케이션의 의존성 주입(DI) 컨테이너

이 모듈은 애플리케이션의 모든 서비스(유스케이스, 어댑터 등)의
인스턴스를 생성하고 필요한 의존성을 주입하는 역할을 중앙에서 관리합니다.
"""

from src.application.ports import LlmPort
from src.application.use_cases import RunEvaluationUseCase
from src.config import settings
from src.factories import FileRepositoryFactory, RagasEvalAdapterFactory
from src.infrastructure.llm.gemini_adapter import GeminiAdapter


class Container:
    """상태 없는 의존성 주입 컨테이너"""

    def __init__(self):
        # 설정에서 값 가져오기
        self.settings = settings
        
        # 모든 어댑터를 명시적으로 생성
        self.llm_adapter: LlmPort = GeminiAdapter(
            api_key=self.settings.GEMINI_API_KEY,
            model_name=self.settings.GEMINI_MODEL_NAME,
            requests_per_minute=self.settings.GEMINI_REQUESTS_PER_MINUTE,
        )
        
        # 팩토리 인스턴스 생성
        self.ragas_eval_adapter_factory = RagasEvalAdapterFactory(
            embedding_model_name=self.settings.GEMINI_EMBEDDING_MODEL_NAME,
            api_key=self.settings.GEMINI_API_KEY,
            embedding_requests_per_minute=self.settings.EMBEDDING_REQUESTS_PER_MINUTE,
        )
        
        self.repository_factory = FileRepositoryFactory()
        
        # 유스케이스도 명시적으로 생성
        self.run_evaluation_use_case = RunEvaluationUseCase(
            llm_port=self.llm_adapter,
            evaluation_runner_factory=self.ragas_eval_adapter_factory,
            repository_factory=self.repository_factory,
        )


# 기본 컨테이너 인스턴스를 생성하여 다른 모듈에서 사용
container = Container()
