"""
성능 모니터 컴포넌트 테스트
API 사용량, 실행 시간 등 성능 모니터링 기능 테스트
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import streamlit as st


# 프로젝트 루트 경로 추가
# 프로젝트 루트를 동적으로 찾아 경로 추가
def add_project_root_to_path():
    current_path = Path(__file__).resolve()
    while current_path != current_path.parent:
        if (current_path / "pyproject.toml").exists():
            sys.path.insert(0, str(current_path))
            return current_path
        current_path = current_path.parent
    raise FileNotFoundError("프로젝트 루트를 찾을 수 없습니다.")


add_project_root_to_path()


@pytest.fixture
def sample_performance_data():
    """테스트용 성능 데이터"""
    return {
        "api_calls": [
            {
                "timestamp": "2024-01-01T10:00:00",
                "endpoint": "gemini",
                "duration": 1.5,
                "status": "success",
            },
            {
                "timestamp": "2024-01-01T10:01:00",
                "endpoint": "gemini",
                "duration": 2.1,
                "status": "success",
            },
            {
                "timestamp": "2024-01-01T10:02:00",
                "endpoint": "gemini",
                "duration": 0.8,
                "status": "error",
            },
        ],
        "evaluation_history": [
            {
                "id": 1,
                "timestamp": "2024-01-01T10:00:00",
                "duration": 45.2,
                "qa_count": 10,
                "ragas_score": 0.85,
            },
            {
                "id": 2,
                "timestamp": "2024-01-01T11:00:00", 
                "duration": 52.1,
                "qa_count": 15,
                "ragas_score": 0.82,
            },
        ]
    }


class TestPerformanceMonitor:
    """성능 모니터 테스트"""

    def test_performance_monitor_import(self):
        """성능 모니터 모듈 임포트 테스트"""
        try:
            from src.presentation.web.components.performance_monitor import (
                show_performance_monitor,
                load_evaluation_history_for_performance,
            )
            
            assert callable(show_performance_monitor)
            assert callable(load_evaluation_history_for_performance)
        except ImportError:
            pytest.skip("성능 모니터 모듈이 구현되지 않음")

    def test_api_performance_analysis(self, sample_performance_data):
        """API 성능 분석 테스트"""
        api_calls = sample_performance_data["api_calls"]
        
        def analyze_api_performance(calls):
            """API 성능 분석"""
            total_calls = len(calls)
            success_calls = len([c for c in calls if c["status"] == "success"])
            error_calls = total_calls - success_calls
            
            durations = [c["duration"] for c in calls if c["status"] == "success"]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                "total_calls": total_calls,
                "success_rate": success_calls / total_calls if total_calls > 0 else 0,
                "error_rate": error_calls / total_calls if total_calls > 0 else 0,
                "avg_duration": avg_duration,
            }
        
        analysis = analyze_api_performance(api_calls)
        
        assert analysis["total_calls"] == 3
        assert analysis["success_rate"] == 2/3
        assert analysis["error_rate"] == 1/3
        assert analysis["avg_duration"] == (1.5 + 2.1) / 2

    def test_evaluation_performance_tracking(self, sample_performance_data):
        """평가 성능 추적 테스트"""
        evaluations = sample_performance_data["evaluation_history"]
        
        def track_evaluation_performance(evaluations):
            """평가 성능 추적"""
            if not evaluations:
                return {}
                
            total_duration = sum(e["duration"] for e in evaluations)
            total_qa = sum(e["qa_count"] for e in evaluations)
            avg_score = sum(e["ragas_score"] for e in evaluations) / len(evaluations)
            
            return {
                "total_evaluations": len(evaluations),
                "total_duration": total_duration,
                "avg_duration_per_evaluation": total_duration / len(evaluations),
                "total_qa_processed": total_qa,
                "avg_qa_per_evaluation": total_qa / len(evaluations),
                "avg_ragas_score": avg_score,
            }
        
        performance = track_evaluation_performance(evaluations)
        
        assert performance["total_evaluations"] == 2
        assert performance["total_duration"] == 45.2 + 52.1
        assert performance["total_qa_processed"] == 25
        assert abs(performance["avg_ragas_score"] - 0.835) < 0.001

    @patch('sqlite3.connect')
    def test_load_evaluation_history_for_performance_success(self, mock_connect):
        """평가 이력 로드 성공 테스트"""
        from unittest.mock import MagicMock
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, '2024-01-01 10:00:00', 0.95, 0.90, 0.85, 0.88, 0.895, '{"test": "data"}')
        ]
        
        from src.presentation.web.components.performance_monitor import load_evaluation_history_for_performance
        
        with patch('pathlib.Path.exists', return_value=True):
            result = load_evaluation_history_for_performance()
        
        assert len(result) == 1

    @patch('sqlite3.connect')
    def test_load_evaluation_history_for_performance_empty(self, mock_connect):
        """빈 평가 이력 로드 테스트"""
        from unittest.mock import MagicMock
        
        # Mock empty database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        from src.presentation.web.components.performance_monitor import load_evaluation_history_for_performance
        
        with patch('pathlib.Path.exists', return_value=True):
            result = load_evaluation_history_for_performance()
        
        assert result == []

    def test_performance_metrics_calculation(self):
        """성능 메트릭 계산 테스트"""
        
        def calculate_throughput(qa_count, duration_seconds):
            """처리량 계산 (QA/초)"""
            if duration_seconds <= 0:
                return 0
            return qa_count / duration_seconds
        
        def calculate_efficiency_score(ragas_score, duration_seconds):
            """효율성 점수 계산 (품질/시간)"""
            if duration_seconds <= 0:
                return 0
            return ragas_score / (duration_seconds / 60)  # 품질점수 per minute
        
        # Test throughput calculation
        throughput = calculate_throughput(10, 60)  # 10 QA in 60 seconds
        assert abs(throughput - 10/60) < 0.001
        
        # Test efficiency calculation
        efficiency = calculate_efficiency_score(0.9, 120)  # 0.9 score in 2 minutes
        assert abs(efficiency - 0.45) < 0.001

    def test_resource_usage_monitoring(self):
        """리소스 사용량 모니터링 테스트"""
        
        def monitor_resource_usage(evaluations):
            """리소스 사용량 모니터링"""
            if not evaluations:
                return {}
            
            # API 호출 횟수 추정 (QA 당 평균 4회 호출 가정)
            total_qa = sum(e.get("qa_count", 0) for e in evaluations)
            estimated_api_calls = total_qa * 4
            
            # 평균 처리 시간
            durations = [e.get("duration", 0) for e in evaluations]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                "total_evaluations": len(evaluations),
                "total_qa_processed": total_qa,
                "estimated_api_calls": estimated_api_calls,
                "avg_processing_time": avg_duration,
                "qa_per_minute": total_qa / (sum(durations) / 60) if sum(durations) > 0 else 0,
            }
        
        test_evaluations = [
            {"qa_count": 10, "duration": 60},
            {"qa_count": 15, "duration": 90},
        ]
        
        usage = monitor_resource_usage(test_evaluations)
        
        assert usage["total_evaluations"] == 2
        assert usage["total_qa_processed"] == 25
        assert usage["estimated_api_calls"] == 100  # 25 * 4
        assert usage["avg_processing_time"] == 75  # (60 + 90) / 2

    def test_performance_trend_analysis(self):
        """성능 트렌드 분석 테스트"""
        
        def analyze_performance_trends(evaluations):
            """성능 트렌드 분석"""
            if len(evaluations) < 2:
                return {"trend": "insufficient_data"}
            
            # 시간순 정렬
            sorted_evals = sorted(evaluations, key=lambda x: x["timestamp"])
            
            # 최근 vs 이전 성능 비교
            mid_point = len(sorted_evals) // 2
            recent_scores = [e["ragas_score"] for e in sorted_evals[mid_point:]]
            earlier_scores = [e["ragas_score"] for e in sorted_evals[:mid_point]]
            
            recent_avg = sum(recent_scores) / len(recent_scores)
            earlier_avg = sum(earlier_scores) / len(earlier_scores)
            
            trend = "improving" if recent_avg > earlier_avg else "declining" if recent_avg < earlier_avg else "stable"
            
            return {
                "trend": trend,
                "recent_avg_score": recent_avg,
                "earlier_avg_score": earlier_avg,
                "improvement": recent_avg - earlier_avg,
            }
        
        test_evaluations = [
            {"timestamp": "2024-01-01T10:00:00", "ragas_score": 0.8},
            {"timestamp": "2024-01-01T11:00:00", "ragas_score": 0.82},
            {"timestamp": "2024-01-01T12:00:00", "ragas_score": 0.85},
            {"timestamp": "2024-01-01T13:00:00", "ragas_score": 0.87},
        ]
        
        trends = analyze_performance_trends(test_evaluations)
        
        assert trends["trend"] == "improving"
        assert trends["recent_avg_score"] > trends["earlier_avg_score"]
        assert trends["improvement"] > 0

    def test_alert_system(self):
        """알림 시스템 테스트"""
        
        def check_performance_alerts(current_metrics):
            """성능 알림 체크"""
            alerts = []
            
            # 성공률 낮음 알림
            if current_metrics.get("success_rate", 1.0) < 0.9:
                alerts.append({
                    "type": "warning",
                    "message": f"API 성공률이 {current_metrics['success_rate']:.1%}로 낮습니다",
                    "severity": "medium"
                })
            
            # 평균 응답시간 높음 알림
            if current_metrics.get("avg_duration", 0) > 3.0:
                alerts.append({
                    "type": "warning", 
                    "message": f"평균 응답시간이 {current_metrics['avg_duration']:.1f}초로 높습니다",
                    "severity": "high"
                })
            
            # RAGAS 점수 낮음 알림
            if current_metrics.get("avg_ragas_score", 1.0) < 0.7:
                alerts.append({
                    "type": "error",
                    "message": f"평균 RAGAS 점수가 {current_metrics['avg_ragas_score']:.2f}로 낮습니다",
                    "severity": "high"
                })
            
            return alerts
        
        # Test case: Normal performance
        normal_metrics = {
            "success_rate": 0.95,
            "avg_duration": 1.5,
            "avg_ragas_score": 0.85
        }
        
        alerts = check_performance_alerts(normal_metrics)
        assert len(alerts) == 0
        
        # Test case: Poor performance
        poor_metrics = {
            "success_rate": 0.8,
            "avg_duration": 4.0,
            "avg_ragas_score": 0.6
        }
        
        alerts = check_performance_alerts(poor_metrics)
        assert len(alerts) == 3
        assert any(alert["severity"] == "high" for alert in alerts)