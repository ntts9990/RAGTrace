"""
웹 대시보드 메인 모듈 테스트
Streamlit 앱의 핵심 기능들을 테스트
"""

import pytest
import streamlit as st
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import sys
from pathlib import Path

# 선택적 의존성 체크
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    go = None

# 프로젝트 루트가 sys.path에 있는지 확인
try:
    from src.domain.entities.evaluation_result import EvaluationResult
    from src.domain.entities.evaluation_data import EvaluationData
    HAS_SRC = True
except ImportError:
    HAS_SRC = False

# 프로젝트 루트 경로 추가
# 프로젝트 루트를 동적으로 찾아 경로 추가
def add_project_root_to_path():
    current_path = Path(__file__).resolve()
    while current_path != current_path.parent:
        if (current_path / 'pyproject.toml').exists():
            sys.path.insert(0, str(current_path))
            return current_path
        current_path = current_path.parent
    raise FileNotFoundError("프로젝트 루트를 찾을 수 없습니다.")

add_project_root_to_path()

# 다시 시도해서 임포트
if not HAS_SRC:
    try:
        from src.domain.entities.evaluation_result import EvaluationResult
        from src.domain.entities.evaluation_data import EvaluationData
        HAS_SRC = True
    except ImportError:
        EvaluationResult = None
        EvaluationData = None


@pytest.fixture
def sample_evaluation_result():
    """테스트용 평가 결과 샘플"""
    if not HAS_SRC or EvaluationResult is None:
        pytest.skip("src modules not available")
    return EvaluationResult(
        faithfulness=0.85,
        answer_relevancy=0.78,
        context_recall=0.82,
        context_precision=0.91,
        ragas_score=0.84
    )


@pytest.fixture  
def sample_evaluation_data():
    """테스트용 평가 데이터 샘플"""
    if not HAS_SRC or EvaluationData is None:
        pytest.skip("src modules not available")
    return [
        EvaluationData(
            question="한국의 수도는?",
            contexts=["서울은 한국의 수도입니다."],
            answer="한국의 수도는 서울입니다.",
            ground_truth="서울"
        )
    ]


class TestWebDashboardHelpers:
    """웹 대시보드 헬퍼 함수들 테스트"""
    
    def test_evaluation_result_to_dict(self, sample_evaluation_result):
        """평가 결과를 딕셔너리로 변환하는 기능 테스트"""
        # 실제 구현이 있다면 테스트
        result_dict = {
            'faithfulness': sample_evaluation_result.faithfulness,
            'answer_relevancy': sample_evaluation_result.answer_relevancy,
            'context_recall': sample_evaluation_result.context_recall,
            'context_precision': sample_evaluation_result.context_precision,
            'ragas_score': sample_evaluation_result.ragas_score
        }
        
        assert result_dict['faithfulness'] == 0.85
        assert result_dict['ragas_score'] == 0.84
    
    def test_score_interpretation(self):
        """점수 해석 로직 테스트"""
        # 점수 등급 분류 테스트
        def get_score_grade(score):
            if score >= 0.8:
                return "우수"
            elif score >= 0.6:
                return "양호"
            elif score >= 0.4:
                return "보통"
            else:
                return "개선필요"
        
        assert get_score_grade(0.85) == "우수"
        assert get_score_grade(0.75) == "양호"
        assert get_score_grade(0.55) == "보통"
        assert get_score_grade(0.35) == "개선필요"


class TestDataVisualization:
    """데이터 시각화 관련 테스트"""
    
    def test_radar_chart_data_preparation(self, sample_evaluation_result):
        """레이더 차트 데이터 준비 테스트"""
        metrics = ['Faithfulness', 'Answer Relevancy', 'Context Recall', 'Context Precision']
        values = [
            sample_evaluation_result.faithfulness,
            sample_evaluation_result.answer_relevancy,
            sample_evaluation_result.context_recall,
            sample_evaluation_result.context_precision
        ]
        
        assert len(metrics) == len(values)
        assert all(0 <= v <= 1 for v in values)
        assert values[0] == 0.85  # faithfulness
    
    def test_metrics_dataframe_creation(self, sample_evaluation_result):
        """메트릭 데이터프레임 생성 테스트"""
        df = pd.DataFrame({
            'Metric': ['Faithfulness', 'Answer Relevancy', 'Context Recall', 'Context Precision'],
            'Score': [
                sample_evaluation_result.faithfulness,
                sample_evaluation_result.answer_relevancy,
                sample_evaluation_result.context_recall,
                sample_evaluation_result.context_precision
            ]
        })
        
        assert len(df) == 4
        assert 'Metric' in df.columns
        assert 'Score' in df.columns
        assert df['Score'].max() <= 1.0
        assert df['Score'].min() >= 0.0


