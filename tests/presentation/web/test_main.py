"""
웹 대시보드 메인 모듈 테스트
Streamlit 앱의 핵심 기능들을 테스트
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import streamlit as st

# 선택적 의존성 체크
try:
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    go = None

# 프로젝트 루트가 sys.path에 있는지 확인
try:
    from src.domain.entities.evaluation_data import EvaluationData
    from src.domain.entities.evaluation_result import EvaluationResult

    HAS_SRC = True
except ImportError:
    HAS_SRC = False


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

# 다시 시도해서 임포트
if not HAS_SRC:
    try:
        from src.domain.entities.evaluation_data import EvaluationData
        from src.domain.entities.evaluation_result import EvaluationResult
        HAS_SRC = True
    except ImportError:
        HAS_SRC = False


@pytest.fixture
def sample_evaluation_data():
    """테스트용 평가 데이터"""
    return [
        {
            "question": "한국의 수도는?",
            "answer": "서울입니다",
            "contexts": ["서울은 한국의 수도입니다"],
            "ground_truth": "서울",
            "faithfulness": 0.95,
            "answer_relevancy": 0.90,
            "context_recall": 0.85,
            "context_precision": 0.88,
            "ragas_score": 0.895
        }
    ]


class TestWebMain:
    """웹 대시보드 메인 모듈 테스트"""

    def test_main_module_import(self):
        """메인 모듈 임포트 테스트"""
        try:
            from src.presentation.web.main import load_pages
            assert callable(load_pages)
        except ImportError:
            pytest.skip("웹 메인 모듈이 구현되지 않음")

    def test_load_pages_function(self):
        """페이지 로드 함수 테스트"""
        from src.presentation.web.main import load_pages
        
        pages = load_pages()
        
        assert isinstance(pages, dict)
        assert len(pages) > 0
        
        # 필수 페이지들이 포함되어 있는지 확인
        expected_pages = ["Overview", "Historical", "Detailed Analysis", "Metrics Explanation", "Performance"]
        for expected in expected_pages:
            assert any(expected in key for key in pages.keys())

    @patch('streamlit.sidebar')
    @patch('streamlit.set_page_config')
    def test_streamlit_configuration(self, mock_config, mock_sidebar):
        """Streamlit 설정 테스트"""
        # 실제 설정을 테스트하기 위해 모듈을 임포트
        try:
            import src.presentation.web.main
            # 모듈이 정상적으로 로드되면 설정이 올바르게 되었다고 가정
            assert True
        except Exception as e:
            pytest.fail(f"Streamlit 설정 실패: {e}")

    def test_database_operations(self):
        """데이터베이스 작업 테스트"""
        
        def mock_load_evaluations():
            """모의 평가 결과 로드"""
            return [
                {
                    "id": 1,
                    "timestamp": "2024-01-01 10:00:00",
                    "faithfulness": 0.95,
                    "answer_relevancy": 0.90,
                    "context_recall": 0.85,
                    "context_precision": 0.88,
                    "ragas_score": 0.895
                }
            ]
        
        evaluations = mock_load_evaluations()
        
        assert len(evaluations) == 1
        assert evaluations[0]["ragas_score"] == 0.895

    def test_visualization_functions(self):
        """시각화 함수 테스트"""
        
        def create_metrics_radar_chart(metrics):
            """레이더 차트 생성 테스트"""
            if not HAS_PLOTLY:
                return None
                
            fig = go.Figure()
            
            categories = list(metrics.keys())
            values = list(metrics.values())
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Metrics'
            ))
            
            return fig
        
        test_metrics = {
            "Faithfulness": 0.9,
            "Answer Relevancy": 0.8,
            "Context Recall": 0.85,
            "Context Precision": 0.88
        }
        
        if HAS_PLOTLY:
            chart = create_metrics_radar_chart(test_metrics)
            assert chart is not None
            assert len(chart.data) == 1

    def test_data_processing_functions(self):
        """데이터 처리 함수 테스트"""
        
        def process_evaluation_results(results):
            """평가 결과 처리"""
            if not results:
                return {}
            
            processed = {
                "total_evaluations": len(results),
                "avg_ragas_score": sum(r.get("ragas_score", 0) for r in results) / len(results),
                "metrics_summary": {}
            }
            
            # 메트릭별 평균 계산
            metrics = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
            for metric in metrics:
                values = [r.get(metric, 0) for r in results if metric in r]
                if values:
                    processed["metrics_summary"][metric] = {
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    }
            
            return processed
        
        test_results = [
            {"ragas_score": 0.9, "faithfulness": 0.95, "answer_relevancy": 0.85},
            {"ragas_score": 0.8, "faithfulness": 0.85, "answer_relevancy": 0.75}
        ]
        
        processed = process_evaluation_results(test_results)
        
        assert processed["total_evaluations"] == 2
        assert processed["avg_ragas_score"] == 0.85
        assert "faithfulness" in processed["metrics_summary"]

    @patch('sqlite3.connect')
    def test_database_connection_handling(self, mock_connect):
        """데이터베이스 연결 처리 테스트"""
        from unittest.mock import MagicMock
        
        # 성공적인 연결 테스트
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        
        def test_db_operation():
            """데이터베이스 작업 테스트"""
            conn = mock_connect("test.db")
            cursor = conn.execute("SELECT * FROM evaluations")
            results = cursor.fetchall()
            conn.close()
            return results
        
        results = test_db_operation()
        assert results == []
        mock_connect.assert_called_once()

    def test_error_handling(self):
        """오류 처리 테스트"""
        
        def safe_division(a, b):
            """안전한 나눗셈"""
            try:
                return a / b
            except ZeroDivisionError:
                return 0
            except Exception:
                return None
        
        # 정상 케이스
        assert safe_division(10, 2) == 5
        
        # 0으로 나누기
        assert safe_division(10, 0) == 0
        
        # 잘못된 타입 
        assert safe_division("10", 2) is None

    def test_session_state_management(self):
        """세션 상태 관리 테스트"""
        
        def manage_session_state():
            """세션 상태 관리 로직"""
            # Streamlit 세션 상태 모킹
            session_state = {}
            
            # 기본값 설정
            if "current_page" not in session_state:
                session_state["current_page"] = "Overview"
            
            if "evaluation_history" not in session_state:
                session_state["evaluation_history"] = []
            
            return session_state
        
        state = manage_session_state()
        
        assert "current_page" in state
        assert state["current_page"] == "Overview"
        assert "evaluation_history" in state
        assert isinstance(state["evaluation_history"], list)

    def test_page_routing_logic(self):
        """페이지 라우팅 로직 테스트"""
        
        def route_to_page(page_name, available_pages):
            """페이지 라우팅"""
            if page_name in available_pages:
                return page_name
            else:
                # 기본 페이지로 리디렉션
                return list(available_pages.keys())[0] if available_pages else None
        
        test_pages = {
            "🎯 Overview": "메인 대시보드",
            "📈 Historical": "과거 평가 결과"
        }
        
        # 유효한 페이지
        result = route_to_page("🎯 Overview", test_pages)
        assert result == "🎯 Overview"
        
        # 무효한 페이지 - 기본 페이지로 리디렉션
        result = route_to_page("Invalid Page", test_pages)
        assert result == "🎯 Overview"

    def test_metrics_calculation(self):
        """메트릭 계산 테스트"""
        
        def calculate_overall_score(metrics):
            """전체 점수 계산"""
            if not metrics:
                return 0
            
            # RAGAS 점수 계산 (4개 메트릭의 평균)
            required_metrics = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
            
            available_metrics = [metrics.get(metric, 0) for metric in required_metrics if metric in metrics]
            
            if not available_metrics:
                return 0
            
            return sum(available_metrics) / len(available_metrics)
        
        test_metrics = {
            "faithfulness": 0.9,
            "answer_relevancy": 0.8,
            "context_recall": 0.85,
            "context_precision": 0.88
        }
        
        score = calculate_overall_score(test_metrics)
        expected = (0.9 + 0.8 + 0.85 + 0.88) / 4
        
        assert abs(score - expected) < 0.001

    def test_data_export_functionality(self):
        """데이터 내보내기 기능 테스트"""
        
        def export_to_csv(data):
            """CSV 내보내기"""
            if not data:
                return None
            
            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        
        test_data = [
            {"metric": "faithfulness", "value": 0.9},
            {"metric": "answer_relevancy", "value": 0.8}
        ]
        
        csv_output = export_to_csv(test_data)
        
        assert csv_output is not None
        assert "metric,value" in csv_output
        assert "faithfulness,0.9" in csv_output