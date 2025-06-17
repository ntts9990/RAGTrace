"""Run evaluation use case"""

from typing import Any, Optional, TYPE_CHECKING

from datasets import Dataset

from src.application.ports import (
    EvaluationRepositoryPort,
    EvaluationRunnerPort,
    LlmPort,
)
from src.application.services.data_validator import DataContentValidator
from src.domain import EvaluationData, EvaluationError, EvaluationResult
from src.domain.exceptions import DataValidationError
from src.domain.prompts import PromptType

if TYPE_CHECKING:
    from src.factories import FileRepositoryFactory, RagasEvalAdapterFactory


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
            generation_failures = 0
            generation_successes = 0
            api_failure_details = []
            
            for i, data in enumerate(evaluation_data_list):
                if not data.answer:  # 답변이 없는 경우에만 생성
                    try:
                        generated_answer = self.llm_port.generate_answer(
                            question=data.question,
                            contexts=data.contexts
                        )
                        data.answer = generated_answer
                        generation_successes += 1
                        print(f"답변 생성 완료 ({i+1}/{len(evaluation_data_list)})")
                    except Exception as e:
                        generation_failures += 1
                        # 상세한 실패 정보 수집
                        failure_detail = {
                            "item_index": i + 1,
                            "question": data.question[:100] + "..." if len(data.question) > 100 else data.question,
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                        api_failure_details.append(failure_detail)
                        
                        print(f"답변 생성 실패 ({i+1}/{len(evaluation_data_list)}): {e}")
                        # 실패한 경우 빈 답변으로 설정
                        data.answer = ""
                else:
                    generation_successes += 1

            # 5. Ragas 데이터셋 형식으로 변환 (답변이 포함된 상태)
            dataset = self._convert_to_dataset(evaluation_data_list)

            # 6. LLM 객체 가져오기 (평가를 위해서만 사용)
            llm = self.llm_port.get_llm()

            # 7. 평가 실행 (Evaluation 단계)
            print("평가를 수행하는 중...")
            result_dict = evaluation_runner.evaluate(dataset=dataset, llm=llm)

            # 8. 결과 검증 및 변환
            return self._validate_and_convert_result(
                result_dict, 
                generation_failures, 
                generation_successes, 
                api_failure_details
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

    def _validate_and_convert_result(
        self, 
        result_dict: dict[str, Any],
        generation_failures: int = 0,
        generation_successes: int = 0,
        api_failure_details: list[dict] = None
    ) -> EvaluationResult:
        """결과 딕셔너리를 검증하고 EvaluationResult로 변환"""
        if not result_dict:
            raise EvaluationError("평가 결과가 비어있습니다.")

        # 필수 메트릭 확인
        required_metrics = [
            "faithfulness",
            "answer_relevancy",
            "context_recall",
            "context_precision",
        ]
        for metric in required_metrics:
            if metric not in result_dict:
                raise EvaluationError(f"필수 메트릭이 누락되었습니다: {metric}")

        # 결과가 모두 0인지 확인 및 생성 실패와 연관성 체크
        metric_values = [result_dict.get(metric, 0.0) for metric in required_metrics]
        if all(v == 0.0 for v in metric_values):
            warning_message = "\n경고: 모든 평가 점수가 0입니다."
            if generation_failures > 0:
                warning_message += f"\n답변 생성 실패가 {generation_failures}건 발생했습니다."
            warning_message += "\n다음을 확인해주세요:"
            warning_message += "\n1. API 키가 올바르게 설정되었는지 확인"
            warning_message += "\n2. Gemini API 할당량이 남아있는지 확인"
            warning_message += "\n3. 네트워크 연결이 정상인지 확인"
            warning_message += "\n4. 평가 데이터 형식이 올바른지 확인"
            print(warning_message)

        # 생성 실패에 대한 경고
        if generation_failures > 0:
            total_attempts = generation_failures + generation_successes
            failure_rate = generation_failures / total_attempts * 100
            print(f"\n⚠️  답변 생성 실패: {generation_failures}/{total_attempts}건 ({failure_rate:.1f}%)")
            print("   이는 평가 결과의 신뢰도에 영향을 줄 수 있습니다.")

        # EvaluationResult 생성
        return EvaluationResult(
            faithfulness=result_dict["faithfulness"],
            answer_relevancy=result_dict["answer_relevancy"],
            context_recall=result_dict["context_recall"],
            context_precision=result_dict["context_precision"],
            ragas_score=result_dict.get("ragas_score", 0.0),
            individual_scores=result_dict.get("individual_scores"),
            metadata=result_dict.get("metadata", {}),
            generation_failures=generation_failures,
            generation_successes=generation_successes,
            api_failure_details=api_failure_details or [],
        )
