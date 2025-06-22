"""
AppState Model

Streamlit 세션 상태를 중앙에서 관리하기 위한 단일 상태 객체입니다.
"""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class EvaluationState(BaseModel):
    """평가 관련 상태"""
    is_completed: bool = False
    result: Optional[Dict[str, Any]] = None


class AppState(BaseModel):
    """애플리케이션 전체 세션 상태"""
    
    # Navigation
    selected_page: str = "🔍 Overview"
    
    # Data Selection
    selected_dataset: Optional[str] = None
    
    # Evaluation
    evaluation: EvaluationState = Field(default_factory=EvaluationState)
    
    # History
    evaluation_history: List[Dict[str, Any]] = Field(default_factory=list)
    selected_evaluation_index: Optional[int] = None

    def clear_evaluation_state(self):
        """평가 상태 초기화"""
        self.evaluation = EvaluationState()
        self.selected_evaluation_index = None 