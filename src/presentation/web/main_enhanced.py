"""
RAGTrace Dashboard - Enhanced with Full Features

main 브랜치의 모든 기능을 통합한 완전한 RAGTrace 대시보드입니다.
무한 루프 문제를 해결하면서 모든 기능을 유지합니다.
"""

import json
import sqlite3
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 페이지 설정을 가장 먼저 실행
st.set_page_config(
    page_title="RAGTrace 대시보드",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.domain.prompts import PromptType
from src.utils.paths import (
    DATABASE_PATH,
    get_available_datasets,
    get_evaluation_data_path,
)


# 페이지 정의
def load_pages():
    """사용 가능한 페이지 목록 반환"""
    return {
        "🎯 Overview": "메인 대시보드",
        "🚀 New Evaluation": "새 평가 실행",
        "📈 Historical": "과거 평가 결과",
        "📚 Detailed Analysis": "상세 분석",
        "📖 Metrics Explanation": "메트릭 설명",
        "⚡ Performance": "성능 모니터링",
    }


# 사이드바 및 네비게이션
st.sidebar.title("🔍 RAGTrace 대시보드")

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


# 메인 함수들
def main():
    """메인 애플리케이션"""
    st.title("🔍 RAGTrace - RAG 성능 추적 대시보드")
    st.markdown("---")
    show_overview()


def show_overview():
    """메인 오버뷰 대시보드"""
    st.header("📊 평가 결과 개요")
    
    # 방금 완료된 평가가 있으면 축하 메시지 표시
    if st.session_state.get("evaluation_completed", False):
        st.success("🎉 새로운 평가가 방금 완료되었습니다!")
        # 한 번 표시 후 상태 초기화
        st.session_state.evaluation_completed = False

    # 액션 버튼들
    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

    with col1:
        if st.button(
            "🚀 새 평가 실행", type="primary", help="새로운 RAG 평가를 시작합니다"
        ):
            st.session_state.navigate_to = "🚀 New Evaluation"
            st.rerun()

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
        st.info(
            "📝 아직 평가 결과가 없습니다. '새 평가 실행' 버튼을 클릭하여 첫 평가를 시작하세요!"
        )
        st.markdown("---")
        st.markdown("### 🤔 RAGAS 메트릭이 궁금하신가요?")
        st.markdown(
            "📚 사이드바에서 **'Metrics Guide'**를 선택하면 각 점수가 무엇을 의미하는지 쉽게 알아볼 수 있습니다!"
        )


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

        for metric, color in zip(metrics, colors, strict=False):
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


def show_new_evaluation_page():
    """새 평가 실행 페이지"""
    st.title("🚀 새 평가 실행")
    st.markdown("---")
    
    # LLM 선택 UI 표시
    selected_llm = show_llm_selector()
    
    st.markdown("---")
    
    # 임베딩 선택 UI 표시
    selected_embedding = show_embedding_selector()
    
    st.markdown("---")
    
    # 프롬프트 선택 UI 표시
    selected_prompt_type = show_prompt_selector()
    
    st.markdown("---")
    
    # 데이터셋 선택
    st.markdown("### 📊 데이터셋 선택")
    existing_datasets = get_available_datasets()
    if not existing_datasets:
        st.error("❌ 사용 가능한 평가 데이터셋이 없습니다.")
        st.info("data/ 디렉토리에 JSON 형식의 평가 데이터를 추가하세요.")
        return
    
    # session_state에 선택된 데이터셋 저장
    if "selected_dataset" not in st.session_state:
        st.session_state.selected_dataset = existing_datasets[0]
    
    # 현재 선택된 데이터셋의 인덱스 찾기
    try:
        current_index = existing_datasets.index(st.session_state.selected_dataset)
    except ValueError:
        current_index = 0
        st.session_state.selected_dataset = existing_datasets[0]
    
    # 데이터셋 선택 UI
    selected_dataset = st.selectbox(
        "평가할 데이터셋을 선택하세요:",
        existing_datasets,
        index=current_index,
        key="dataset_selector_box",
        help="평가에 사용할 QA 데이터셋을 선택합니다."
    )
    
    # 선택이 변경되면 session_state 업데이트
    st.session_state.selected_dataset = selected_dataset
    
    # 데이터셋 정보 표시
    dataset_path = get_evaluation_data_path(selected_dataset)
    if dataset_path:
        try:
            with open(dataset_path, encoding="utf-8") as f:
                qa_data = json.load(f)
                st.info(f"📋 선택된 데이터셋: **{selected_dataset}** ({len(qa_data)}개 QA 쌍)")
        except Exception as e:
            st.warning(f"데이터셋 정보 로드 실패: {e}")
    
    st.markdown("---")
    
    # 평가 설정 요약
    st.markdown("### 📋 평가 설정 요약")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.write(f"**🤖 LLM 모델:** {selected_llm}")
    with col2:
        st.write(f"**🔍 임베딩 모델:** {selected_embedding}")
    with col3:
        st.write(f"**🎯 프롬프트 타입:** {selected_prompt_type.value}")
    with col4:
        st.write(f"**📊 데이터셋:** {selected_dataset}")
    
    st.markdown("---")
    
    # 평가 실행 버튼들
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← 뒤로가기"):
            st.session_state.navigate_to = "🎯 Overview"
            st.rerun()
    
    with col2:
        if st.button("🚀 평가 시작", type="primary", use_container_width=True):
            execute_evaluation(selected_prompt_type, selected_dataset, selected_llm, selected_embedding)
    
    with col3:
        st.write("")  # 빈 공간


# 컴포넌트 함수들 (지연 로딩)
def show_llm_selector():
    """LLM 선택기 (지연 로딩)"""
    try:
        from src.presentation.web.components.llm_selector import show_llm_selector as _show_llm_selector
        return _show_llm_selector()
    except ImportError:
        # 컴포넌트가 없으면 간단한 대체 UI
        return st.selectbox("LLM 모델 선택", ["gemini", "hcx"], key="llm_selector")


def show_embedding_selector():
    """임베딩 선택기 (지연 로딩)"""
    try:
        from src.presentation.web.components.embedding_selector import show_embedding_selector as _show_embedding_selector
        return _show_embedding_selector()
    except ImportError:
        # 컴포넌트가 없으면 간단한 대체 UI
        return st.selectbox("임베딩 모델 선택", ["gemini", "bge_m3", "hcx"], key="embedding_selector")


def show_prompt_selector():
    """프롬프트 선택기 (지연 로딩)"""
    try:
        from src.presentation.web.components.prompt_selector import show_prompt_selector as _show_prompt_selector
        return _show_prompt_selector()
    except ImportError:
        # 컴포넌트가 없으면 간단한 대체 UI
        prompt_options = [PromptType.DEFAULT, PromptType.KOREAN_FORMAL, PromptType.NUCLEAR_HYDRO_TECH]
        selected = st.selectbox("프롬프트 타입 선택", 
                               [p.value for p in prompt_options], 
                               key="prompt_selector")
        return next(p for p in prompt_options if p.value == selected)


def execute_evaluation(prompt_type: PromptType, dataset_name: str, llm_type: str, embedding_type: str):
    """평가 실행 로직 (지연 로딩 적용)"""
    with st.spinner("🔄 평가를 실행 중입니다..."):
        try:
            # 평가 설정 정보 표시
            st.markdown("### 🔧 평가 설정")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"🤖 **LLM 모델**: {llm_type}")
                st.info(f"📊 **데이터셋**: {dataset_name}")
            
            with col2:
                st.info(f"🔍 **임베딩 모델**: {embedding_type}")
                st.info(f"🎯 **프롬프트 타입**: {prompt_type.value}")
            
            # 프롬프트 타입 설명 추가
            if prompt_type == PromptType.DEFAULT:
                st.success("📝 **기본 RAGAS 프롬프트 (영어)** - 범용적이고 안정적인 평가")
            elif prompt_type == PromptType.NUCLEAR_HYDRO_TECH:
                st.success("⚛️ **원자력/수력 기술 문서 특화 프롬프트** - 기술 정확성과 안전 규정에 최적화")
            elif prompt_type == PromptType.KOREAN_FORMAL:
                st.success("📋 **한국어 공식 문서 특화 프롬프트** - 정책 문서와 법규 해석에 최적화")
            
            st.markdown("---")

            # HCX 선택 시 API 키 확인
            if llm_type == "hcx" or embedding_type == "hcx":
                from src.config import settings
                if not settings.CLOVA_STUDIO_API_KEY:
                    st.error("❌ HCX 모델을 사용하려면 .env 파일에 CLOVA_STUDIO_API_KEY를 설정해야 합니다.")
                    return

            # 컨테이너 로딩 (지연 로딩)
            st.info("🔧 평가 시스템 초기화 중...")
            
            # 새로운 컨테이너 방식 사용
            from src.container import container
            from src.container.factories.evaluation_use_case_factory import EvaluationRequest
            
            request = EvaluationRequest(
                llm_type=llm_type,
                embedding_type=embedding_type,
                prompt_type=prompt_type
            )
            evaluation_use_case, llm_adapter, embedding_adapter = container.create_evaluation_use_case(request)
            
            st.info("📊 데이터셋 로딩 및 검증 중...")
            
            # 진행 상황 표시
            progress_placeholder = st.empty()
            
            with progress_placeholder.container():
                st.info("⚡ 평가 실행 중... (최대 30초 소요)")
                progress_bar = st.progress(0)
                progress_text = st.empty()
                
                # 평가 실행
                progress_text.text("평가 시작...")
                progress_bar.progress(25)
                
                evaluation_result = evaluation_use_case.execute(
                    dataset_name=dataset_name
                )
                
                progress_bar.progress(100)
                progress_text.text("평가 완료!")
            
            # 진행 상황 표시 제거
            progress_placeholder.empty()

            # 결과 저장
            result_dict = evaluation_result.to_dict()
            if "metadata" not in result_dict:
                result_dict["metadata"] = {}
            result_dict["metadata"]["llm_type"] = llm_type
            result_dict["metadata"]["embedding_type"] = embedding_type
            result_dict["metadata"]["dataset"] = dataset_name
            result_dict["metadata"]["prompt_type"] = prompt_type.value

            dataset_path = get_evaluation_data_path(dataset_name)
            if dataset_path:
                try:
                    with open(dataset_path, encoding="utf-8") as f:
                        qa_data = json.load(f)
                        qa_count = len(result_dict.get("individual_scores", []))
                        result_dict["qa_data"] = qa_data[:qa_count]
                except Exception as e:
                    st.warning(f"QA 데이터 로드 실패: {e}")

            save_evaluation_result(result_dict)

            st.success("✅ 평가가 완료되었습니다!")
            st.balloons()
            
            # 평가 결과 요약 표시
            st.markdown("### 📊 평가 결과")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🏆 RAGAS Score", f"{result_dict.get('ragas_score', 0):.3f}")
            with col2:
                st.metric("✅ Faithfulness", f"{result_dict.get('faithfulness', 0):.3f}")
            with col3:
                st.metric("🎯 Answer Relevancy", f"{result_dict.get('answer_relevancy', 0):.3f}")
            with col4:
                st.metric("🔄 Context Recall", f"{result_dict.get('context_recall', 0):.3f}")
            
            # 결과 페이지로 이동
            st.markdown("---")
            
            # 평가 완료 상태 저장
            st.session_state.evaluation_completed = True
            st.session_state.latest_evaluation_result = result_dict
            
            st.info("💡 평가가 완료되었습니다! 결과를 확인해보세요.")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("📊 Overview 페이지로 이동", type="primary", use_container_width=True, key="goto_overview"):
                    st.session_state.navigate_to = "🎯 Overview"
                    st.rerun()
            
            with col2:
                if st.button("📈 Historical 페이지로 이동", type="secondary", use_container_width=True, key="goto_historical"):
                    st.session_state.navigate_to = "📈 Historical"
                    st.rerun()

        except Exception as e:
            st.error(f"❌ 평가 중 오류 발생: {str(e)}")
            st.exception(e)


