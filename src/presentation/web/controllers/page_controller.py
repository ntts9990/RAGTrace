"""
Page Controller

페이지 라우팅과 렌더링을 담당하는 컨트롤러입니다.
"""

import streamlit as st

from ..views import OverviewView, EvaluationView, HistoricalView
from ..models.navigation_model import NavigationModel
from ..models.session_model import SessionManager


# 전역 뷰 캐시 (Streamlit 세션 전체에서 공유)
if 'view_cache' not in st.session_state:
    st.session_state.view_cache = {}


class PageController:
    """페이지 렌더링 컨트롤러"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.navigation = NavigationModel()
        print("🔧 PageController 생성됨 (뷰들은 지연 로딩)")

    def _get_view(self, page_name: str):
        """뷰를 지연 로딩으로 가져옵니다."""
        if page_name not in st.session_state.view_cache:
            print(f"🔄 {page_name} 뷰 생성 중...")
            if page_name == "🔍 Overview":
                view = OverviewView(self.session_manager)
            elif page_name == "🚀 Run Evaluation":
                view = EvaluationView(self.session_manager)
            elif page_name == "📈 Historical Analysis":
                view = HistoricalView(self.session_manager)
            else:
                return None
            st.session_state.view_cache[page_name] = view
            print(f"✅ {page_name} 뷰 생성 완료")
        
        return st.session_state.view_cache[page_name]

    def render_current_page(self):
        """현재 선택된 페이지를 렌더링"""
        current_page_name = self.session_manager.state.selected_page
        view = self._get_view(current_page_name)
        
        if view:
            view.render()
        else:
            st.error(f"페이지를 찾을 수 없습니다: {current_page_name}")
            # 기본 페이지로 이동
            self.session_manager.state.selected_page = self.navigation.get_default_page()
            st.rerun()