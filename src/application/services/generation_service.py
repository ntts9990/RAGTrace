"""답변 생성 서비스"""

from typing import List

from src.application.ports.llm import AnswerGeneratorPort
from src.domain.entities.evaluation_data import EvaluationData


class GenerationService:
    """답변 생성을 담당하는 애플리케이션 서비스"""
    
    def __init__(self, answer_generator: AnswerGeneratorPort):
        self.answer_generator = answer_generator
    
    def generate_missing_answers(
        self, 
        evaluation_data_list: List[EvaluationData]
    ) -> "GenerationResult":
        """
        평가 데이터 목록에서 누락된 답변을 생성합니다.
        
        Args:
            evaluation_data_list: 평가 데이터 목록
            
        Returns:
            GenerationResult: 생성 결과 (성공/실패 통계 포함)
        """
        generation_failures = 0
        generation_successes = 0
        api_failure_details = []
        
        total_items = len(evaluation_data_list)
        
        for i, data in enumerate(evaluation_data_list):
            if not data.answer:  # 답변이 없는 경우에만 생성
                try:
                    generated_answer = self.answer_generator.generate_answer(
                        question=data.question,
                        contexts=data.contexts
                    )
                    data.answer = generated_answer
                    generation_successes += 1
                    print(f"답변 생성 완료 ({i+1}/{total_items})")
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
                    
                    print(f"답변 생성 실패 ({i+1}/{total_items}): {e}")
                    # 실패한 경우 빈 답변으로 설정
                    data.answer = ""
            else:
                generation_successes += 1
        
        return GenerationResult(
            failures=generation_failures,
            successes=generation_successes,
            failure_details=api_failure_details
        )


class GenerationResult:
    """답변 생성 결과를 나타내는 값 객체"""
    
    def __init__(
        self, 
        failures: int, 
        successes: int, 
        failure_details: List[dict]
    ):
        self.failures = failures
        self.successes = successes
        self.failure_details = failure_details
    
    @property
    def total_attempts(self) -> int:
        """총 시도 횟수"""
        return self.failures + self.successes
    
    @property
    def failure_rate(self) -> float:
        """실패율 (0.0 ~ 1.0)"""
        if self.total_attempts == 0:
            return 0.0
        return self.failures / self.total_attempts
    
    @property
    def success_rate(self) -> float:
        """성공률 (0.0 ~ 1.0)"""
        return 1.0 - self.failure_rate
    
    def has_failures(self) -> bool:
        """실패가 있는지 여부"""
        return self.failures > 0