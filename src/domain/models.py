from dataclasses import dataclass
from typing import List


@dataclass
class EvaluationData:
    """RAGAs 평가를 위한 데이터셋의 단일 항목을 나타내는 데이터 클래스"""
    question: str
    contexts: List[str]
    answer: str
    ground_truth: str 