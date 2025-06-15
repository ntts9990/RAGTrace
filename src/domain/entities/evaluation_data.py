"""Evaluation data entity"""

from dataclasses import dataclass
from typing import List


@dataclass
class EvaluationData:
    """RAGAs 평가를 위한 데이터셋의 단일 항목을 나타내는 엔티티"""

    question: str
    contexts: List[str]
    answer: str
    ground_truth: str

    def __post_init__(self):
        """데이터 유효성 검증"""
        if not self.question.strip():
            raise ValueError("Question cannot be empty")
        if not self.contexts:
            raise ValueError("Contexts cannot be empty")
        if not self.answer.strip():
            raise ValueError("Answer cannot be empty")
        if not self.ground_truth.strip():
            raise ValueError("Ground truth cannot be empty")
