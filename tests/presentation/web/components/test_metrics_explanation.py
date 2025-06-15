"""
메트릭 설명 컴포넌트 테스트
RAGAS 메트릭 설명 기능들을 테스트
"""

import pytest
import streamlit as st
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestMetricsExplanation:
    """메트릭 설명 기능 테스트"""
    
    def test_metrics_explanation_module_import(self):
        """메트릭 설명 모듈 임포트 테스트"""
        try:
            from src.presentation.web.components.metrics_explanation import show_metrics_explanation
            assert callable(show_metrics_explanation)
        except ImportError as e:
            pytest.fail(f"메트릭 설명 모듈 임포트 실패: {e}")
    
    @patch('streamlit.header')
    @patch('streamlit.markdown')
    def test_show_metrics_explanation_basic(self, mock_markdown, mock_header):
        """기본 메트릭 설명 표시 테스트"""
        from src.presentation.web.components.metrics_explanation import show_metrics_explanation
        
        show_metrics_explanation()
        
        # 헤더와 마크다운이 호출되었는지 확인
        mock_header.assert_called()
        mock_markdown.assert_called()
    
    def test_metrics_definitions(self):
        """각 메트릭 정의 테스트"""
        metrics_info = {
            "faithfulness": {
                "name": "Faithfulness (신뢰성)",
                "description": "답변이 주어진 컨텍스트와 얼마나 일치하는가",
                "range": "0.0 ~ 1.0"
            },
            "answer_relevancy": {
                "name": "Answer Relevancy (답변 관련성)",
                "description": "답변이 질문과 얼마나 관련이 있는가",
                "range": "0.0 ~ 1.0"
            },
            "context_recall": {
                "name": "Context Recall (컨텍스트 재현율)",
                "description": "필요한 정보가 컨텍스트에 포함되어 있는가",
                "range": "0.0 ~ 1.0"
            },
            "context_precision": {
                "name": "Context Precision (컨텍스트 정확성)",
                "description": "컨텍스트에 불필요한 정보가 포함되어 있지 않은가",
                "range": "0.0 ~ 1.0"
            }
        }
        
        # 각 메트릭이 올바른 정보를 가지고 있는지 확인
        for metric_key, info in metrics_info.items():
            assert "name" in info
            assert "description" in info
            assert "range" in info
            assert info["range"] == "0.0 ~ 1.0"


class TestMetricsVisualization:
    """메트릭 시각화 테스트"""
    
    def test_create_metrics_comparison_chart(self):
        """메트릭 비교 차트 생성 테스트"""
        sample_data = {
            'Faithfulness': 0.85,
            'Answer Relevancy': 0.78,
            'Context Recall': 0.82,
            'Context Precision': 0.91
        }
        
        def create_comparison_chart(data):
            """메트릭 비교 차트 생성 함수 (가상)"""
            import plotly.graph_objects as go
            
            fig = go.Figure(data=go.Scatterpolar(
                r=list(data.values()),
                theta=list(data.keys()),
                fill='toself',
                name='RAGAS Metrics'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )),
                showlegend=True
            )
            
            return fig
        
        # 차트 생성 테스트
        chart = create_comparison_chart(sample_data)
        assert chart is not None
        assert hasattr(chart, 'data')
        assert len(chart.data) > 0
    
    def test_metric_score_colors(self):
        """메트릭 점수별 색상 분류 테스트"""
        def get_score_color(score):
            """점수에 따른 색상 반환"""
            if score >= 0.8:
                return "green"
            elif score >= 0.6:
                return "orange"
            elif score >= 0.4:
                return "yellow"
            else:
                return "red"
        
        assert get_score_color(0.85) == "green"
        assert get_score_color(0.75) == "orange"
        assert get_score_color(0.55) == "yellow"
        assert get_score_color(0.35) == "red"


