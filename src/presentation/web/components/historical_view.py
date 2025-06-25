"""
Historical View Component

히스토리 페이지 컴포넌트입니다. (기존 코드 분리)
"""

import streamlit as st
import pandas as pd

from ..models.session_model import SessionManager
from ..services.database_service import DatabaseService
from ..services.chart_service import ChartService


def show_historical():
    """히스토리 페이지"""
    st.header("📈 평가 이력")
    
    session = SessionManager()
    database = DatabaseService()

    # 상세 분석으로 이동하는 안내
    st.info(
        "💡 특정 평가의 상세 분석을 보려면 '상세 분석' 페이지에서 평가를 선택하세요."
    )

    history = database.load_evaluation_history()

    if history:
        df = pd.DataFrame(history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # 테이블 표시 및 상세 분석 버튼 추가
        st.subheader("📋 평가 이력 테이블")

        # 각 평가에 대한 상세 정보와 상세 분석 버튼
        for i, row in df.iterrows():
            with st.expander(
                f"평가 #{i+1} - {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
            ):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.metric("RAGAS 점수", f"{row.get('ragas_score', 0):.3f}")
                    st.metric("Faithfulness", f"{row.get('faithfulness', 0):.3f}")

                with col2:
                    st.metric(
                        "Answer Relevancy", f"{row.get('answer_relevancy', 0):.3f}"
                    )
                    st.metric("Context Recall", f"{row.get('context_recall', 0):.3f}")

                with col3:
                    st.metric(
                        "Context Precision", f"{row.get('context_precision', 0):.3f}"
                    )
                    st.metric(
                        "Answer Correctness", f"{row.get('answer_correctness', 0):.3f}"
                    )

                    # 상세 분석 페이지로 이동 버튼
                    if st.button("🔍 상세 분석", key=f"detail_btn_{i}"):
                        # 선택된 평가 인덱스를 세션 상태에 저장
                        session.set_selected_evaluation_index(i)
                        session.navigate_to("📚 Detailed Analysis")
                        st.rerun()

        # 전체 테이블도 표시
        st.subheader("📊 전체 평가 이력")
        st.dataframe(df, use_container_width=True)

        # 상세 비교 차트
        st.subheader("📊 평가 비교")

        if len(df) > 1:
            # 사용자가 비교할 평가 선택
            col1, col2 = st.columns(2)

            with col1:
                eval1_idx = st.selectbox(
                    "첫 번째 평가",
                    range(len(df)),
                    format_func=lambda x: f"{df.iloc[x]['timestamp'].strftime('%Y-%m-%d %H:%M')} (#{x+1})",
                )

            with col2:
                eval2_idx = st.selectbox(
                    "두 번째 평가",
                    range(len(df)),
                    index=min(1, len(df) - 1),
                    format_func=lambda x: f"{df.iloc[x]['timestamp'].strftime('%Y-%m-%d %H:%M')} (#{x+1})",
                )

            if eval1_idx != eval2_idx:
                chart_service = ChartService()
                comparison_fig = chart_service.create_comparison_chart(
                    df.iloc[eval1_idx].to_dict(), 
                    df.iloc[eval2_idx].to_dict()
                )
                st.plotly_chart(comparison_fig, use_container_width=True)

    else:
        st.info("�� 아직 평가 이력이 없습니다.")