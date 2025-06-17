"""Run evaluation use case"""

from typing import Any, Optional, TYPE_CHECKING

from datasets import Dataset

from src.application.ports import (
    EvaluationRepositoryPort,
    EvaluationRunnerPort,
    LlmPort,
)
from src.domain import EvaluationData, EvaluationError, EvaluationResult
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

            # 3. 답변 생성 (Generation 단계)
            print("답변을 생성하는 중...")
            for i, data in enumerate(evaluation_data_list):
                if not data.answer:  # 답변이 없는 경우에만 생성
                    try:
                        generated_answer = self.llm_port.generate_answer(
                            question=data.question,
                            contexts=data.contexts
                        )
                        data.answer = generated_answer
                        print(f"답변 생성 완료 ({i+1}/{len(evaluation_data_list)})")
                    except Exception as e:
                        print(f"답변 생성 실패 ({i+1}/{len(evaluation_data_list)}): {e}")
                        # 실패한 경우 빈 답변으로 설정
                        data.answer = ""

            # 4. Ragas 데이터셋 형식으로 변환 (답변이 포함된 상태)
            dataset = self._convert_to_dataset(evaluation_data_list)

            # 5. LLM 객체 가져오기 (평가를 위해서만 사용)
            llm = self.llm_port.get_llm()

            # 6. 평가 실행 (Evaluation 단계)
            print("평가를 수행하는 중...")
            result_dict = evaluation_runner.evaluate(dataset=dataset, llm=llm)

            # 7. 결과 검증 및 변환
            return self._validate_and_convert_result(result_dict)

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
        self, result_dict: dict[str, Any]
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

        # 결과가 모두 0인지 확인
        metric_values = [result_dict.get(metric, 0.0) for metric in required_metrics]
        if all(v == 0.0 for v in metric_values):
            print("\n경고: 모든 평가 점수가 0입니다. 다음을 확인해주세요:")
            print("1. API 키가 올바르게 설정되었는지 확인")
            print("2. Gemini API 할당량이 남아있는지 확인")
            print("3. 네트워크 연결이 정상인지 확인")
            print("4. 평가 데이터 형식이 올바른지 확인")

        # EvaluationResult 생성
        return EvaluationResult(
            faithfulness=result_dict["faithfulness"],
            answer_relevancy=result_dict["answer_relevancy"],
            context_recall=result_dict["context_recall"],
            context_precision=result_dict["context_precision"],
            ragas_score=result_dict.get("ragas_score", 0.0),
            individual_scores=result_dict.get("individual_scores"),
            metadata={"timestamp": result_dict.get("timestamp")},
        )
