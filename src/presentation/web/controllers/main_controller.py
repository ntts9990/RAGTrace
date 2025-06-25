"""
Main Controller

메인 애플리케이션 컨트롤러입니다.
"""

import streamlit as st

from ..models.session_model import SessionManager
from ..models.navigation_model import NavigationModel
from .page_controller import PageController


@st.cache_resource
def get_session_manager():
    """SessionManager 싱글톤 인스턴스"""
    print("🔧 SessionManager 생성")
    return SessionManager()


@st.cache_resource
def get_navigation_model():
    """NavigationModel 싱글톤 인스턴스"""
    print("🔧 NavigationModel 생성")
    return NavigationModel()


@st.cache_resource
def get_page_controller():
    """PageController 싱글톤 인스턴스"""
    print("🔧 PageController 생성")
    session_manager = get_session_manager()
    return PageController(session_manager)


class MainController:
    """메인 애플리케이션 컨트롤러"""
    
    def __init__(self):
        self.session_manager = get_session_manager()
        self.navigation = get_navigation_model()
        self.page_controller = get_page_controller()
        print("🔧 MainController 생성")
    
    def initialize_app(self) -> None:
        """애플리케이션 초기화"""
        # 페이지 설정은 main.py에서 이미 완료됨
        
        # 세션 상태 초기화 (SessionManager가 자동으로 처리)
        
        # 네비게이션 처리
        self.session_manager.handle_navigation()
    
    def render_sidebar(self) -> None:
        """사이드바 렌더링"""
        st.sidebar.title("🔍 RAGTrace 대시보드")
        
        # 페이지 선택
        pages = self.navigation.get_pages()
        page_keys = list(pages.keys())
        
        # 상태 객체에서 직접 현재 페이지 가져오기
        current_page = self.session_manager.state.selected_page
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
        # 상태 객체의 값을 직접 변경
        self.session_manager.state.selected_page = st.session_state.page_selector
    
    def render_main_content(self) -> None:
        """메인 콘텐츠 렌더링"""
        self.page_controller.render_current_page()
    
    def run(self) -> None:
        """애플리케이션 실행"""
        self.initialize_app()
        self.render_sidebar()
        self.render_main_content()