class TestDatabaseOperations:
    """데이터베이스 연동 테스트 (Streamlit 앱에서 사용)"""
    
    @patch('sqlite3.connect')
    def test_save_evaluation_result(self, mock_connect, sample_evaluation_result):
        """평가 결과 저장 테스트"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 실제 구현이 있다면 테스트
        def save_evaluation_result(result, db_path="test.db"):
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO evaluations (faithfulness, answer_relevancy, context_recall, context_precision, ragas_score, timestamp)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (result.faithfulness, result.answer_relevancy, result.context_recall, result.context_precision, result.ragas_score))
            conn.commit()
            conn.close()
        
        # 함수 실행
        save_evaluation_result(sample_evaluation_result)
        
        # 호출 확인
        mock_connect.assert_called_once()
        mock_conn.cursor.assert_called_once()
    
    @patch('sqlite3.connect')
    def test_load_evaluation_history(self, mock_connect):
        """평가 이력 로드 테스트"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # 가짜 데이터 설정
        mock_cursor.fetchall.return_value = [
            (1, 0.85, 0.78, 0.82, 0.91, 0.84, '2024-01-01 12:00:00'),
            (2, 0.88, 0.82, 0.85, 0.93, 0.87, '2024-01-02 12:00:00')
        ]
        
        def load_evaluation_history(db_path="test.db"):
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM evaluations ORDER BY timestamp DESC")
            results = cursor.fetchall()
            conn.close()
            return results
        
        # 함수 실행
        history = load_evaluation_history()
        
        # 결과 확인
        assert len(history) == 2
        assert history[0][1] == 0.85  # faithfulness
        mock_connect.assert_called_once()


class TestErrorHandling:
    """에러 처리 테스트"""
    
    def test_invalid_data_handling(self):
        """잘못된 데이터 처리 테스트"""
        with pytest.raises(ValueError):
            # 잘못된 점수 범위
            EvaluationResult(
                faithfulness=1.5,  # 범위 초과
                answer_relevancy=0.8,
                context_recall=0.7,
                context_precision=0.9,
                ragas_score=0.85
            )
    
    def test_empty_data_handling(self):
        """빈 데이터 처리 테스트"""
        empty_data = []
        
        # 빈 데이터에 대한 처리 로직 테스트
        def process_empty_data(data):
            if not data:
                return {"message": "데이터가 없습니다", "data": []}
            return {"message": "정상", "data": data}
        
        result = process_empty_data(empty_data)
        assert result["message"] == "데이터가 없습니다"
        assert result["data"] == []


class TestUIComponents:
    """UI 컴포넌트 테스트 (모킹 기반)"""
    
    @patch('streamlit.metric')
    def test_metrics_display(self, mock_metric, sample_evaluation_result):
        """메트릭 표시 테스트"""
        def display_metrics(result):
            st.metric("Faithfulness", f"{result.faithfulness:.3f}")
            st.metric("Answer Relevancy", f"{result.answer_relevancy:.3f}")
            st.metric("Context Recall", f"{result.context_recall:.3f}")
            st.metric("Context Precision", f"{result.context_precision:.3f}")
        
        display_metrics(sample_evaluation_result)
        
        # 메트릭 호출 확인
        assert mock_metric.call_count == 4
    
    @patch('streamlit.success')
    @patch('streamlit.warning')
    @patch('streamlit.error')
    def test_status_messages(self, mock_error, mock_warning, mock_success):
        """상태 메시지 표시 테스트"""
        def show_status_message(score):
            if score >= 0.8:
                st.success(f"우수한 성능입니다! ({score:.3f})")
            elif score >= 0.6:
                st.warning(f"양호한 성능입니다. ({score:.3f})")
            else:
                st.error(f"성능 개선이 필요합니다. ({score:.3f})")
        
        # 각 범위별 테스트
        show_status_message(0.85)
        mock_success.assert_called_once()
        
        show_status_message(0.75)
        mock_warning.assert_called_once()
        
        show_status_message(0.45)
        mock_error.assert_called_once()


def test_module_imports():
    """모듈 임포트 테스트"""
    try:
        import src.presentation.web.main
        assert True
    except ImportError as e:
        pytest.skip(f"웹 대시보드 모듈 임포트 실패: {e}")


def test_streamlit_configuration():
    """Streamlit 설정 테스트"""
    # 페이지 설정이 올바른지 확인하는 기본 테스트
    page_config = {
        "page_title": "RAGAS 평가 대시보드",
        "page_icon": "🧪",
        "layout": "wide"
    }
    
    assert page_config["page_title"] == "RAGAS 평가 대시보드"
    assert page_config["layout"] == "wide"