"""
Historical View

히스토리 페이지 뷰입니다.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any

from .base_view import BaseView


class HistoricalView(BaseView):
    """히스토리 페이지 뷰"""
    
    def __init__(self, session_manager):
        super().__init__(session_manager)
        self._db_service = None  # 지연 로딩
        self._chart_service = None  # 지연 로딩

    @property
    def db_service(self):
        """DatabaseService를 지연 로딩으로 가져옵니다."""
        if self._db_service is None:
            from ..services import DatabaseService
            self._db_service = DatabaseService()
        return self._db_service
    
    @property
    def chart_service(self):
        """ChartService를 지연 로딩으로 가져옵니다."""
        if self._chart_service is None:
            from ..services import ChartService
            self._chart_service = ChartService()
        return self._chart_service

    def render(self) -> None:
        """히스토리 페이지 렌더링"""
        st.title("📈 Historical Analysis")
        st.write("과거에 실행된 모든 평가 이력을 확인하고, 성능 추이를 분석합니다.")
        
        history = self.db_service.load_evaluation_history()
        
        if not history:
            st.warning("평가 이력이 없습니다.")
            return

        df = pd.DataFrame(history).sort_values(by="timestamp", ascending=False).reset_index(drop=True)
        
        # --- Performance Trends ---
        st.subheader("Performance Trends")
        trend_chart = self.chart_service.create_trend_chart(df)
        st.altair_chart(trend_chart, use_container_width=True)
        
        # --- Evaluation History Table ---
        st.subheader("Evaluation History")
        st.dataframe(df[['timestamp', 'model', 'ragas_score', 'faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']])

        # --- Detailed Analysis ---
        st.subheader("Detailed Analysis")
        
        # AppState에서 선택된 인덱스 가져오기
        # 이전에 선택된 인덱스가 유효한지 확인
        if self.state.selected_evaluation_index is None or self.state.selected_evaluation_index >= len(df):
            self.state.selected_evaluation_index = 0

        selected_index = st.selectbox(
            "Select an evaluation to see details:",
            options=df.index,
            format_func=lambda x: f"Evaluation on {pd.to_datetime(df.loc[x, 'timestamp']).strftime('%Y-%m-%d %H:%M')} (Score: {df.loc[x, 'ragas_score']:.3f})",
            index=self.state.selected_evaluation_index
        )
        
        if selected_index is not None and selected_index != self.state.selected_evaluation_index:
            self.state.selected_evaluation_index = selected_index
            st.rerun() # 선택 변경 시 즉시 UI 업데이트

        if self.state.selected_evaluation_index is not None:
            st.write(f"#### Details for Evaluation on {pd.to_datetime(df.loc[self.state.selected_evaluation_index, 'timestamp']).strftime('%Y-%m-%d %H:%M')}")
            # 전체 데이터를 보여주기 위해 to_dict() 사용
            st.json(df.loc[self.state.selected_evaluation_index].to_dict())