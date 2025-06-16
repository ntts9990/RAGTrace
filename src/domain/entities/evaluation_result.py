"""Evaluation result entity"""

from dataclasses import dataclass
from typing import Any


@dataclass
class EvaluationResult:
    """RAGAs 평가 결과를 나타내는 엔티티"""

    faithfulness: float
    answer_relevancy: float
    context_recall: float
    context_precision: float
    ragas_score: float
    individual_scores: list[dict[str, float]] | None = None
    metadata: dict[str, Any] | None = None

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
        }

        if self.individual_scores:
            result["individual_scores"] = self.individual_scores
        if self.metadata:
            result["metadata"] = self.metadata

        return result
