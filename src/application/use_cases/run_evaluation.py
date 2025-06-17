"""Run evaluation use case"""

from typing import Any, Optional, TYPE_CHECKING

from datasets import Dataset

from src.application.ports import (
    EvaluationRepositoryPort,
    EvaluationRunnerPort,
    LlmPort,
)
from src.application.services.data_validator import DataContentValidator
from src.application.services.generation_service import GenerationService
from src.application.services.result_conversion_service import ResultConversionService
from src.domain import EvaluationData, EvaluationError, EvaluationResult
from src.domain.exceptions import DataValidationError
from src.domain.prompts import PromptType

if TYPE_CHECKING:
    from src.infrastructure.evaluation import RagasEvalAdapterFactory
    from src.infrastructure.repository import FileRepositoryFactory


class RunEvaluationUseCase:
    """평가 실행 유스케이스"""

    def __init__(
        self,
        llm_port: LlmPort,
        evaluation_runner_factory: "RagasEvalAdapterFactory",
        repository_factory: "FileRepositoryFactory",
    ):
        self.llm_port = llm_port
        self.evaluation_runner_factory = evaluation_runner_factory
        self.repository_factory = repository_factory
        self.data_validator = DataContentValidator()
        self.generation_service = GenerationService(answer_generator=llm_port)
        self.result_conversion_service = ResultConversionService()

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
        try:
            # 1. 필요한 서비스 인스턴스 생성
            repository_port = self.repository_factory.create_repository(dataset_name)
            evaluation_runner = self.evaluation_runner_factory.create_evaluator(prompt_type)

            # 2. 데이터 로드
            evaluation_data_list = repository_port.load_data()
            if not evaluation_data_list:
                raise EvaluationError("평가 데이터가 없습니다.")

            print(f"평가할 데이터 개수: {len(evaluation_data_list)}개")

            # 3. 데이터 내용 사전 검증
            print("데이터 내용을 검증하는 중...")
            validation_report = self.data_validator.validate_data_list(evaluation_data_list)
            
            if validation_report.has_errors or validation_report.has_warnings:
                validation_message = self.data_validator.create_user_friendly_report(validation_report)
                print(f"\n{validation_message}")
                
                if validation_report.has_errors:
                    # 에러가 있는 경우 사용자에게 선택권 제공 (실제 UI에서는 버튼으로 처리)
                    print("\n❓ 오류가 있는 데이터로 평가를 계속 진행하시겠습니까?")
                    print("   품질이 낮은 결과가 나올 수 있습니다.")
                    # 현재는 경고만 표시하고 계속 진행
                elif validation_report.has_warnings:
                    print("\n💡 경고사항이 있지만 평가를 계속 진행합니다.")

            # 4. 답변 생성 (Generation 단계)
            print("답변을 생성하는 중...")
            generation_result = self.generation_service.generate_missing_answers(evaluation_data_list)

            # 5. Ragas 데이터셋 형식으로 변환 (답변이 포함된 상태)
            dataset = self._convert_to_dataset(evaluation_data_list)

            # 6. LLM 객체 가져오기 (평가를 위해서만 사용)
            llm = self.llm_port.get_llm()

            # 7. 평가 실행 (Evaluation 단계)
            print("평가를 수행하는 중...")
            result_dict = evaluation_runner.evaluate(dataset=dataset, llm=llm)

            # 8. 결과 검증 및 변환
            return self.result_conversion_service.validate_and_convert_result(
                result_dict, 
                generation_result.failures, 
                generation_result.successes, 
                generation_result.failure_details
            )

        except Exception as e:
            if isinstance(e, EvaluationError):
                raise
            raise EvaluationError(f"평가 실행 중 오류 발생: {str(e)}") from e

    def _convert_to_dataset(
        self, evaluation_data_list: list[EvaluationData]
    ) -> Dataset:
        """평가 데이터를 Ragas Dataset 형식으로 변환"""
        data_dict = {
            "question": [d.question for d in evaluation_data_list],
            "contexts": [d.contexts for d in evaluation_data_list],
            "answer": [d.answer for d in evaluation_data_list],
            "ground_truth": [d.ground_truth for d in evaluation_data_list],
        }
        return Dataset.from_dict(data_dict)

