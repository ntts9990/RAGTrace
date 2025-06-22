"""
Base View

모든 뷰의 기본 클래스입니다.
"""

from abc import ABC, abstractmethod
from ..models.session_model import SessionManager


class BaseView(ABC):
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    @property
    def state(self):
        """현재 애플리케이션 상태에 대한 바로가기"""
        return self.session_manager.state
        
    @abstractmethod
    def render(self):
        """페이지 콘텐츠를 렌더링합니다."""
        pass

"""
Historical View Component

과거 평가 이력을 보여주는 컴포넌트입니다. (현재는 View로 대체됨)
"""

import streamlit as st
import pandas as pd

from ..models.session_model import SessionManager
# ... (이하 코드는 현재 사용되지 않으므로 그대로 둠) 