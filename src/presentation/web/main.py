"""
RAGAS 평가 결과 대시보드
직관적이고 비교 가능한 시각화 제공
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.utils.paths import get_available_datasets, DATABASE_PATH, get_evaluation_data_path
# 페이지 정의 (간단한 딕셔너리로 대체)
def load_pages():
    """사용 가능한 페이지 목록 반환"""
    return {
        "🎯 Overview": "메인 대시보드",
        "📈 Historical": "과거 평가 결과",
        "📚 Detailed Analysis": "상세 분석",
        "📖 Metrics Explanation": "메트릭 설명",
        "⚡ Performance": "성능 모니터링"
    }
from src.application.use_cases import RunEvaluationUseCase
from src.infrastructure.evaluation import RagasEvalAdapter
from src.infrastructure.llm.gemini_adapter import GeminiAdapter
from src.infrastructure.repository.file_adapter import FileRepositoryAdapter

# 대시보드 컴포넌트
from src.presentation.web.components.detailed_analysis import show_detailed_analysis as show_detailed_component
from src.presentation.web.components.metrics_explanation import show_metrics_explanation as show_metrics_component
from src.presentation.web.components.performance_monitor import show_performance_monitor as show_performance_component

# --- 페이지 설정 ---
st.set_page_config(
    page_title="RAGTrace 대시보드",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 사이드바 ---
st.sidebar.title("🔍 RAGTrace 대시보드")

# --- 페이지 로드 및 라우팅 ---
pages = load_pages()
page_keys = list(pages.keys())

# 페이지 네비게이션 상태 관리
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "🎯 Overview"

# 네비게이션 버튼으로 페이지 이동 처리
if "navigate_to" in st.session_state:
    st.session_state.selected_page = st.session_state.navigate_to
    del st.session_state.navigate_to


# 페이지 선택 콜백 함수
def on_page_change():
    st.session_state.selected_page = st.session_state.page_selector


# 사이드바에서 페이지 선택
st.sidebar.selectbox(
    "페이지 선택",
    page_keys,
    index=page_keys.index(st.session_state.selected_page),
    key="page_selector",
    on_change=on_page_change,
)

page = st.session_state.selected_page

# --- 메인 페이지 ---
def main_page():
    st.title("🔍 RAGTrace - RAG 성능 추적 대시보드")
    st.markdown("---")

    if ('evaluation_results' in st.session_state and
            st.session_state.evaluation_results):
        show_overview()
    else:
        show_overview()


def show_overview():
    """메인 오버뷰 대시보드"""
    st.header("📊 평가 결과 개요")

    # 액션 버튼들
    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

    with col1:
        if st.button("🚀 새 평가 실행", type="primary", help="새로운 RAG 평가를 시작합니다"):
            run_new_evaluation()

    with col2:
        if st.button("🔄 새로고침", help="최신 결과를 다시 로드합니다"):
            st.rerun()

    with col3:
        if st.button("📈 이력보기", help="과거 평가 결과를 확인합니다"):
            st.session_state.navigate_to = "📈 Historical"
            st.rerun()

    with col4:
        if st.button("📚 메트릭 가이드", help="RAGAS 점수의 의미를 알아보세요"):
            st.session_state.navigate_to = "📖 Metrics Explanation"
            st.rerun()

    # 최신 평가 결과 로드
    latest_result = load_latest_result()

    if latest_result:
        show_metric_cards(latest_result)
        show_metric_charts(latest_result)
        show_recent_trends()
    else:
        st.info("📝 아직 평가 결과가 없습니다. '새 평가 실행' 버튼을 클릭하여 첫 평가를 시작하세요!")
        st.markdown("---")
        st.markdown("### 🤔 RAGAS 메트릭이 궁금하신가요?")
        st.markdown("📚 사이드바에서 **'Metrics Guide'**를 선택하면 각 점수가 무엇을 의미하는지 쉽게 알아볼 수 있습니다!")


def show_metric_cards(result):
    """메트릭 카드 표시"""
    st.subheader("🎯 핵심 지표")

    col1, col2, col3, col4, col5 = st.columns(5)

    metrics = [
        ("종합 점수", result.get("ragas_score", 0), "🏆"),
        ("Faithfulness", result.get("faithfulness", 0), "✅"),
        ("Answer Relevancy", result.get("answer_relevancy", 0), "🎯"),
        ("Context Recall", result.get("context_recall", 0), "🔄"),
        ("Context Precision", result.get("context_precision", 0), "📍"),
    ]

    for i, (name, value, icon) in enumerate(metrics):
        with [col1, col2, col3, col4, col5][i]:
            # 점수에 따른 색상
            if value >= 0.8:
                color = "green"
            elif value >= 0.6:
                color = "orange"
            else:
                color = "red"

            # 이전 평가와의 비교를 위한 델타 계산
            previous_result = get_previous_result()
            delta_value = None
            if previous_result and name.lower().replace(" ", "_") in previous_result:
                prev_value = previous_result[name.lower().replace(" ", "_")]
                delta_value = value - prev_value

            st.metric(
                label=f"{icon} {name}",
                value=f"{value:.3f}",
                delta=f"{delta_value:.3f}" if delta_value is not None else None,
            )


def show_metric_charts(result):
    """메트릭 시각화 차트"""
    st.subheader("📈 시각화")

    col1, col2 = st.columns(2)

    with col1:
        # 레이더 차트
        show_radar_chart(result)

    with col2:
        # 바 차트
        show_bar_chart(result)


def show_radar_chart(result):
    """레이더 차트 생성"""
    metrics = [
        "faithfulness",
        "answer_relevancy",
        "context_recall",
        "context_precision",
    ]
    values = [result.get(metric, 0) for metric in metrics]
    labels = ["Faithfulness", "Answer Relevancy", "Context Recall", "Context Precision"]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],  # 첫 번째 값을 마지막에 추가하여 차트를 닫음
            theta=labels + [labels[0]],
            fill="toself",
            name="RAGAS 점수",
            line_color="rgb(32, 201, 151)",
        )
    )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title="📊 메트릭 균형도",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def show_bar_chart(result):
    """바 차트 생성"""
    metrics = [
        "faithfulness",
        "answer_relevancy",
        "context_recall",
        "context_precision",
    ]
    values = [result.get(metric, 0) for metric in metrics]
    labels = ["Faithfulness", "Answer Relevancy", "Context Recall", "Context Precision"]

    # 색상 매핑
    colors = ["green" if v >= 0.8 else "orange" if v >= 0.6 else "red" for v in values]

    fig = go.Figure(data=[go.Bar(x=labels, y=values, marker_color=colors)])

    fig.update_layout(
        title="📊 메트릭별 성능",
        yaxis_title="점수",
        yaxis=dict(range=[0, 1]),
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def show_recent_trends():
    """최근 트렌드 표시"""
    st.subheader("📈 최근 트렌드")

    # 히스토리 데이터 로드
    history = load_evaluation_history(limit=10)

    if len(history) > 1:
        df = pd.DataFrame(history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # 트렌드 차트
        fig = go.Figure()

        metrics = [
            "faithfulness",
            "answer_relevancy",
            "context_recall",
            "context_precision",
            "ragas_score",
        ]
        colors = ["blue", "green", "orange", "red", "purple"]

        for metric, color in zip(metrics, colors):
            if metric in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df["timestamp"],
                        y=df[metric],
                        mode="lines+markers",
                        name=metric.replace("_", " ").title(),
                        line=dict(color=color),
                    )
                )

        fig.update_layout(
            title="📈 평가 점수 트렌드",
            xaxis_title="시간",
            yaxis_title="점수",
            yaxis=dict(range=[0, 1]),
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 트렌드 표시를 위해 더 많은 평가 데이터가 필요합니다.")


def run_new_evaluation():
    """새로운 평가 실행"""
    with st.spinner("🔄 평가를 실행 중입니다..."):
        try:
            # 사용자가 선택할 수 있는 데이터셋 옵션
            import os
            import random

            # 중앙 경로 관리 모듈에서 사용 가능한 데이터셋 가져오기
            existing_datasets = get_available_datasets()

            if not existing_datasets:
                st.error("❌ 사용 가능한 평가 데이터셋이 없습니다.")
                return

            # 랜덤하게 데이터셋 선택 (다양성을 위해)
            selected_dataset = random.choice(existing_datasets)
            st.info(f"📊 선택된 데이터셋: {selected_dataset.split('/')[-1]}")

            # 기존 평가 서비스 활용
            llm_adapter = GeminiAdapter(model_name="gemini-2.5-flash-preview-05-20", requests_per_minute=1000)

            # 중앙 경로 관리 모듈을 사용하여 안정적인 경로 획득
            dataset_path = get_evaluation_data_path(selected_dataset)
            if not dataset_path:
                st.error(f"데이터셋 '{selected_dataset}'을 찾을 수 없습니다.")
                return
            
            repository_adapter = FileRepositoryAdapter(file_path=str(dataset_path))

            ragas_eval_adapter = RagasEvalAdapter()

            evaluation_use_case = RunEvaluationUseCase(
                llm_port=llm_adapter,
                repository_port=repository_adapter,
                evaluation_runner=ragas_eval_adapter,
            )

            # 평가 실행
            evaluation_result = evaluation_use_case.execute()

            # 결과 저장 (데이터셋 정보 포함)
            result_dict = evaluation_result.to_dict()
            result_dict["metadata"]["dataset"] = selected_dataset

            # QA 데이터도 함께 저장
            try:
                with open(dataset_path, "r", encoding="utf-8") as f:
                    qa_data = json.load(f)
                    # 실제 평가된 개수만큼만 저장
                    qa_count = len(result_dict.get("individual_scores", []))
                    result_dict["qa_data"] = qa_data[:qa_count]
            except Exception as e:
                st.warning(f"QA 데이터 로드 실패: {e}")

            save_evaluation_result(result_dict)

            st.success("✅ 평가가 완료되었습니다!")
            st.rerun()

        except Exception as e:
            st.error(f"❌ 평가 중 오류 발생: {str(e)}")


def show_historical():
    """히스토리 페이지"""
    st.header("📈 평가 이력")

    # 상세 분석으로 이동하는 안내
    st.info("💡 특정 평가의 상세 분석을 보려면 '상세 분석' 페이지에서 평가를 선택하세요.")

    history = load_evaluation_history()

    if history:
        df = pd.DataFrame(history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # 테이블 표시 및 상세 분석 버튼 추가
        st.subheader("📋 평가 이력 테이블")

        # 각 평가에 대한 상세 정보와 상세 분석 버튼
        for i, row in df.iterrows():
            with st.expander(f"평가 #{i+1} - {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.metric("RAGAS 점수", f"{row.get('ragas_score', 0):.3f}")
                    st.metric("Faithfulness", f"{row.get('faithfulness', 0):.3f}")

                with col2:
                    st.metric("Answer Relevancy", f"{row.get('answer_relevancy', 0):.3f}")
                    st.metric("Context Recall", f"{row.get('context_recall', 0):.3f}")

                with col3:
                    st.metric("Context Precision", f"{row.get('context_precision', 0):.3f}")

                    # 상세 분석 페이지로 이동 버튼
                    if st.button(f"🔍 상세 분석", key=f"detail_btn_{i}"):
                        # 선택된 평가 인덱스를 세션 상태에 저장
                        st.session_state.selected_evaluation_index = i
                        st.session_state.navigate_to = "📚 Detailed Analysis"
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
                show_comparison_chart(df.iloc[eval1_idx], df.iloc[eval2_idx])

    else:
        st.info("📝 아직 평가 이력이 없습니다.")


def show_comparison_chart(eval1, eval2):
    """두 평가 결과 비교 차트"""
    metrics = [
        "faithfulness",
        "answer_relevancy",
        "context_recall",
        "context_precision",
        "ragas_score",
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name=f'평가 1 ({eval1["timestamp"]})',
            x=metrics,
            y=[eval1.get(m, 0) for m in metrics],
            marker_color="lightblue",
        )
    )

    fig.add_trace(
        go.Bar(
            name=f'평가 2 ({eval2["timestamp"]})',
            x=metrics,
            y=[eval2.get(m, 0) for m in metrics],
            marker_color="darkblue",
        )
    )

    fig.update_layout(title="📊 평가 결과 비교", barmode="group", yaxis=dict(range=[0, 1]), height=400)

    st.plotly_chart(fig, use_container_width=True)


def show_detailed_analysis():
    """상세 분석 페이지"""
    show_detailed_component()


def show_metrics_guide():
    """메트릭 가이드 페이지"""
    show_metrics_component()


def show_performance():
    """성능 모니터링 페이지"""
    show_performance_component()


# 데이터 저장/로드 함수들


def init_db():
    """데이터베이스 초기화"""
    db_path = DATABASE_PATH
    db_path.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            faithfulness REAL,
            answer_relevancy REAL,
            context_recall REAL,
            context_precision REAL,
            ragas_score REAL,
            raw_data TEXT
        )
    """
    )

    conn.commit()
    conn.close()


