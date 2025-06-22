"""
Page Controller

페이지 라우팅과 렌더링을 담당하는 컨트롤러입니다.
"""

import streamlit as st

from ..models.session_model import SessionModel
from ..models.navigation_model import NavigationModel
from ..services.database_service import DatabaseService
from ..views.overview_view import OverviewView
from ..views.evaluation_view import EvaluationView
from ..views.historical_view import HistoricalView


class PageController:
    """페이지 컨트롤러"""
    
    def __init__(self):
        self.session = SessionModel()
        self.navigation = NavigationModel()
        self.database = DatabaseService()
        
        # 뷰 인스턴스들
        self.overview_view = OverviewView()
        self.evaluation_view = EvaluationView()
        self.historical_view = HistoricalView()
    
    def render_current_page(self) -> None:
        """현재 페이지 렌더링"""
        current_page = self.session.get_selected_page()
        
        if current_page == "🎯 Overview":
            self._render_overview_page()
        elif current_page == "🚀 New Evaluation":
            self._render_evaluation_page()
        elif current_page == "📈 Historical":
            self._render_historical_page()
        elif current_page == "📚 Detailed Analysis":
            self._render_detailed_analysis_page()
        elif current_page == "📖 Metrics Explanation":
            self._render_metrics_page()
        elif current_page == "⚡ Performance":
            self._render_performance_page()
        else:
            self._render_overview_page()
    
    def _render_overview_page(self) -> None:
        """Overview 페이지 렌더링"""
        latest_result = self.database.load_latest_result()
        history = self.database.load_evaluation_history(limit=10)
        
        self.overview_view.render(
            latest_result=latest_result,
            history=history
        )
    
    def _render_evaluation_page(self) -> None:
        """새 평가 실행 페이지 렌더링"""
        self.evaluation_view.render()
    
    def _render_historical_page(self) -> None:
        """Historical 페이지 렌더링"""
        self.historical_view.render()
    
    def _render_detailed_analysis_page(self) -> None:
        """상세 분석 페이지 렌더링 (기존 컴포넌트 사용)"""
        from src.presentation.web.components.detailed_analysis import (
            show_detailed_analysis as show_detailed_component,
        )
        show_detailed_component()
    
    def _render_metrics_page(self) -> None:
        """메트릭 가이드 페이지 렌더링 (기존 컴포넌트 사용)"""
        from src.presentation.web.components.metrics_explanation import (
            show_metrics_explanation as show_metrics_component,
        )
        show_metrics_component()
    
    def _render_performance_page(self) -> None:
        """성능 모니터링 페이지 렌더링 (기존 컴포넌트 사용)"""
        from src.presentation.web.components.performance_monitor import (
            show_performance_monitor as show_performance_component,
        )
        show_performance_component()