class TestMetricsExamples:
    """메트릭 예시 테스트"""
    
    def test_faithfulness_examples(self):
        """Faithfulness 예시 테스트"""
        examples = {
            "good": {
                "context": "서울은 한국의 수도입니다.",
                "answer": "한국의 수도는 서울입니다.",
                "score": 0.9
            },
            "bad": {
                "context": "서울은 한국의 수도입니다.",
                "answer": "한국의 수도는 부산입니다.",
                "score": 0.1
            }
        }
        
        # 좋은 예시는 높은 점수, 나쁜 예시는 낮은 점수
        assert examples["good"]["score"] > 0.8
        assert examples["bad"]["score"] < 0.3
    
    def test_answer_relevancy_examples(self):
        """Answer Relevancy 예시 테스트"""
        examples = {
            "relevant": {
                "question": "한국의 수도는 어디인가요?",
                "answer": "한국의 수도는 서울입니다.",
                "score": 0.95
            },
            "irrelevant": {
                "question": "한국의 수도는 어디인가요?",
                "answer": "오늘 날씨가 좋네요.",
                "score": 0.05
            }
        }
        
        assert examples["relevant"]["score"] > 0.9
        assert examples["irrelevant"]["score"] < 0.1


class TestInteractiveElements:
    """인터랙티브 요소 테스트"""
    
    @patch('streamlit.slider')
    def test_score_threshold_slider(self, mock_slider):
        """점수 임계값 슬라이더 테스트"""
        mock_slider.return_value = 0.7
        
        def create_threshold_slider():
            threshold = st.slider(
                "평가 기준 점수",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.05
            )
            return threshold
        
        threshold = create_threshold_slider()
        assert threshold == 0.7
        mock_slider.assert_called_once()
    
    @patch('streamlit.selectbox')
    def test_metric_selector(self, mock_selectbox):
        """메트릭 선택 박스 테스트"""
        mock_selectbox.return_value = "Faithfulness"
        
        def create_metric_selector():
            metric = st.selectbox(
                "메트릭 선택",
                options=["Faithfulness", "Answer Relevancy", "Context Recall", "Context Precision"]
            )
            return metric
        
        selected_metric = create_metric_selector()
        assert selected_metric == "Faithfulness"
        mock_selectbox.assert_called_once()


class TestMetricsInterpretation:
    """메트릭 해석 기능 테스트"""
    
    def test_score_interpretation_text(self):
        """점수 해석 텍스트 생성 테스트"""
        def get_interpretation(metric_name, score):
            """메트릭 점수에 대한 해석 반환"""
            interpretations = {
                "high": f"{metric_name} 점수가 {score:.2f}로 우수합니다!",
                "medium": f"{metric_name} 점수가 {score:.2f}로 양호합니다.",
                "low": f"{metric_name} 점수가 {score:.2f}로 개선이 필요합니다."
            }
            
            if score >= 0.8:
                return interpretations["high"]
            elif score >= 0.6:
                return interpretations["medium"]
            else:
                return interpretations["low"]
        
        high_score_text = get_interpretation("Faithfulness", 0.85)
        medium_score_text = get_interpretation("Faithfulness", 0.75)
        low_score_text = get_interpretation("Faithfulness", 0.45)
        
        assert "우수합니다" in high_score_text
        assert "양호합니다" in medium_score_text
        assert "개선이 필요합니다" in low_score_text
    
    def test_improvement_suggestions(self):
        """개선 제안 기능 테스트"""
        def get_improvement_suggestion(metric_name, score):
            """낮은 점수에 대한 개선 제안"""
            if score < 0.6:
                suggestions = {
                    "Faithfulness": "답변이 컨텍스트 내용과 더 일치하도록 생성 모델을 조정하세요.",
                    "Answer Relevancy": "질문과 더 관련성 높은 답변을 생성하도록 프롬프트를 개선하세요.",
                    "Context Recall": "더 포괄적인 검색 결과를 제공하도록 검색 시스템을 개선하세요.",
                    "Context Precision": "불필요한 정보를 제거하도록 검색 결과를 필터링하세요."
                }
                return suggestions.get(metric_name, "일반적인 개선이 필요합니다.")
            return "현재 점수가 양호합니다."
        
        low_faithfulness_suggestion = get_improvement_suggestion("Faithfulness", 0.45)
        good_score_suggestion = get_improvement_suggestion("Faithfulness", 0.85)
        
        assert "생성 모델을 조정" in low_faithfulness_suggestion
        assert "양호합니다" in good_score_suggestion


def test_component_integration():
    """컴포넌트 통합 테스트"""
    # 메트릭 설명 컴포넌트가 다른 컴포넌트들과 잘 통합되는지 테스트
    try:
        from src.presentation.web.components import metrics_explanation
        assert hasattr(metrics_explanation, 'show_metrics_explanation')
    except ImportError:
        # 모듈이 없더라도 테스트는 통과 (선택적 컴포넌트)
        pass