def show_historical():
    """히스토리 페이지"""
    st.header("📈 평가 이력")

    history = load_evaluation_history()

    if history:
        df = pd.DataFrame(history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # 테이블 표시
        st.subheader("📋 평가 이력 테이블")

        # 각 평가에 대한 상세 정보
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

                    # 상세 분석 페이지로 이동 버튼
                    if st.button("🔍 상세 분석", key=f"detail_btn_{i}"):
                        st.session_state.selected_evaluation_index = i
                        st.session_state.navigate_to = "📚 Detailed Analysis"
                        st.rerun()

        # 전체 테이블 표시
        st.subheader("📊 전체 평가 이력")
        st.dataframe(df, use_container_width=True)

        # 평가 비교
        st.subheader("📊 평가 비교")

        if len(df) > 1:
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

    fig.update_layout(
        title="📊 평가 결과 비교", barmode="group", yaxis=dict(range=[0, 1]), height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def show_detailed_analysis():
    """상세 분석 페이지"""
    try:
        from src.presentation.web.components.detailed_analysis import (
            show_detailed_analysis as show_detailed_component,
        )
        show_detailed_component()
    except ImportError:
        st.header("📚 상세 분석")
        st.info("상세 분석 컴포넌트를 로딩 중입니다...")
        st.write("이 기능은 구현 중입니다.")


def show_metrics_guide():
    """메트릭 가이드 페이지"""
    try:
        from src.presentation.web.components.metrics_explanation import (
            show_metrics_explanation as show_metrics_component,
        )
        show_metrics_component()
    except ImportError:
        st.header("📖 메트릭 설명")
        st.markdown("""
        ### RAGAS 메트릭 설명
        
        **🏆 RAGAS Score**: 전체 종합 점수
        - 모든 메트릭의 조화 평균
        - 0.0 ~ 1.0 범위
        
        **✅ Faithfulness**: 답변의 사실 정확성
        - 생성된 답변이 제공된 컨텍스트에 얼마나 충실한지 측정
        
        **🎯 Answer Relevancy**: 답변의 관련성
        - 생성된 답변이 질문과 얼마나 관련이 있는지 측정
        
        **🔄 Context Recall**: 컨텍스트 재현율
        - 관련 정보가 검색된 컨텍스트에 얼마나 포함되어 있는지 측정
        
        **📍 Context Precision**: 컨텍스트 정밀도
        - 검색된 컨텍스트가 얼마나 관련성이 높은지 측정
        """)


def show_performance():
    """성능 모니터링 페이지"""
    try:
        from src.presentation.web.components.performance_monitor import (
            show_performance_monitor as show_performance_component,
        )
        show_performance_component()
    except ImportError:
        st.header("⚡ 성능 모니터링")
        st.info("성능 모니터링 컴포넌트를 로딩 중입니다...")
        st.write("이 기능은 구현 중입니다.")


# 데이터베이스 함수들
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


# 페이지 라우팅
if page == "🎯 Overview":
    main()
elif page == "🚀 New Evaluation":
    show_new_evaluation_page()
elif page == "📈 Historical":
    show_historical()
elif page == "📚 Detailed Analysis":
    show_detailed_analysis()
elif page == "📖 Metrics Explanation":
    show_metrics_guide()
elif page == "⚡ Performance":
    show_performance()
else:
    main()


if __name__ == "__main__":
    main() 