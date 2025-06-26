"""
RAGTrace Dashboard - Enhanced with Full Features

main 브랜치의 모든 기능을 통합한 완전한 RAGTrace 대시보드입니다.
"""

import json
import random
import sqlite3
from datetime import datetime
import warnings

# torch 관련 경고 무시
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", message=".*torch.classes.*")

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
from src.presentation.web.components.llm_selector import show_llm_selector
from src.presentation.web.components.embedding_selector import show_embedding_selector
from src.presentation.web.components.prompt_selector import show_prompt_selector


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


# 페이지 선택 콜백 함수
def on_page_change():
    st.session_state.selected_page = st.session_state.page_selector


# 메인 함수
def main():
    """메인 애플리케이션 - Streamlit 앱 시작점"""
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
    
    # 사이드바에서 페이지 선택
    st.sidebar.selectbox(
        "페이지 선택",
        page_keys,
        index=page_keys.index(st.session_state.selected_page),
        key="page_selector",
        on_change=on_page_change,
    )
    
    page = st.session_state.selected_page
    
    # 공통 헤더
    st.title("🔍 RAGTrace - RAG 성능 추적 대시보드")
    st.markdown("---")
    
    # 페이지 라우팅
    if page == "🎯 Overview":
        show_overview()
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
            "🚀 새 평가 실행", type="primary", help="새로운 RAG 평가를 시작합니다",
            key="overview_new_eval_btn"
        ):
            st.session_state.navigate_to = "🚀 New Evaluation"
            st.rerun()

    with col2:
        if st.button("🔄 새로고침", help="최신 결과를 다시 로드합니다", key="overview_refresh_btn"):
            st.rerun()

    with col3:
        if st.button("📈 이력보기", help="과거 평가 결과를 확인합니다", key="overview_history_btn"):
            st.session_state.navigate_to = "📈 Historical"
            st.rerun()

    with col4:
        if st.button("📚 메트릭 가이드", help="RAGAS 점수의 의미를 알아보세요", key="overview_guide_btn"):
            st.session_state.navigate_to = "📖 Metrics Explanation"
            st.rerun()

    # 최신 평가 결과 로드
    latest_result = load_latest_result()

    if latest_result:
        # 평가 기본 정보 표시
        show_evaluation_info(latest_result)
        show_metric_cards(latest_result)
        show_metric_charts(latest_result)
        show_export_section(latest_result)
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
    
    # 컨테이너 테스트 버튼 (기존 기능 유지)
    st.markdown("---")
    if st.button("🧪 컨테이너 테스트", key="overview_container_test_btn"):
        try:
            with st.spinner("컨테이너 로딩 중..."):
                from src.container import container
                from src.container.factories.evaluation_use_case_factory import EvaluationRequest
                
                request = EvaluationRequest(
                    llm_type="gemini",
                    embedding_type="gemini",
                    prompt_type=PromptType.DEFAULT
                )
                
                evaluation_use_case, llm_adapter, embedding_adapter = container.create_evaluation_use_case(request)
                st.success("✅ 컨테이너가 성공적으로 로딩되었습니다!")
                st.info(f"LLM Adapter: {type(llm_adapter).__name__}")
                st.info(f"Embedding Adapter: {type(embedding_adapter).__name__}")
                
        except Exception as e:
            st.error(f"❌ 컨테이너 로딩 실패: {str(e)}")


def show_evaluation_info(result):
    """평가 기본 정보 표시"""
    st.subheader("📋 평가 정보")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        qa_count = result.get('qa_count', 'N/A')
        st.markdown(f"**QA 개수**")
        st.markdown(f"<span style='font-size: 16px;'>{qa_count}</span>", unsafe_allow_html=True)
    
    with col2:
        eval_id = result.get('evaluation_id', 'N/A')
        if eval_id != 'N/A' and len(str(eval_id)) > 8:
            eval_id = str(eval_id)[:8]
        st.markdown(f"**평가 ID**")
        st.markdown(f"<span style='font-size: 16px;'>{eval_id}</span>", unsafe_allow_html=True)
    
    with col3:
        llm_model = result.get('llm_model', 'N/A')
        st.markdown(f"**LLM 모델**")
        st.markdown(f"<span style='font-size: 16px;'>{llm_model}</span>", unsafe_allow_html=True)
    
    with col4:
        embedding_model = result.get('embedding_model', 'N/A')
        st.markdown(f"**임베딩 모델**")
        st.markdown(f"<span style='font-size: 16px;'>{embedding_model}</span>", unsafe_allow_html=True)
    
    dataset_name = result.get('dataset_name', 'N/A')
    st.markdown(f"**데이터셋**: {dataset_name}")
    
    st.markdown("---")


