import pytest

from src.domain.value_objects.metrics import (
    DEFAULT_THRESHOLDS,
    MetricLevel,
    MetricScore,
    MetricThresholds,
)


# MetricScore 테스트
def test_metric_score_creation_success():
    """MetricScore가 유효한 값으로 성공적으로 생성되는지 테스트"""
    score = MetricScore(0.85)
    assert score.value == 0.85


@pytest.mark.parametrize("invalid_score", [-0.1, 1.1])
def test_metric_score_creation_invalid(invalid_score):
    """MetricScore가 유효하지 않은 값으로 생성 시 ValueError를 발생하는지 테스트"""
    with pytest.raises(ValueError, match="Metric score must be between 0.0 and 1.0"):
        MetricScore(invalid_score)


@pytest.mark.parametrize(
    "score_value, expected_level",
    [
        (0.95, MetricLevel.EXCELLENT),
        (0.88, MetricLevel.GOOD),
        (0.72, MetricLevel.FAIR),
        (0.55, MetricLevel.POOR),
    ],
)
def test_metric_score_get_level(score_value, expected_level):
    """get_level 메소드가 올바른 성능 수준을 반환하는지 테스트"""
    score = MetricScore(score_value)
    thresholds = MetricThresholds(excellent=0.9, good=0.8, fair=0.7)
    assert score.get_level(thresholds) == expected_level


# MetricThresholds 테스트
def test_metric_thresholds_creation_success():
    """MetricThresholds가 유효한 값으로 성공적으로 생성되는지 테스트"""
    thresholds = MetricThresholds(excellent=0.9, good=0.7, fair=0.5)
    assert thresholds.excellent == 0.9


@pytest.mark.parametrize(
    "invalid_thresholds",
    [
        {"excellent": 0.8, "good": 0.9, "fair": 0.7},  # good > excellent
        {"excellent": 0.9, "good": 0.7, "fair": 0.8},  # fair > good
        {"excellent": 1.1, "good": 0.8, "fair": 0.7},  # excellent > 1.0
        {"excellent": 0.9, "good": -0.1, "fair": -0.2},  # good < 0.0
    ],
)
def test_metric_thresholds_creation_invalid(invalid_thresholds):
    """MetricThresholds가 유효하지 않은 순서나 범위의 값으로 생성 시 ValueError를 발생하는지 테스트"""
    with pytest.raises(ValueError, match="Thresholds must be in ascending order"):
        MetricThresholds(**invalid_thresholds)


def test_default_thresholds_are_valid():
    """DEFAULT_THRESHOLDS에 정의된 모든 임계값이 유효한지 테스트"""
    try:
        for name, thresholds in DEFAULT_THRESHOLDS.items():
            # 객체 생성 자체가 유효성 검사를 수행함
            assert isinstance(thresholds, MetricThresholds)
    except ValueError as e:
        pytest.fail(f"DEFAULT_THRESHOLDS validation failed: {e}")
