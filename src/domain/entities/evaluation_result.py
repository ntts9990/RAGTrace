"""Evaluation result entity"""

from dataclasses import dataclass
from typing import Any


@dataclass
class EvaluationResult:
    """RAGAS 평가 결과를 나타내는 엔티티"""

    faithfulness: float
    answer_relevancy: float
    context_recall: float
    context_precision: float
    ragas_score: float
    answer_correctness: float | None = None  # answer_correctness 메트릭 추가
    individual_scores: list[dict[str, float]] | None = None
    metadata: dict[str, Any] | None = None
    generation_failures: int = 0
    generation_successes: int = 0
    api_failure_details: list[dict[str, Any]] | None = None

    def __post_init__(self):
        """평가 결과 유효성 검증"""
        for metric_name, score in [
            ("faithfulness", self.faithfulness),
            ("answer_relevancy", self.answer_relevancy),
            ("context_recall", self.context_recall),
            ("context_precision", self.context_precision),
            ("ragas_score", self.ragas_score),
        ]:
            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"{metric_name} must be between 0.0 and 1.0, got {score}"
                )

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환"""
        result = {
            "faithfulness": self.faithfulness,
            "answer_relevancy": self.answer_relevancy,
            "context_recall": self.context_recall,
            "context_precision": self.context_precision,
            "ragas_score": self.ragas_score,
            "generation_failures": self.generation_failures,
            "generation_successes": self.generation_successes,
        }

        # answer_correctness가 있으면 추가
        if self.answer_correctness is not None:
            result["answer_correctness"] = self.answer_correctness

        if self.individual_scores:
            result["individual_scores"] = self.individual_scores
        if self.metadata:
            result["metadata"] = self.metadata
        if self.api_failure_details:
            result["api_failure_details"] = self.api_failure_details

        return result
    
    @property
    def total_generation_attempts(self) -> int:
        """총 답변 생성 시도 횟수"""
        return self.generation_failures + self.generation_successes
    
    @property
    def generation_success_rate(self) -> float:
        """답변 생성 성공률 (0.0 ~ 1.0)"""
        if self.total_generation_attempts == 0:
            return 1.0
        return self.generation_successes / self.total_generation_attempts
    
    def has_generation_issues(self) -> bool:
        """답변 생성에 문제가 있는지 확인"""
        return self.generation_failures > 0
