"""
Session Model

세션 상태 관리 모델입니다.
"""

import streamlit as st
from typing import Optional, Any, Dict

from src.domain.prompts import PromptType
from .navigation_model import NavigationModel


class SessionModel:
    """세션 상태 관리"""
    
    @staticmethod
    def get_selected_page() -> str:
        """현재 선택된 페이지 반환"""
        if "selected_page" not in st.session_state:
            st.session_state.selected_page = NavigationModel.get_default_page()
        return st.session_state.selected_page
    
    @staticmethod
    def set_selected_page(page: str) -> None:
        """선택된 페이지 설정"""
        st.session_state.selected_page = page
    
    @staticmethod
    def navigate_to(page: str) -> None:
        """페이지 네비게이션"""
        st.session_state.navigate_to = page
    
    @staticmethod
    def handle_navigation() -> None:
        """네비게이션 처리"""
        if "navigate_to" in st.session_state:
            st.session_state.selected_page = st.session_state.navigate_to
            del st.session_state.navigate_to
    
    @staticmethod
    def get_selected_dataset() -> Optional[str]:
        """선택된 데이터셋 반환"""
        return st.session_state.get("selected_dataset")
    
    @staticmethod
    def set_selected_dataset(dataset: str) -> None:
        """선택된 데이터셋 설정"""
        st.session_state.selected_dataset = dataset
    
    @staticmethod
    def get_evaluation_completed() -> bool:
        """평가 완료 상태 반환"""
        return st.session_state.get("evaluation_completed", False)
    
    @staticmethod
    def set_evaluation_completed(completed: bool) -> None:
        """평가 완료 상태 설정"""
        st.session_state.evaluation_completed = completed
    
    @staticmethod
    def get_latest_evaluation_result() -> Optional[Dict[str, Any]]:
        """최신 평가 결과 반환"""
        return st.session_state.get("latest_evaluation_result")
    
    @staticmethod
    def set_latest_evaluation_result(result: Dict[str, Any]) -> None:
        """최신 평가 결과 설정"""
        st.session_state.latest_evaluation_result = result
    
    @staticmethod
    def get_selected_evaluation_index() -> Optional[int]:
        """선택된 평가 인덱스 반환"""
        return st.session_state.get("selected_evaluation_index")
    
    @staticmethod
    def set_selected_evaluation_index(index: int) -> None:
        """선택된 평가 인덱스 설정"""
        st.session_state.selected_evaluation_index = index
    
    @staticmethod
    def clear_evaluation_state() -> None:
        """평가 상태 초기화"""
        keys_to_clear = [
            "evaluation_completed",
            "latest_evaluation_result",
            "selected_evaluation_index"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]