"""Run evaluation use case"""
from typing import Dict, Any
from datasets import Dataset

from src.domain import EvaluationData, EvaluationResult, EvaluationError
from src.application.ports import LlmPort, EvaluationRepositoryPort, EvaluationRunnerPort


class RunEvaluationUseCase:
    """평가 실행 유스케이스"""

    def __init__(
        self,
        llm_port: LlmPort,
        repository_port: EvaluationRepositoryPort,
        evaluation_runner: EvaluationRunnerPort,
    ):
        self.llm_port = llm_port
        self.repository_port = repository_port
        self.evaluation_runner = evaluation_runner

    def execute(self) -> EvaluationResult:
        """
        평가를 실행하고 결과를 반환합니다.
        
        Returns:
            EvaluationResult: 평가 결과 엔티티
            
        Raises:
            EvaluationError: 평가 실행 중 오류 발생 시
        """
        try:
            # 1. 데이터 로드
            evaluation_data_list = self.repository_port.load_data()
            if not evaluation_data_list:
                raise EvaluationError("평가 데이터가 없습니다.")

            print(f"평가할 데이터 개수: {len(evaluation_data_list)}개")

            # 2. Ragas 데이터셋 형식으로 변환
            dataset = self._convert_to_dataset(evaluation_data_list)

            # 3. LLM 객체 가져오기
            llm = self.llm_port.get_llm()

            # 4. 평가 실행
            result_dict = self.evaluation_runner.evaluate(
                dataset=dataset,
                llm=llm
            )
            
            # 5. 결과 검증 및 변환
            return self._validate_and_convert_result(result_dict)
            
        except Exception as e:
            if isinstance(e, EvaluationError):
                raise
            raise EvaluationError(f"평가 실행 중 오류 발생: {str(e)}") from e

    def _convert_to_dataset(self, evaluation_data_list: list[EvaluationData]) -> Dataset:
        """평가 데이터를 Ragas Dataset 형식으로 변환"""
        data_dict = {
            "question": [d.question for d in evaluation_data_list],
            "contexts": [d.contexts for d in evaluation_data_list],
            "answer": [d.answer for d in evaluation_data_list],
            "ground_truth": [d.ground_truth for d in evaluation_data_list],
        }
        return Dataset.from_dict(data_dict)

    def _validate_and_convert_result(self, result_dict: Dict[str, Any]) -> EvaluationResult:
        """결과 딕셔너리를 검증하고 EvaluationResult로 변환"""
        if not result_dict:
            raise EvaluationError("평가 결과가 비어있습니다.")
        
        # 필수 메트릭 확인
        required_metrics = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
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
            metadata={"timestamp": result_dict.get("timestamp")}
        )