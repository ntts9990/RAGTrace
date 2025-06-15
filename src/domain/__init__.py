"""Domain layer module"""
from .entities import EvaluationData, EvaluationResult
from .value_objects import MetricScore, MetricThresholds, DEFAULT_THRESHOLDS
from .exceptions import (
    EvaluationError,
    InvalidEvaluationDataError,
    EvaluationTimeoutError,
    LLMConnectionError
)

__all__ = [
    "EvaluationData",
    "EvaluationResult", 
    "MetricScore",
    "MetricThresholds",
    "DEFAULT_THRESHOLDS",
    "EvaluationError",
    "InvalidEvaluationDataError",
    "EvaluationTimeoutError",
    "LLMConnectionError"
]