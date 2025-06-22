"""
Main Controller

메인 애플리케이션 컨트롤러입니다.
"""

import streamlit as st

from ..models.session_model import SessionModel
from ..models.navigation_model import NavigationModel
from .page_controller import PageController


class MainController:
    """메인 애플리케이션 컨트롤러"""
    
    def __init__(self):
        self.session = SessionModel()
        self.navigation = NavigationModel()
        self.page_controller = PageController()
    
    def initialize_app(self) -> None:
        """애플리케이션 초기화"""
        # 페이지 설정
        st.set_page_config(
            page_title="RAGTrace 대시보드",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        
        # 세션 상태 초기화
        self._initialize_session_state()
        
        # 네비게이션 처리
        self.session.handle_navigation()
    
    def _initialize_session_state(self) -> None:
        """세션 상태 초기화"""
        # 기본 페이지 설정
        if "selected_page" not in st.session_state:
            st.session_state.selected_page = self.navigation.get_default_page()
    
    def render_sidebar(self) -> None:
        """사이드바 렌더링"""
        st.sidebar.title("🔍 RAGTrace 대시보드")
        
        # 페이지 선택
        pages = self.navigation.get_pages()
        page_keys = list(pages.keys())
        
        current_page = self.session.get_selected_page()
        current_index = page_keys.index(current_page) if current_page in page_keys else 0
        
        selected_page = st.sidebar.selectbox(
            "페이지 선택",
            page_keys,
            index=current_index,
            key="page_selector",
            on_change=self._on_page_change,
        )
    
    def _on_page_change(self) -> None:
        """페이지 변경 콜백"""
        self.session.set_selected_page(st.session_state.page_selector)
    
    def render_main_content(self) -> None:
        """메인 콘텐츠 렌더링"""
        self.page_controller.render_current_page()
    
    def run(self) -> None:
        """애플리케이션 실행"""
        self.initialize_app()
        self.render_sidebar()
        self.render_main_content()