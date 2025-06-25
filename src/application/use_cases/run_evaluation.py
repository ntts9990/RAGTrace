"""
Refactored Run Evaluation Use Case using Command Pattern

Command 패턴을 사용한 리팩토링된 평가 실행 유스케이스입니다.
"""

from typing import Any, Optional, TYPE_CHECKING

from src.application.ports import LlmPort
from src.application.services.data_validator import DataContentValidator
from src.application.services.generation_service import GenerationService
from src.application.services.result_conversion_service import ResultConversionService
from src.domain import EvaluationResult
from src.domain.prompts import PromptType

from .commands import (
    EvaluationPipeline,
    LoadDataCommand,
    ValidateDataCommand,
    GenerateAnswersCommand,
    RunEvaluationCommand,
    ConvertResultCommand
)

if TYPE_CHECKING:
    from src.infrastructure.repository import FileRepositoryFactory


class RunEvaluationUseCase:
    """Command 패턴을 사용한 리팩토링된 평가 실행 유스케이스"""

    def __init__(
        self,
        llm_port: LlmPort,
        evaluation_runner_factory: Any,  # RagasEvalAdapter 인스턴스
        repository_factory: "FileRepositoryFactory",
        data_validator: DataContentValidator,
        generation_service: GenerationService,
        result_conversion_service: ResultConversionService,
    ):
        self.llm_port = llm_port
        self.evaluation_runner_factory = evaluation_runner_factory
        self.repository_factory = repository_factory
        self.data_validator = data_validator
        self.generation_service = generation_service
        self.result_conversion_service = result_conversion_service
        
        # 파이프라인 초기화
        self.pipeline = self._create_pipeline()

    def _create_pipeline(self) -> EvaluationPipeline:
        """평가 파이프라인 생성"""
        return (EvaluationPipeline()
                .add_command(LoadDataCommand(self.repository_factory))
                .add_command(ValidateDataCommand(self.data_validator))
                .add_command(GenerateAnswersCommand(self.generation_service))
                .add_command(RunEvaluationCommand(self.evaluation_runner_factory))
                .add_command(ConvertResultCommand(self.result_conversion_service)))

    def execute(
        self, 
        dataset_name: str, 
        prompt_type: Optional[PromptType] = None
    ) -> EvaluationResult:
        """
        평가를 실행하고 결과를 반환합니다.

        Args:
            dataset_name: 평가할 데이터셋 이름
            prompt_type: 사용할 프롬프트 타입 (선택사항)

        Returns:
            EvaluationResult: 평가 결과 엔티티

        Raises:
            EvaluationError: 평가 실행 중 오류 발생 시
        """
        return self.pipeline.execute(dataset_name, prompt_type)
    
    def get_pipeline_info(self) -> str:
        """파이프라인 정보 반환"""
        return self.pipeline.get_pipeline_info()

