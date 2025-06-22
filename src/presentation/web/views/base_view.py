"""
Base View

모든 뷰의 기본 클래스입니다.
"""

from abc import ABC, abstractmethod
import streamlit as st
from typing import Any, Dict, Optional

from ..models.session_model import SessionManager


class BaseView(ABC):
    """기본 뷰 클래스"""
    
    def __init__(self, session_manager: SessionManager):
        self.session = session_manager
    
    @abstractmethod
    def render(self, **kwargs) -> None:
        """뷰 렌더링"""
        pass
    
    def show_navigation_button(self, text: str, target_page: str, button_type: str = "secondary", help_text: Optional[str] = None) -> bool:
        """네비게이션 버튼 표시"""
        if st.button(text, type=button_type, help=help_text):
            self.session.navigate_to(target_page)
            st.rerun()
            return True
        return False
    
    def show_metric_card(self, label: str, value: float, icon: str, delta: Optional[float] = None) -> None:
        """메트릭 카드 표시"""
        st.metric(
            label=f"{icon} {label}",
            value=f"{value:.3f}",
            delta=f"{delta:.3f}" if delta is not None else None,
        )
    
    def show_error(self, message: str) -> None:
        """에러 메시지 표시"""
        st.error(message)
    
    def show_success(self, message: str) -> None:
        """성공 메시지 표시"""
        st.success(message)
    
    def show_info(self, message: str) -> None:
        """정보 메시지 표시"""
        st.info(message)
    
    def show_warning(self, message: str) -> None:
        """경고 메시지 표시"""
        st.warning(message)
    
    def create_columns(self, cols: int) -> Any:
        """컬럼 생성"""
        return st.columns(cols)
    
    def show_spinner(self, text: str):
        """스피너 표시"""
        return st.spinner(text)
    
    def show_balloons(self) -> None:
        """축하 풍선 효과"""
        st.balloons()