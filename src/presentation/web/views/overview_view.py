"""
Overview View

메인 대시보드 뷰입니다.
"""

import streamlit as st
from typing import Optional, Dict, Any, List

from .base_view import BaseView
from ..models.evaluation_model import EvaluationResult, EvaluationModel
from ..services.chart_service import ChartService


class OverviewView(BaseView):
    """메인 대시보드 뷰"""
    
    def render(self, latest_result: Optional[Dict[str, Any]] = None, history: Optional[List[Dict[str, Any]]] = None) -> None:
        """메인 오버뷰 렌더링"""
        st.title("🔍 RAGTrace - RAG 성능 추적 대시보드")
        st.markdown("---")
        
        # 평가 완료 축하 메시지
        if self.session.get_evaluation_completed():
            self.show_success("🎉 새로운 평가가 방금 완료되었습니다!")
            self.session.set_evaluation_completed(False)
        
        self._render_header()
        
        if latest_result:
            result = EvaluationModel.parse_result_dict(latest_result)
            self._render_metric_cards(result)
            self._render_metric_charts(result)
            if history and len(history) > 1:
                self._render_recent_trends(history)
        else:
            self._render_empty_state()
    
    def _render_header(self) -> None:
        """헤더 영역 렌더링"""
        st.header("📊 평가 결과 개요")
        
        # 액션 버튼들
        col1, col2, col3, col4 = self.create_columns([2, 1, 1, 2])

        with col1:
            self.show_navigation_button(
                "🚀 새 평가 실행", 
                "🚀 New Evaluation", 
                "primary", 
                "새로운 RAG 평가를 시작합니다"
            )

        with col2:
            if st.button("🔄 새로고침", help="최신 결과를 다시 로드합니다"):
                st.rerun()

        with col3:
            self.show_navigation_button(
                "📈 이력보기", 
                "📈 Historical", 
                "secondary", 
                "과거 평가 결과를 확인합니다"
            )

        with col4:
            self.show_navigation_button(
                "📚 메트릭 가이드", 
                "📖 Metrics Explanation", 
                "secondary", 
                "RAGAS 점수의 의미를 알아보세요"
            )
    
    def _render_metric_cards(self, result: EvaluationResult) -> None:
        """메트릭 카드 표시"""
        st.subheader("🎯 핵심 지표")

        col1, col2, col3, col4, col5 = self.create_columns(5)

        metrics_data = [
            ("종합 점수", result.ragas_score, "🏆"),
            ("Faithfulness", result.faithfulness, "✅"),
            ("Answer Relevancy", result.answer_relevancy, "🎯"),
            ("Context Recall", result.context_recall, "🔄"),
            ("Context Precision", result.context_precision, "📍"),
        ]

        for i, (name, value, icon) in enumerate(metrics_data):
            with [col1, col2, col3, col4, col5][i]:
                # 델타 계산 (이전 결과와 비교)
                delta_value = self._calculate_delta(name, value)
                self.show_metric_card(name, value, icon, delta_value)
    
    def _calculate_delta(self, metric_name: str, current_value: float) -> Optional[float]:
        """이전 결과와의 델타 계산"""
        # 여기서는 실제 이전 결과를 가져와서 계산해야 함
        # 현재는 None 반환
        return None
    
    def _render_metric_charts(self, result: EvaluationResult) -> None:
        """메트릭 시각화 차트"""
        st.subheader("📈 시각화")

        col1, col2 = self.create_columns(2)

        with col1:
            # 레이더 차트
            radar_fig = ChartService.create_radar_chart(result)
            st.plotly_chart(radar_fig, use_container_width=True)

        with col2:
            # 바 차트
            bar_fig = ChartService.create_bar_chart(result)
            st.plotly_chart(bar_fig, use_container_width=True)
    
    def _render_recent_trends(self, history: List[Dict[str, Any]]) -> None:
        """최근 트렌드 표시"""
        st.subheader("📈 최근 트렌드")

        trend_fig = ChartService.create_trend_chart(history)
        if trend_fig:
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            self.show_info("📊 트렌드 표시를 위해 더 많은 평가 데이터가 필요합니다.")
    
    def _render_empty_state(self) -> None:
        """빈 상태 렌더링"""
        self.show_info(
            "📝 아직 평가 결과가 없습니다. '새 평가 실행' 버튼을 클릭하여 첫 평가를 시작하세요!"
        )
        st.markdown("---")
        st.markdown("### 🤔 RAGAS 메트릭이 궁금하신가요?")
        st.markdown(
            "📚 사이드바에서 **'Metrics Guide'**를 선택하면 각 점수가 무엇을 의미하는지 쉽게 알아볼 수 있습니다!"
        )