def show_metric_cards(result):
    """메트릭 카드 표시"""
    st.subheader("🎯 핵심 지표")

    # answer_correctness가 있는지 확인
    has_answer_correctness = "answer_correctness" in result

    # 컬럼 수 동적 설정
    if has_answer_correctness:
        cols = st.columns(6)
    else:
        cols = st.columns(5)

    metrics = [
        ("종합 점수", result.get("ragas_score", 0), "🏆"),
        ("Faithfulness", result.get("faithfulness", 0), "✅"),
        ("Answer Relevancy", result.get("answer_relevancy", 0), "🎯"),
        ("Context Recall", result.get("context_recall", 0), "🔄"),
        ("Context Precision", result.get("context_precision", 0), "📍"),
    ]
    
    # answer_correctness가 있으면 추가
    if has_answer_correctness:
        metrics.append(("Answer Correctness", result.get("answer_correctness", 0), "✔️"))

    for i, (name, value, icon) in enumerate(metrics):
        with cols[i]:
            # 이전 평가와의 비교를 위한 델타 계산
            previous_result = get_previous_result()
            delta_value = None
            if previous_result and name.lower().replace(" ", "_") in previous_result:
                prev_value = previous_result[name.lower().replace(" ", "_")]
                # 안전한 타입 체크 및 변환
                if prev_value is not None and isinstance(prev_value, (int, float)) and isinstance(value, (int, float)):
                    delta_value = value - prev_value

            # 안전한 value 표시
            try:
                value_str = f"{float(value):.3f}" if value is not None else "0.000"
            except (ValueError, TypeError):
                value_str = "0.000"
            
            st.metric(
                label=f"{icon} {name}",
                value=value_str,
                delta=f"{delta_value:.3f}" if delta_value is not None else None,
            )

    # 평가 시간 정보 표시
    metadata = result.get("metadata", {})
    if metadata.get("total_duration_seconds"):
        st.subheader("⏱️ 평가 성능")
        
        time_col1, time_col2, time_col3 = st.columns(3)
        
        with time_col1:
            st.metric(
                label="⏱️ 총 평가 시간",
                value=f"{metadata.get('total_duration_minutes', 0):.1f}분",
                help=f"{metadata.get('total_duration_seconds', 0):.1f}초"
            )
        
        with time_col2:
            st.metric(
                label="📊 평균 문항 시간",
                value=f"{metadata.get('avg_time_per_item_seconds', 0):.1f}초",
                help="문항당 평균 처리 시간"
            )
        
        with time_col3:
            dataset_size = metadata.get('dataset_size', 0)
            throughput = dataset_size / metadata.get('total_duration_seconds', 1) * 60 if metadata.get('total_duration_seconds') else 0
            st.metric(
                label="🚀 처리 속도",
                value=f"{throughput:.1f}문항/분",
                help=f"총 {dataset_size}개 문항"
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


def show_export_section(result):
    """결과 내보내기 섹션"""
    st.subheader("📥 결과 내보내기")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 CSV 다운로드", key="download_csv_btn", help="상세 평가 결과를 CSV 파일로 다운로드"):
            try:
                from src.application.services.result_exporter import ResultExporter
                
                exporter = ResultExporter()
                csv_file = exporter.export_to_csv(result)
                
                # 파일 읽기
                with open(csv_file, 'rb') as f:
                    csv_data = f.read()
                
                st.download_button(
                    label="📄 CSV 파일 저장",
                    data=csv_data,
                    file_name=f"ragas_detailed_{result.get('metadata', {}).get('evaluation_id', 'unknown')}.csv",
                    mime="text/csv",
                    key="csv_download"
                )
                
                st.success("✅ CSV 파일이 준비되었습니다!")
                
            except Exception as e:
                st.error(f"❌ CSV 생성 실패: {str(e)}")
    
    with col2:
        if st.button("📈 요약 통계 CSV", key="download_summary_btn", help="메트릭별 기초 통계를 CSV로 다운로드"):
            try:
                from src.application.services.result_exporter import ResultExporter
                
                exporter = ResultExporter()
                summary_file = exporter.export_summary_csv(result)
                
                # 파일 읽기
                with open(summary_file, 'rb') as f:
                    summary_data = f.read()
                
                st.download_button(
                    label="📊 요약 CSV 저장",
                    data=summary_data,
                    file_name=f"ragas_summary_{result.get('metadata', {}).get('evaluation_id', 'unknown')}.csv",
                    mime="text/csv",
                    key="summary_download"
                )
                
                st.success("✅ 요약 통계 CSV가 준비되었습니다!")
                
            except Exception as e:
                st.error(f"❌ 요약 CSV 생성 실패: {str(e)}")
    
    with col3:
        if st.button("📋 분석 보고서", key="download_report_btn", help="상세 분석 보고서를 마크다운으로 다운로드"):
            try:
                from src.application.services.result_exporter import ResultExporter
                
                exporter = ResultExporter()
                report_file = exporter.generate_analysis_report(result)
                
                # 파일 읽기
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = f.read()
                
                st.download_button(
                    label="📄 보고서 저장",
                    data=report_data.encode('utf-8'),
                    file_name=f"ragas_analysis_{result.get('metadata', {}).get('evaluation_id', 'unknown')}.md",
                    mime="text/markdown",
                    key="report_download"
                )
                
                st.success("✅ 분석 보고서가 준비되었습니다!")
                
            except Exception as e:
                st.error(f"❌ 보고서 생성 실패: {str(e)}")
    
    # 전체 패키지 다운로드
    st.markdown("---")
    
    if st.button("📦 전체 패키지 다운로드", key="download_package_btn", help="CSV, 요약, 보고서를 모두 포함한 ZIP 파일"):
        try:
            import zipfile
            import tempfile
            from pathlib import Path
            
            from src.application.services.result_exporter import ResultExporter
            
            exporter = ResultExporter()
            
            # 임시 디렉토리에 모든 파일 생성
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # 모든 파일 생성
                files = exporter.export_full_package(result)
                
                # ZIP 파일 생성
                zip_path = temp_path / "ragas_evaluation_package.zip"
                
                with zipfile.ZipFile(zip_path, 'w') as zip_file:
                    for file_type, file_path in files.items():
                        zip_file.write(file_path, Path(file_path).name)
                
                # ZIP 파일 읽기
                with open(zip_path, 'rb') as f:
                    zip_data = f.read()
                
                st.download_button(
                    label="📦 ZIP 패키지 저장",
                    data=zip_data,
                    file_name=f"ragas_package_{result.get('metadata', {}).get('evaluation_id', 'unknown')}.zip",
                    mime="application/zip",
                    key="package_download"
                )
                
                st.success("✅ 전체 패키지가 준비되었습니다!")
                st.info("📋 포함된 파일: 상세 CSV, 요약 CSV, 분석 보고서")
                
        except Exception as e:
            st.error(f"❌ 패키지 생성 실패: {str(e)}")
            import traceback
            st.error(f"상세 오류: {traceback.format_exc()}")


def show_radar_chart(result):
    """레이더 차트 생성"""
    metrics = [
        "faithfulness",
        "answer_relevancy",
        "context_recall",
        "context_precision",
    ]
    labels = ["Faithfulness", "Answer Relevancy", "Context Recall", "Context Precision"]
    
    # answer_correctness가 있으면 추가
    if "answer_correctness" in result:
        metrics.append("answer_correctness")
        labels.append("Answer Correctness")
    
    values = [result.get(metric, 0) for metric in metrics]
    
    # 안전한 값 변환
    safe_values = []
    for v in values:
        try:
            safe_values.append(float(v) if v is not None else 0.0)
        except (ValueError, TypeError):
            safe_values.append(0.0)

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=safe_values + [safe_values[0]],  # 첫 번째 값을 마지막에 추가하여 차트를 닫음
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
    labels = ["Faithfulness", "Answer Relevancy", "Context Recall", "Context Precision"]
    
    # answer_correctness가 있으면 추가
    if "answer_correctness" in result:
        metrics.append("answer_correctness")
        labels.append("Answer Correctness")
    
    values = [result.get(metric, 0) for metric in metrics]
    
    # 안전한 값 변환
    safe_values = []
    for v in values:
        try:
            safe_values.append(float(v) if v is not None else 0.0)
        except (ValueError, TypeError):
            safe_values.append(0.0)

    # 색상 매핑
    colors = ["green" if v >= 0.8 else "orange" if v >= 0.6 else "red" for v in safe_values]

    fig = go.Figure(data=[go.Bar(x=labels, y=safe_values, marker_color=colors)])

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
    st.header("🚀 새 평가 실행")
    
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
    
    # 탭으로 기존 파일 선택과 새 파일 업로드 구분
    dataset_tab1, dataset_tab2 = st.tabs(["📁 파일 업로드", "📂 기존 데이터셋"])
    
    with dataset_tab1:
        st.markdown("#### 새 데이터셋 업로드")
        uploaded_file = st.file_uploader(
            "평가 데이터 파일을 선택하세요",
            type=["json", "xlsx", "xls", "csv"],
            help="JSON, Excel(.xlsx, .xls), CSV 파일을 지원합니다.",
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            # 파일 타입에 따른 처리
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            try:
                if file_extension == 'json':
                    # JSON 파일 직접 로드
                    qa_data = json.load(uploaded_file)
                    st.success(f"✅ JSON 파일 로드 완료: {uploaded_file.name} ({len(qa_data)}개 항목)")
                    
                elif file_extension in ['xlsx', 'xls', 'csv']:
                    # Excel/CSV 파일은 변환 필요
                    st.info("📄 Excel/CSV 파일을 JSON으로 변환 중...")
                    
                    # 임시 파일로 저장
                    import tempfile
                    import os
                    from pathlib import Path
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_file_path = tmp_file.name
                    
                    try:
                        # data importer 사용
                        from src.infrastructure.data_import.importers import ImporterFactory
                        
                        importer = ImporterFactory.create_importer(tmp_file_path)
                        evaluation_data_list = importer.import_data(tmp_file_path)
                        
                        # EvaluationData 객체를 dict로 변환
                        qa_data = [
                            {
                                "question": item.question,
                                "contexts": item.contexts,
                                "answer": item.answer,
                                "ground_truth": item.ground_truth
                            }
                            for item in evaluation_data_list
                        ]
                        
                        st.success(f"✅ {file_extension.upper()} 파일 변환 완료: {uploaded_file.name} ({len(qa_data)}개 항목)")
                        
                        # 변환된 데이터 미리보기
                        with st.expander("📋 변환된 데이터 미리보기 (처음 3개)"):
                            for i, item in enumerate(qa_data[:3]):
                                st.markdown(f"**항목 {i+1}:**")
                                st.json(item)
                        
                    finally:
                        # 임시 파일 삭제
                        os.unlink(tmp_file_path)
                else:
                    st.error(f"❌ 지원되지 않는 파일 형식: {file_extension}")
                    qa_data = None
                    
                # 업로드된 데이터를 session_state에 저장
                if qa_data:
                    st.session_state.uploaded_data = qa_data
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.session_state.use_uploaded_file = True
                    
            except Exception as e:
                st.error(f"❌ 파일 로드 실패: {str(e)}")
                st.info("파일 형식을 확인하고 다시 시도해주세요.")
    
    with dataset_tab2:
        st.markdown("#### 기존 데이터셋 선택")
        existing_datasets = get_available_datasets()
        if not existing_datasets:
            st.info("📝 기존 데이터셋이 없습니다. 파일을 업로드하거나 data/ 디렉토리에 추가하세요.")
            selected_dataset = None
        else:
            # session_state에 선택된 데이터셋 저장
            if "selected_dataset" not in st.session_state:
                st.session_state.selected_dataset = existing_datasets[0]
            
            # 현재 선택된 데이터셋의 인덱스 찾기
            try:
                current_index = existing_datasets.index(st.session_state.selected_dataset)
            except (ValueError, IndexError):
                current_index = 0
                st.session_state.selected_dataset = existing_datasets[0] if existing_datasets else None
            
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
            st.session_state.use_uploaded_file = False
            
            # 데이터셋 정보 표시
            dataset_path = get_evaluation_data_path(selected_dataset)
            if dataset_path:
                try:
                    from pathlib import Path
                    from src.infrastructure.data_import.importers import ExcelImporter, CSVImporter
                    
                    file_path_obj = Path(dataset_path)
                    file_extension = file_path_obj.suffix.lower()
                    
                    if file_extension in ['.xlsx', '.xls']:
                        # Excel 파일 처리
                        importer = ExcelImporter()
                        evaluation_data_list = importer.import_data(file_path_obj)
                        qa_count = len(evaluation_data_list)
                    elif file_extension == '.csv':
                        # CSV 파일 처리
                        importer = CSVImporter()
                        evaluation_data_list = importer.import_data(file_path_obj)
                        qa_count = len(evaluation_data_list)
                    else:
                        # JSON 파일 처리 (기본)
                        with open(dataset_path, encoding="utf-8") as f:
                            qa_data = json.load(f)
                            qa_count = len(qa_data)
                    
                    st.info(f"📋 선택된 데이터셋: **{selected_dataset}** ({qa_count}개 QA 쌍)")
                except Exception as e:
                    st.warning(f"데이터셋 정보 로드 실패: {e}")
    
    # 최종 선택된 데이터셋 이름 결정
    if st.session_state.get('use_uploaded_file', False) and st.session_state.get('uploaded_filename'):
        selected_dataset = st.session_state.uploaded_filename
    elif not st.session_state.get('use_uploaded_file', False) and dataset_tab2:
        selected_dataset = st.session_state.get('selected_dataset', None)
    
    st.markdown("---")
    
    # 평가 설정 요약
    st.markdown("### 📋 평가 설정 요약")
    col1, col2, col3, col4 = st.columns(4)
    
    # 표시명 매핑
    llm_display_names = {
        "gemini": "🌐 Google Gemini 2.5 Flash",
        "hcx": "🚀 NAVER HyperCLOVA X"
    }
    
    embedding_display_names = {
        "gemini": "🌐 Google Gemini Embedding",
        "bge_m3": "🎯 BGE-M3 Local Embedding", 
        "hcx": "🚀 NAVER HCX Embedding"
    }
    
    with col1:
        st.write(f"**🤖 LLM 모델:** {llm_display_names.get(selected_llm, selected_llm)}")
    with col2:
        st.write(f"**🔍 임베딩 모델:** {embedding_display_names.get(selected_embedding, selected_embedding)}")
    with col3:
        st.write(f"**🎯 프롬프트 타입:** {selected_prompt_type.value}")
    with col4:
        st.write(f"**📊 데이터셋:** {selected_dataset}")
    
    st.markdown("---")
    
    # 평가 실행 버튼들
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← 뒤로가기", key="new_eval_back_btn"):
            st.session_state.navigate_to = "🎯 Overview"
            st.rerun()
    
    with col2:
        if st.button("🚀 평가 시작", type="primary", use_container_width=True, key="new_eval_start_btn"):
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
        st.markdown("### 🤖 LLM 모델 선택")
        llm_options = {
            "🌐 Google Gemini 2.5 Flash": "gemini",
            "🚀 NAVER HyperCLOVA X": "hcx"
        }
        selected_display = st.selectbox(
            "사용할 LLM 모델을 선택하세요:",
            list(llm_options.keys()),
            key="llm_selector"
        )
        return llm_options[selected_display]


def show_embedding_selector():
    """임베딩 선택기 (지연 로딩)"""
    try:
        from src.presentation.web.components.embedding_selector import show_embedding_selector as _show_embedding_selector
        return _show_embedding_selector()
    except ImportError:
        # 컴포넌트가 없으면 간단한 대체 UI
        st.markdown("### 🔍 임베딩 모델 선택")
        embedding_options = {
            "🌐 Google Gemini Embedding": "gemini",
            "🎯 BGE-M3 Local Embedding": "bge_m3",
            "🚀 NAVER HCX Embedding": "hcx"
        }
        selected_display = st.selectbox(
            "사용할 임베딩 모델을 선택하세요:",
            list(embedding_options.keys()),
            key="embedding_selector"
        )
        return embedding_options[selected_display]


def show_prompt_selector():
    """프롬프트 선택기 (지연 로딩)"""
    try:
        from src.presentation.web.components.prompt_selector import show_prompt_selector as _show_prompt_selector
        return _show_prompt_selector()
    except ImportError:
        # 컴포넌트가 없으면 간단한 대체 UI
        st.markdown("### 🎯 프롬프트 타입 선택")
        prompt_options = [PromptType.DEFAULT, PromptType.KOREAN_FORMAL, PromptType.NUCLEAR_HYDRO_TECH]
        selected = st.selectbox("프롬프트 타입 선택", 
                               [p.value for p in prompt_options], 
                               key="prompt_selector")
        return next(p for p in prompt_options if p.value == selected)


def execute_evaluation(prompt_type: PromptType, dataset_name: str, llm_type: str, embedding_type: str):
    """평가 실행 로직"""
    with st.spinner("🔄 평가를 실행 중입니다..."):
        try:
            # 업로드된 파일을 사용하는 경우 특별 처리
            if st.session_state.get('use_uploaded_file', False) and st.session_state.get('uploaded_data'):
                # 업로드된 데이터를 임시 파일로 저장
                import tempfile
                import os
                from pathlib import Path
                
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_file:
                    json.dump(st.session_state.uploaded_data, tmp_file, ensure_ascii=False, indent=2)
                    temp_dataset_path = tmp_file.name
                
                # 임시 데이터셋 이름 설정
                actual_dataset_name = f"uploaded_{dataset_name}"
            else:
                temp_dataset_path = None
                actual_dataset_name = dataset_name
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

            # HCX 선택 시 API 키 확인 및 사용자 안내
            if llm_type == "hcx" or embedding_type == "hcx":
                from src.config import settings
                if not settings.CLOVA_STUDIO_API_KEY:
                    st.error("❌ HCX 모델을 사용하려면 .env 파일에 CLOVA_STUDIO_API_KEY를 설정해야 합니다.")
                    return
                else:
                    st.warning("⚠️ **HCX API 사용 시 주의사항**")
                    st.markdown("""
                    - HCX API는 요청 한도가 있어 429 오류가 발생할 수 있습니다
                    - 실패한 평가는 자동으로 재시도됩니다 (최대 3회)
                    - 대량 평가 시에는 Gemini 모델 사용을 권장합니다
                    """)
                    st.markdown("---")

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
                if llm_type == "hcx" or embedding_type == "hcx":
                    st.info("⚡ 평가 실행 중... (HCX API 사용으로 10-15분 소요 예상)")
                    st.warning("🔄 HCX API 429 오류 방지를 위해 순차 처리합니다. 중단하지 마시고 기다려주세요.")
                    st.info("📊 설정: 워커 1개, 재시도 8회, 지수 백오프 적용")
                else:
                    st.info("⚡ 평가 실행 중... (2-5분 소요 예상)")
                
                progress_bar = st.progress(0)
                progress_text = st.empty()
                
                # 평가 실행
                progress_text.text("평가 시작...")
                progress_bar.progress(25)
                
                # 업로드된 파일인 경우 경로 직접 전달
                if temp_dataset_path:
                    # 임시로 데이터를 data/ 디렉토리에 복사
                    from pathlib import Path
                    import shutil
                    
                    data_dir = Path("data")
                    data_dir.mkdir(exist_ok=True)
                    temp_data_file = data_dir / f"temp_{dataset_name}.json"
                    
                    shutil.copy(temp_dataset_path, temp_data_file)
                    
                    try:
                        evaluation_result = evaluation_use_case.execute(
                            dataset_name=f"temp_{dataset_name}"
                        )
                    finally:
                        # 평가 후 임시 파일 삭제
                        if temp_data_file.exists():
                            temp_data_file.unlink()
                        if temp_dataset_path and os.path.exists(temp_dataset_path):
                            os.unlink(temp_dataset_path)
                else:
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

            # 추가 정보 저장
            import uuid
            evaluation_id = str(uuid.uuid4())[:8]
            
            # LLM과 임베딩 모델 표시명 매핑
            llm_display_names = {
                "gemini": "Google Gemini 2.5 Flash",
                "hcx": "NAVER HyperCLOVA X"
            }
            
            embedding_display_names = {
                "gemini": "Google Gemini Embedding",
                "bge_m3": "BGE-M3 Local Embedding", 
                "hcx": "NAVER HCX Embedding"
            }
            
            result_dict["evaluation_id"] = evaluation_id
            result_dict["llm_model"] = llm_display_names.get(llm_type, llm_type)
            result_dict["embedding_model"] = embedding_display_names.get(embedding_type, embedding_type)
            result_dict["dataset_name"] = actual_dataset_name if 'actual_dataset_name' in locals() else dataset_name

            dataset_path = get_evaluation_data_path(dataset_name)
            if dataset_path:
                try:
                    from pathlib import Path
                    from src.infrastructure.data_import.importers import ExcelImporter, CSVImporter
                    
                    file_path_obj = Path(dataset_path)
                    file_extension = file_path_obj.suffix.lower()
                    
                    if file_extension in ['.xlsx', '.xls']:
                        # Excel 파일 처리
                        importer = ExcelImporter()
                        evaluation_data_list = importer.import_data(file_path_obj)
                        qa_data = [
                            {
                                "question": item.question,
                                "contexts": item.contexts,
                                "answer": item.answer,
                                "ground_truth": item.ground_truth
                            }
                            for item in evaluation_data_list
                        ]
                    elif file_extension == '.csv':
                        # CSV 파일 처리
                        importer = CSVImporter()
                        evaluation_data_list = importer.import_data(file_path_obj)
                        qa_data = [
                            {
                                "question": item.question,
                                "contexts": item.contexts,
                                "answer": item.answer,
                                "ground_truth": item.ground_truth
                            }
                            for item in evaluation_data_list
                        ]
                    else:
                        # JSON 파일 처리 (기본)
                        with open(dataset_path, encoding="utf-8") as f:
                            qa_data = json.load(f)
                    
                    qa_count = len(result_dict.get("individual_scores", []))
                    result_dict["qa_count"] = qa_count
                    result_dict["qa_data"] = qa_data[:qa_count]
                except Exception as e:
                    st.warning(f"QA 데이터 로드 실패: {e}")
                    result_dict["qa_count"] = len(result_dict.get("individual_scores", []))
            else:
                result_dict["qa_count"] = len(result_dict.get("individual_scores", []))

            save_evaluation_result(result_dict)

            st.success("✅ 평가가 완료되었습니다!")
            st.balloons()
            
            # 평가 결과 요약 표시
            st.markdown("### 📊 평가 결과")
            
            # API 실패 케이스 확인 및 안내
            individual_scores = result_dict.get("individual_scores", [])
            failed_count = 0
            total_count = len(individual_scores)
            
            for scores in individual_scores:
                # 0.2는 API 실패 시 부여하는 부분 점수
                if any(score == 0.2 for score in scores.values()):
                    failed_count += 1
            
            if failed_count > 0:
                st.warning(f"⚠️ **일부 평가 실패**: {total_count}개 중 {failed_count}개가 API 한도로 인해 부분 점수를 받았습니다.")
                st.info("💡 **개선 방법**: Gemini 모델 사용 또는 잠시 후 재평가를 권장합니다.")
            
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
            # 제목에 모델 정보 포함
            llm_model = row.get('llm_model', 'N/A')
            embedding_model = row.get('embedding_model', 'N/A')
            qa_count = row.get('qa_count', 'N/A')
            
            # 모델명이 길면 줄임
            if llm_model and len(str(llm_model)) > 20:
                llm_display = str(llm_model)[:20] + "..."
            else:
                llm_display = llm_model
                
            if embedding_model and len(str(embedding_model)) > 20:
                embedding_display = str(embedding_model)[:20] + "..."
            else:
                embedding_display = embedding_model
            
            with st.expander(
                f"평가 #{i+1} - {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} | QA: {qa_count}"
            ):
                # 평가 기본 정보
                st.markdown("**📋 평가 정보**")
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    st.markdown(f"**LLM 모델**: <span style='font-size: 14px;'>{llm_display}</span>", unsafe_allow_html=True)
                    st.markdown(f"**임베딩 모델**: <span style='font-size: 14px;'>{embedding_display}</span>", unsafe_allow_html=True)
                with info_col2:
                    st.markdown(f"**데이터셋**: <span style='font-size: 14px;'>{row.get('dataset_name', 'N/A')}</span>", unsafe_allow_html=True)
                    st.markdown(f"**평가 ID**: <span style='font-size: 14px;'>{str(row.get('evaluation_id', 'N/A'))[:8]}</span>", unsafe_allow_html=True)
                
                st.markdown("---")
                
                col1, col2, col3, col4 = st.columns([1.8, 1.8, 1.8, 1])

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

                with col4:
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
    ]
    
    # answer_correctness가 두 평가 모두에 있으면 추가
    if "answer_correctness" in eval1 and "answer_correctness" in eval2:
        metrics.append("answer_correctness")
    
    metrics.append("ragas_score")

    fig = go.Figure()

    # 안전한 값 변환
    def safe_get_values(eval_dict, metric_list):
        values = []
        for m in metric_list:
            v = eval_dict.get(m, 0)
            try:
                values.append(float(v) if v is not None else 0.0)
            except (ValueError, TypeError):
                values.append(0.0)
        return values
    
    eval1_values = safe_get_values(eval1, metrics)
    eval2_values = safe_get_values(eval2, metrics)

    fig.add_trace(
        go.Bar(
            name=f'평가 1 ({eval1["timestamp"]})',
            x=metrics,
            y=eval1_values,
            marker_color="lightblue",
        )
    )

    fig.add_trace(
        go.Bar(
            name=f'평가 2 ({eval2["timestamp"]})',
            x=metrics,
            y=eval2_values,
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
        
        **✔️ Answer Correctness**: 답변의 정확도
        - 생성된 답변이 정답(ground truth)과 얼마나 일치하는지 측정
        - Semantic similarity와 factual similarity를 종합적으로 평가
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

    # 기존 테이블 구조 확인
    cursor.execute("PRAGMA table_info(evaluations)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # 새로운 컬럼들이 없으면 추가
    new_columns = [
        'qa_count', 'evaluation_id', 'llm_model', 'embedding_model', 'dataset_name',
        'total_duration_seconds', 'total_duration_minutes', 'avg_time_per_item_seconds',
        'answer_correctness'
    ]
    
    for column in new_columns:
        if column not in columns:
            try:
                if column in ['qa_count', 'total_duration_seconds', 'total_duration_minutes', 'avg_time_per_item_seconds', 'answer_correctness']:
                    cursor.execute(f"ALTER TABLE evaluations ADD COLUMN {column} REAL")
                else:
                    cursor.execute(f"ALTER TABLE evaluations ADD COLUMN {column} TEXT")
                print(f"✅ 컬럼 '{column}' 추가됨")
            except Exception as e:
                print(f"⚠️ 컬럼 '{column}' 추가 실패: {e}")

    # 테이블이 없으면 생성
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            faithfulness REAL,
            answer_relevancy REAL,
            context_recall REAL,
            context_precision REAL,
            answer_correctness REAL,
            ragas_score REAL,
            raw_data TEXT,
            qa_count INTEGER,
            evaluation_id TEXT,
            llm_model TEXT,
            embedding_model TEXT,
            dataset_name TEXT,
            total_duration_seconds REAL,
            total_duration_minutes REAL,
            avg_time_per_item_seconds REAL
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

    # 메타데이터에서 시간 정보 추출
    metadata = result.get("metadata", {})
    
    cursor.execute(
        """
        INSERT INTO evaluations (
            timestamp, faithfulness, answer_relevancy, 
            context_recall, context_precision, answer_correctness, ragas_score, raw_data,
            qa_count, evaluation_id, llm_model, embedding_model, dataset_name,
            total_duration_seconds, total_duration_minutes, avg_time_per_item_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            datetime.now().isoformat(),
            result.get("faithfulness", 0),
            result.get("answer_relevancy", 0),
            result.get("context_recall", 0),
            result.get("context_precision", 0),
            result.get("answer_correctness", 0),
            result.get("ragas_score", 0),
            json.dumps(result),
            result.get("qa_count", 0),
            result.get("evaluation_id", ""),
            result.get("llm_model", ""),
            result.get("embedding_model", ""),
            result.get("dataset_name", ""),
            metadata.get("total_duration_seconds", 0.0),
            metadata.get("total_duration_minutes", 0.0),
            metadata.get("avg_time_per_item_seconds", 0.0),
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
    
    # 테이블 구조 확인
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(evaluations)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # answer_correctness 컬럼이 있는지 확인
    if 'answer_correctness' in columns:
        query = """
            SELECT timestamp, faithfulness, answer_relevancy, 
                   context_recall, context_precision, answer_correctness, ragas_score,
                   qa_count, evaluation_id, llm_model, embedding_model, dataset_name,
                   total_duration_seconds, total_duration_minutes, avg_time_per_item_seconds
            FROM evaluations 
            ORDER BY timestamp DESC
        """
    else:
        # answer_correctness 컬럼이 없는 경우 0으로 처리
        query = """
            SELECT timestamp, faithfulness, answer_relevancy, 
                   context_recall, context_precision, 0 as answer_correctness, ragas_score,
                   qa_count, evaluation_id, llm_model, embedding_model, dataset_name,
                   total_duration_seconds, total_duration_minutes, avg_time_per_item_seconds
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


if __name__ == "__main__":
    main()