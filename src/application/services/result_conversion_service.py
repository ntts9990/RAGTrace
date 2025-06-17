"""평가 결과 변환 서비스"""

from typing import Any, Dict, List

from src.domain.entities.evaluation_result import EvaluationResult
from src.domain.exceptions.evaluation_exceptions import EvaluationError


class ResultConversionService:
    """평가 결과 변환 및 검증을 담당하는 애플리케이션 서비스"""
    
    def validate_and_convert_result(
        self, 
        result_dict: Dict[str, Any],
        generation_failures: int = 0,
        generation_successes: int = 0,
        api_failure_details: List[dict] = None
    ) -> EvaluationResult:
        """
        결과 딕셔너리를 검증하고 EvaluationResult로 변환합니다.
        
        Args:
            result_dict: Ragas 평가 결과 딕셔너리
            generation_failures: 답변 생성 실패 건수
            generation_successes: 답변 생성 성공 건수
            api_failure_details: API 실패 상세 정보
            
        Returns:
            EvaluationResult: 검증된 평가 결과
            
        Raises:
            EvaluationError: 결과 검증 실패 시
        """
        # 1. 기본 검증
        self._validate_result_dict(result_dict)
        
        # 2. 메트릭 값 검증 및 경고
        self._check_metric_values(result_dict, generation_failures)
        
        # 3. 생성 실패 경고
        self._warn_generation_failures(generation_failures, generation_successes)
        
        # 4. EvaluationResult 객체 생성
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
    
    def _validate_result_dict(self, result_dict: Dict[str, Any]) -> None:
        """결과 딕셔너리의 기본 유효성을 검증합니다."""
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
    
    def _check_metric_values(
        self, 
        result_dict: Dict[str, Any], 
        generation_failures: int
    ) -> None:
        """메트릭 값들을 검증하고 필요시 경고를 출력합니다."""
        required_metrics = [
            "faithfulness",
            "answer_relevancy", 
            "context_recall",
            "context_precision",
        ]
        
        # 결과가 모두 0인지 확인 및 생성 실패와 연관성 체크
        metric_values = [result_dict.get(metric, 0.0) for metric in required_metrics]
        if all(v == 0.0 for v in metric_values):
            warning_message = "\\n경고: 모든 평가 점수가 0입니다."
            if generation_failures > 0:
                warning_message += f"\\n답변 생성 실패가 {generation_failures}건 발생했습니다."
            warning_message += "\\n다음을 확인해주세요:"
            warning_message += "\\n1. API 키가 올바르게 설정되었는지 확인"
            warning_message += "\\n2. Gemini API 할당량이 남아있는지 확인"
            warning_message += "\\n3. 네트워크 연결이 정상인지 확인"
            warning_message += "\\n4. 평가 데이터 형식이 올바른지 확인"
            print(warning_message)
    
    def _warn_generation_failures(
        self, 
        generation_failures: int, 
        generation_successes: int
    ) -> None:
        """답변 생성 실패에 대한 경고를 출력합니다."""
        if generation_failures > 0:
            total_attempts = generation_failures + generation_successes
            failure_rate = generation_failures / total_attempts * 100
            print(f"\\n⚠️  답변 생성 실패: {generation_failures}/{total_attempts}건 ({failure_rate:.1f}%)")
            print("   이는 평가 결과의 신뢰도에 영향을 줄 수 있습니다.")