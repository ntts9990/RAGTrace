"""Evaluation runner port interface"""

from abc import ABC, abstractmethod
from typing import Any

from datasets import Dataset


class EvaluationRunnerPort(ABC):
    """평가 실행기 포트 인터페이스"""

    @abstractmethod
    def evaluate(self, dataset: Dataset, llm: Any) -> dict[str, Any]:
        """
        주어진 데이터셋과 LLM을 사용하여 평가를 실행합니다.

        Args:
            dataset: 평가할 데이터셋
            llm: 평가에 사용할 LLM 객체

        Returns:
            평가 결과 딕셔너리 (메트릭별 점수 포함)
        """
        pass