def save_evaluation_result(result):
    """평가 결과 저장"""
    init_db()

    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO evaluations (
            timestamp, faithfulness, answer_relevancy, 
            context_recall, context_precision, ragas_score, raw_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            datetime.now().isoformat(),
            result.get("faithfulness", 0),
            result.get("answer_relevancy", 0),
            result.get("context_recall", 0),
            result.get("context_precision", 0),
            result.get("ragas_score", 0),
            json.dumps(result),
        ),
    )

    conn.commit()
    conn.close()


def load_latest_result():
    """최신 평가 결과 로드"""
    history = load_evaluation_history(limit=1)
    return history[0] if history else None


def load_evaluation_history(limit=None):
    """평가 이력 로드"""
    init_db()

    conn = sqlite3.connect(str(DATABASE_PATH))

    query = """
        SELECT timestamp, faithfulness, answer_relevancy, 
               context_recall, context_precision, ragas_score
        FROM evaluations 
        ORDER BY timestamp DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df.to_dict("records")


def get_previous_result():
    """이전 평가 결과 반환"""
    history = load_evaluation_history(limit=2)
    return history[1] if len(history) > 1 else None


# --- 페이지 라우팅 ---
if page == "🎯 Overview":
    main_page()
elif page == "📈 Historical":
    show_historical()
elif page == "📚 Detailed Analysis":
    show_detailed_analysis()
elif page == "📖 Metrics Explanation":
    show_metrics_guide()
elif page == "⚡ Performance":
    show_performance()
else:
    main_page()
