"""애플리케이션의 의존성 주입(DI) 컨테이너

이 모듈은 애플리케이션의 모든 서비스(유스케이스, 어댑터 등)의
인스턴스를 생성하고 필요한 의존성을 주입하는 역할을 중앙에서 관리합니다.
"""

from src.config import settings
from src.application.use_cases import RunEvaluationUseCase
from src.infrastructure.llm.gemini_adapter import GeminiAdapter
from src.infrastructure.evaluation import RagasEvalAdapter
from src.infrastructure.repository.file_adapter import FileRepositoryAdapter
from src.utils.paths import get_evaluation_data_path

class Container:
    """서비스 인스턴스를 관리하는 컨테이너 클래스"""

    def __init__(self):
        # LLM 어댑터 인스턴스화
        self.llm_adapter = GeminiAdapter(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL_NAME,
            requests_per_minute=settings.GEMINI_REQUESTS_PER_MINUTE
        )

        # Ragas 평가 실행기 인스턴스화
        self.ragas_eval_adapter = RagasEvalAdapter(
            embedding_model_name=settings.GEMINI_EMBEDDING_MODEL_NAME,
            api_key=settings.GEMINI_API_KEY,
            embedding_requests_per_minute=settings.EMBEDDING_REQUESTS_PER_MINUTE,
        )

    def get_run_evaluation_use_case(self, dataset_name: str) -> RunEvaluationUseCase:
        """RunEvaluationUseCase 인스턴스를 생성하여 반환"""
        
        # 데이터셋 경로 확인
        dataset_path = get_evaluation_data_path(dataset_name)
        if not dataset_path:
            raise FileNotFoundError(f"'{dataset_name}' 데이터셋을 찾을 수 없습니다.")

        # 파일 리포지토리 어댑터는 요청 시마다 생성
        file_repository_adapter = FileRepositoryAdapter(file_path=str(dataset_path))
        
        # 유스케이스 인스턴스화 및 의존성 주입
        return RunEvaluationUseCase(
            llm_port=self.llm_adapter,
            repository_port=file_repository_adapter,
            evaluation_runner=self.ragas_eval_adapter,
        )

# 컨테이너 인스턴스를 생성하여 다른 모듈에서 사용
container = Container() 