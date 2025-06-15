"""Metric-related value objects"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class MetricLevel(Enum):
    """메트릭 성능 수준"""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass(frozen=True)
class MetricScore:
    """메트릭 점수 값 객체"""

    value: float

    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Metric score must be between 0.0 and 1.0, got {self.value}")

    def get_level(self, thresholds: "MetricThresholds") -> MetricLevel:
        """임계값을 기준으로 성능 수준 반환"""
        if self.value >= thresholds.excellent:
            return MetricLevel.EXCELLENT
        elif self.value >= thresholds.good:
            return MetricLevel.GOOD
        elif self.value >= thresholds.fair:
            return MetricLevel.FAIR
        else:
            return MetricLevel.POOR


@dataclass(frozen=True)
class MetricThresholds:
    """메트릭 임계값 설정"""

    excellent: float = 0.9
    good: float = 0.8
    fair: float = 0.6

    def __post_init__(self):
        if not (0.0 <= self.fair <= self.good <= self.excellent <= 1.0):
            raise ValueError("Thresholds must be in ascending order between 0.0 and 1.0")


# 기본 임계값 설정
DEFAULT_THRESHOLDS: Dict[str, MetricThresholds] = {
    "faithfulness": MetricThresholds(excellent=0.95, good=0.85, fair=0.7),
    "answer_relevancy": MetricThresholds(excellent=0.9, good=0.8, fair=0.6),
    "context_recall": MetricThresholds(excellent=0.95, good=0.85, fair=0.7),
    "context_precision": MetricThresholds(excellent=0.9, good=0.8, fair=0.6),
}
