"""
Page Controller

페이지 라우팅과 렌더링을 담당하는 컨트롤러입니다.
"""

import streamlit as st

from ..views import OverviewView, EvaluationView, HistoricalView
from ..models.navigation_model import NavigationModel
from ..models.session_model import SessionManager


class PageController:
    """페이지 렌더링 컨트롤러"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.navigation = NavigationModel()
        self.views = {
            "🔍 Overview": OverviewView(session_manager),
            "🚀 Run Evaluation": EvaluationView(session_manager),
            "📈 Historical Analysis": HistoricalView(session_manager),
        }

    def render_current_page(self):
        """현재 선택된 페이지를 렌더링"""
        current_page_name = self.session_manager.state.selected_page
        view = self.views.get(current_page_name)
        
        if view:
            view.render()
        else:
            st.error(f"페이지를 찾을 수 없습니다: {current_page_name}")
            # 기본 페이지로 이동
            self.session_manager.state.selected_page = self.navigation.get_default_page()
            st.rerun()