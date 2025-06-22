"""
Session Model

세션 상태 관리 모델입니다.
AppState 객체를 통해 상태를 중앙에서 관리합니다.
"""

import streamlit as st
from typing import Optional, Any, Dict
from .app_state import AppState, EvaluationState
from .navigation_model import NavigationModel


class SessionManager:
    """세션 상태 관리자"""
    
    def __init__(self, session_state=st.session_state):
        self._session_state = session_state
        if 'app_state' not in self._session_state:
            self._session_state.app_state = AppState()
            # 초기 페이지 설정
            self._session_state.app_state.selected_page = NavigationModel.get_default_page()
            
    @property
    def state(self) -> AppState:
        """현재 애플리케이션 상태를 나타내는 AppState 객체를 반환합니다."""
        return self._session_state.app_state
        
    def initialize(self):
        """세션 초기화"""
        # AppState의 기본값으로 이미 초기화되므로 추가 로직이 필요 없을 수 있음
        # 필요 시 여기에 초기화 로직 추가
        pass

    def clear_evaluation_state(self):
        """평가 관련 상태 초기화"""
        self.state.clear_evaluation_state()
        
    def handle_navigation(self) -> None:
        """
        네비게이션 요청을 처리합니다.
        'navigate_to' 키는 콜백에서 직접 페이지를 바꾸기 어려울 때 사용될 수 있습니다.
        """
        if "navigate_to" in self._session_state:
            self.state.selected_page = self._session_state.navigate_to
            del self._session_state.navigate_to

    def get_selected_page(self) -> str:
        """현재 선택된 페이지 반환"""
        if "selected_page" not in self._session_state:
            self._session_state.selected_page = NavigationModel.get_default_page()
        return self._session_state.selected_page
    
    def set_selected_page(self, page: str) -> None:
        """선택된 페이지 설정"""
        self._session_state.selected_page = page
    
    def navigate_to(self, page: str) -> None:
        """페이지 네비게이션"""
        self._session_state.navigate_to = page
    
    def get_selected_dataset(self) -> Optional[str]:
        """선택된 데이터셋 반환"""
        return self._session_state.get("selected_dataset")
    
    def set_selected_dataset(self, dataset: str) -> None:
        """선택된 데이터셋 설정"""
        self._session_state.selected_dataset = dataset
    
    def get_evaluation_completed(self) -> bool:
        """평가 완료 상태 반환"""
        return self._session_state.get("evaluation_completed", False)
    
    def set_evaluation_completed(self, completed: bool) -> None:
        """평가 완료 상태 설정"""
        self._session_state.evaluation_completed = completed
    
    def get_latest_evaluation_result(self) -> Optional[Dict[str, Any]]:
        """최신 평가 결과 반환"""
        return self._session_state.get("latest_evaluation_result")
    
    def set_latest_evaluation_result(self, result: Dict[str, Any]) -> None:
        """최신 평가 결과 설정"""
        self._session_state.latest_evaluation_result = result
    
    def get_selected_evaluation_index(self) -> Optional[int]:
        """선택된 평가 인덱스 반환"""
        return self._session_state.get("selected_evaluation_index")
    
    def set_selected_evaluation_index(self, index: int) -> None:
        """선택된 평가 인덱스 설정"""
        self._session_state.selected_evaluation_index = index