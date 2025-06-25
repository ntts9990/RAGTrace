"""
상세 분석 컴포넌트 - 실제 평가 데이터 기반
실제로 평가된 QA 데이터만 표시하고 Historical 페이지와 연동
"""

import json
import sqlite3
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
import streamlit as st

from src.utils.paths import (
    DATABASE_PATH,
    get_available_datasets,
    get_evaluation_data_path,
)


def load_all_evaluations():
    """모든 평가 결과 로드 (Historical 페이지 연동용)"""
    try:
        # Use DATABASE_PATH from paths module
        if not DATABASE_PATH.exists():
            return []

        conn = sqlite3.connect(str(DATABASE_PATH))

        query = """
            SELECT id, timestamp, faithfulness, answer_relevancy, 
                   context_recall, context_precision, answer_correctness, ragas_score, raw_data
            FROM evaluations 
            ORDER BY timestamp DESC
        """

        cursor = conn.execute(query)
        results = cursor.fetchall()
        conn.close()

        evaluations = []
        for row in results:
            evaluation = {
                "id": row[0],
                "timestamp": row[1],
                "faithfulness": row[2],
                "answer_relevancy": row[3],
                "context_recall": row[4],
                "context_precision": row[5],
                "answer_correctness": row[6],
                "ragas_score": row[7],
                "raw_data": json.loads(row[8]) if row[8] else None,
            }
            evaluations.append(evaluation)

        return evaluations

    except Exception as e:
        st.error(f"평가 결과 로드 중 오류: {e}")
        return []


def load_evaluation_by_id(evaluation_id):
    """특정 평가 ID로 평가 결과 로드"""
    try:
        # Use DATABASE_PATH from paths module
        if not DATABASE_PATH.exists():
            return None, []

        conn = sqlite3.connect(str(DATABASE_PATH))

        query = """
            SELECT raw_data 
            FROM evaluations 
            WHERE id = ?
        """

        result = conn.execute(query, (evaluation_id,)).fetchone()
        conn.close()

        if result and result[0]:
            raw_data = json.loads(result[0])
            individual_scores = raw_data.get("individual_scores", [])
            return raw_data, individual_scores

        return None, []

    except Exception as e:
        st.error(f"평가 결과 로드 중 오류: {e}")
        return None, []


def load_actual_qa_data_from_dataset_simple(dataset_name, qa_count):
    """간단한 버전 - 직접 파일 로드"""
    try:
        # 하드코딩된 절대 경로 사용
        if "variant1" in dataset_name:
            file_path = get_evaluation_data_path("evaluation_data_variant1.json")
        else:
            file_path = get_evaluation_data_path("evaluation_data.json")

        if not file_path:
            st.error(f"데이터셋 '{dataset_name}'을 찾을 수 없습니다.")
            return None

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
            return data[:qa_count]
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None


def load_actual_qa_data_from_dataset(dataset_name, qa_count):
    """데이터셋 파일에서 실제 QA 데이터 로드 (개선된 버전)"""
    try:
        # 중앙 경로 관리 모듈 사용
        file_path = get_evaluation_data_path(dataset_name)

        if not file_path:
            st.error(f"데이터셋 '{dataset_name}'을 찾을 수 없습니다.")
            # 사용 가능한 데이터셋 목록 표시
            available_datasets = get_available_datasets()
            if available_datasets:
                st.info(f"사용 가능한 데이터셋: {', '.join(available_datasets)}")
            return None

        # 파일 로드 및 파싱
        with open(file_path, encoding="utf-8") as f:
            all_qa_data = json.load(f)

        if not isinstance(all_qa_data, list) or len(all_qa_data) == 0:
            st.error(
                f"데이터셋 '{dataset_name}'의 형식이 올바르지 않거나 비어있습니다."
            )
            return None

        # 요청된 개수만큼 반환
        result = all_qa_data[:qa_count]
        st.success(
            f"데이터셋 '{file_path.name}'에서 {len(result)}개의 QA 데이터를 로드했습니다."
        )
        return result

    except json.JSONDecodeError as e:
        st.error(f"JSON 파싱 오류: {e}")
        return None
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return None


def get_actual_qa_data_from_evaluation(raw_data, evaluation_db_id):
    """평가 결과에서 실제 사용된 QA 데이터 추출"""
    if not raw_data:
        return None

    # raw_data에서 실제 평가에 사용된 QA 데이터 찾기
    metadata = raw_data.get("metadata", {})

    # individual_scores의 개수가 실제 평가된 QA 개수
    individual_scores = raw_data.get("individual_scores", [])
    actual_qa_count = len(individual_scores)

    # 메타데이터에서 정보 추출, 없으면 DB ID 사용
    evaluation_id = metadata.get("evaluation_id", f"DB#{evaluation_db_id}")
    model_info = metadata.get("model", "Gemini-2.5-Flash")
    dataset_info = metadata.get("dataset", "evaluation_data.json")

    # 데이터셋에서 파일명만 추출
    if "/" in dataset_info:
        dataset_name = dataset_info.split("/")[-1]
    else:
        dataset_name = dataset_info

    # 실제 QA 데이터 로드 - 간단한 버전 사용
    actual_qa_data = load_actual_qa_data_from_dataset_simple(
        dataset_name, actual_qa_count
    )

    return {
        "qa_count": actual_qa_count,
        "dataset_size": metadata.get("dataset_size", actual_qa_count),
        "evaluation_id": evaluation_id,
        "timestamp": metadata.get("timestamp", "unknown"),
        "model": model_info,
        "dataset": dataset_name,
        "qa_data": actual_qa_data,
    }


def show_detailed_analysis():
    """상세 분석 메인 화면 - 실제 평가 데이터 기반"""
    st.header("🔍 상세 분석")

    # 평가 선택 섹션
    st.subheader("📋 평가 선택")

    # 모든 평가 결과 로드
    all_evaluations = load_all_evaluations()

    if not all_evaluations:
        st.error("❌ 평가 결과가 없습니다. 먼저 평가를 실행해주세요.")
        st.info("💡 Overview 페이지에서 '새 평가 실행' 버튼을 클릭하세요.")
        return

    # 평가 선택 옵션 생성
    evaluation_options = []
    for i, eval_data in enumerate(all_evaluations):
        timestamp = eval_data["timestamp"]
        qa_count = 0
        if eval_data["raw_data"] and eval_data["raw_data"].get("individual_scores"):
            qa_count = len(eval_data["raw_data"]["individual_scores"])

        # timestamp를 더 읽기 쉬운 형태로 변환
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp

        option_text = f"평가 #{eval_data['id']} - {formatted_time} ({qa_count}개 QA)"
        evaluation_options.append(option_text)

    # 세션 상태로 선택된 평가 관리
    if "selected_evaluation_index" not in st.session_state:
        st.session_state.selected_evaluation_index = 0

    selected_eval_idx = st.selectbox(
        "분석할 평가 선택",
        range(len(evaluation_options)),
        format_func=lambda x: evaluation_options[x],
        index=st.session_state.selected_evaluation_index,
        key="evaluation_selector",
    )

    # 선택된 평가 데이터 로드
    selected_evaluation = all_evaluations[selected_eval_idx]
    evaluation_id = selected_evaluation["id"]

    # 선택된 평가의 상세 데이터 로드
    raw_data, individual_scores = load_evaluation_by_id(evaluation_id)

    if not raw_data:
        st.error(f"❌ 평가 ID {evaluation_id}의 상세 데이터를 로드할 수 없습니다.")
        return

    # 실제 평가된 QA 데이터 정보
    qa_info = get_actual_qa_data_from_evaluation(raw_data, evaluation_id)

    if not qa_info or qa_info["qa_count"] == 0:
        st.error("❌ 이 평가에는 개별 QA 데이터가 없습니다.")
        return

    # 평가 정보 표시
    st.success(f"✅ 평가 #{evaluation_id} 로드 완료")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("QA 개수", qa_info["qa_count"])
    with col2:
        st.metric("평가 ID", qa_info["evaluation_id"])
    with col3:
        st.metric("모델", qa_info["model"])
    with col4:
        st.metric("데이터셋", qa_info["dataset"])
    with col5:
        ragas_score = selected_evaluation.get("ragas_score", 0)
        st.metric("RAGAS 점수", f"{ragas_score:.3f}")

    # 개별 점수가 있는 경우에만 분석 진행
    if not individual_scores:
        st.warning("⚠️ 이 평가에는 개별 QA 점수가 없습니다.")
        show_overall_metrics_only(selected_evaluation)
        return

    # 탭으로 구분 - 고급 분석 기능 추가
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 QA 개별 분석", 
        "📈 메트릭 분포", 
        "🎯 패턴 분석", 
        "📊 EDA 분석",
        "📈 시계열 분석", 
        "🚨 이상치 탐지",
        "🔍 고급 통계"
    ])

    with tab1:
        # 디버그: qa_info 상태 확인
        if qa_info and "qa_data" in qa_info:
            if qa_info["qa_data"]:
                st.info(f"📊 QA 데이터 상태: 로드됨 ({len(qa_info['qa_data'])}개)")
            else:
                st.warning("📊 QA 데이터 상태: 비어있음")
                # 터미널 출력 확인 안내
                st.info("💡 터미널에서 디버그 로그를 확인하세요.")
        show_qa_analysis_actual(
            individual_scores, evaluation_id, qa_info.get("qa_data")
        )

    with tab2:
        show_metric_distribution_actual(individual_scores, selected_evaluation)

    with tab3:
        show_pattern_analysis_actual(individual_scores, selected_evaluation)

    with tab4:
        show_eda_analysis(all_evaluations, selected_evaluation)

    with tab5:
        show_time_series_analysis(all_evaluations, selected_evaluation)

    with tab6:
        show_anomaly_detection(all_evaluations, selected_evaluation)

    with tab7:
        show_advanced_statistics(individual_scores, selected_evaluation, all_evaluations)


def show_overall_metrics_only(evaluation_data):
    """개별 점수가 없을 때 전체 메트릭만 표시"""
    st.subheader("📊 전체 평가 결과")

    metrics = [
        "faithfulness",
        "answer_relevancy",
        "context_recall",
        "context_precision",
    ]
    
    # answer_correctness가 있으면 추가
    if "answer_correctness" in evaluation_data:
        metrics.append("answer_correctness")
        cols = st.columns(5)
    else:
        cols = st.columns(4)

    for i, metric in enumerate(metrics):
        with cols[i]:
            score = evaluation_data.get(metric, 0)
            st.metric(label=metric.replace("_", " ").title(), value=f"{score:.3f}")


def show_qa_analysis_actual(individual_scores, evaluation_id, qa_data=None):
    """실제 평가된 QA 개별 분석"""
    st.subheader("📋 QA 개별 분석")

    qa_count = len(individual_scores)

    if qa_count == 0:
        st.warning("분석할 QA 데이터가 없습니다.")
        return

    # 디버그: qa_data 상태 확인
    if qa_data is None:
        st.error("⚠️ QA 데이터가 로드되지 않았습니다.")
        with st.expander("🔍 문제 해결 방법"):
            st.markdown(
                """
            **가능한 원인:**
            1. 평가 데이터 파일이 프로젝트의 `data/` 디렉토리에 없음
            2. 파일 이름이 `evaluation_data.json` 또는 `evaluation_data_variant1.json`이 아님
            3. 파일 권한 문제
            
            **해결 방법:**
            - 프로젝트 루트의 `data/` 디렉토리에서 파일 확인
            - 필요한 경우 파일 권한 수정
            - 로그를 확인하여 정확한 오류 위치 파악
            """
            )
    elif len(qa_data) == 0:
        st.error("⚠️ QA 데이터가 비어있습니다.")
    else:
        st.success(f"✅ {len(qa_data)}개의 QA 데이터가 로드되었습니다.")

    # QA 선택 옵션 생성 (실제 점수와 질문 내용 기반)
    qa_options = []
    for i, qa_score in enumerate(individual_scores):
        # 평균 점수 계산
        avg_score = 0
        if qa_score:
            avg_score = (
                sum(qa_score.values()) / len(qa_score) if qa_score.values() else 0
            )

        # 질문 내용 미리보기 추가
        question_preview = "질문 정보 없음"
        if qa_data and i < len(qa_data):
            question = qa_data[i].get("question", "")
            if question:
                # 질문 길이에 따라 동적으로 처리
                if len(question) > 50:
                    question_preview = question[:47] + "..."
                else:
                    question_preview = question

        qa_options.append(f"QA #{i+1}: {question_preview} (평균: {avg_score:.3f})")

    selected_qa_idx = st.selectbox(
        "분석할 QA 선택", range(len(qa_options)), format_func=lambda x: qa_options[x]
    )

    if selected_qa_idx is not None and selected_qa_idx < len(individual_scores):
        qa_scores = individual_scores[selected_qa_idx]
        qa_content = (
            qa_data[selected_qa_idx]
            if qa_data and selected_qa_idx < len(qa_data)
            else None
        )
        show_individual_qa_details_actual(
            selected_qa_idx + 1, qa_scores, evaluation_id, qa_content
        )


def show_individual_qa_details_actual(
    qa_number, qa_scores, evaluation_id, qa_content=None
):
    """실제 평가된 개별 QA 상세 정보 표시"""
    st.markdown(f"### 📝 QA {qa_number} 상세 분석 (평가 #{evaluation_id})")

    if not qa_scores:
        st.error("❌ 이 QA에 대한 점수 데이터가 없습니다.")
        return

    # QA 내용 표시 (실제 질문, 답변, 컨텍스트)
    if qa_content:
        st.markdown("#### 📋 QA 내용")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🤔 질문:**")
            st.info(qa_content.get("question", "질문 정보 없음"))

            st.markdown("**💡 생성된 답변:**")
            st.success(qa_content.get("answer", "답변 정보 없음"))

        with col2:
            st.markdown("**📚 제공된 컨텍스트:**")
            contexts = qa_content.get("contexts", [])
            for i, context in enumerate(contexts, 1):
                with st.expander(f"컨텍스트 {i}"):
                    st.text(context)

            st.markdown("**✅ 정답 (Ground Truth):**")
            st.info(qa_content.get("ground_truth", "정답 정보 없음"))

        st.markdown("---")

    # 점수 카드 표시
    st.markdown("#### 📊 평가 점수")

    metrics = [
        "faithfulness",
        "answer_relevancy",
        "context_recall",
        "context_precision",
    ]
    
    # answer_correctness가 qa_scores에 있으면 추가
    if "answer_correctness" in qa_scores:
        metrics.append("answer_correctness")
        score_cols = st.columns(5)
    else:
        score_cols = st.columns(4)

    for i, metric in enumerate(metrics):
        with score_cols[i]:
            score = qa_scores.get(metric, 0)
            color = "green" if score >= 0.8 else "orange" if score >= 0.6 else "red"
            st.metric(label=metric.replace("_", " ").title(), value=f"{score:.3f}")

    # 점수 시각화
    show_qa_score_chart_actual(qa_scores, qa_number)

    # 평가 근거 (점수 기반)
    show_evaluation_reasoning_actual(qa_number, qa_scores, qa_content)


def show_qa_score_chart_actual(scores, qa_number):
    """실제 평가된 QA 점수 차트"""
    st.markdown("#### 📈 점수 시각화")

    col1, col2 = st.columns(2)

    with col1:
        # 바 차트
        metrics = list(scores.keys())
        values = list(scores.values())

        fig = go.Figure(
            data=[
                go.Bar(
                    x=metrics,
                    y=values,
                    marker_color=[
                        "green" if v >= 0.8 else "orange" if v >= 0.6 else "red"
                        for v in values
                    ],
                    text=[f"{v:.3f}" for v in values],
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title=f"QA {qa_number} 메트릭 점수",
            yaxis_title="점수",
            yaxis=dict(range=[0, 1]),
            height=300,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # 레이더 차트
        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],  # 차트를 닫기 위해 첫 번째 값 추가
                theta=metrics + [metrics[0]],
                fill="toself",
                name=f"QA {qa_number}",
                line_color="rgb(32, 201, 151)",
            )
        )

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            title=f"QA {qa_number} 메트릭 균형도",
            height=300,
        )

        st.plotly_chart(fig, use_container_width=True)


def show_evaluation_reasoning_actual(qa_number, scores, qa_content=None):
    """실제 평가 점수 기반 평가 근거"""
    st.markdown("#### 🧠 평가 근거")

    # QA 내용 요약 표시 (평가 근거에서 참고용)
    if qa_content:
        st.info(
            f"**참고:** 이 분석은 '{qa_content.get('question', '')[:50]}...' 질문에 대한 평가입니다."
        )

    # 각 메트릭별 분석
    metrics_analysis = {
        "faithfulness": {
            "description": "답변이 제공된 컨텍스트에 얼마나 충실한지 측정",
            "score": scores.get("faithfulness", 0),
            "analysis": generate_faithfulness_analysis_actual(
                scores.get("faithfulness", 0)
            ),
        },
        "answer_relevancy": {
            "description": "답변이 질문과 얼마나 관련이 있는지 측정",
            "score": scores.get("answer_relevancy", 0),
            "analysis": generate_relevancy_analysis_actual(
                scores.get("answer_relevancy", 0)
            ),
        },
        "context_recall": {
            "description": "Ground truth의 정보가 컨텍스트에서 얼마나 발견되는지 측정",
            "score": scores.get("context_recall", 0),
            "analysis": generate_recall_analysis_actual(
                scores.get("context_recall", 0)
            ),
        },
        "context_precision": {
            "description": "검색된 컨텍스트가 질문과 얼마나 관련이 있는지 측정",
            "score": scores.get("context_precision", 0),
            "analysis": generate_precision_analysis_actual(
                scores.get("context_precision", 0)
            ),
        },
    }
    
    # answer_correctness가 있으면 추가
    if "answer_correctness" in scores:
        metrics_analysis["answer_correctness"] = {
            "description": "생성된 답변이 정답(ground truth)과 얼마나 일치하는지 측정",
            "score": scores.get("answer_correctness", 0),
            "analysis": generate_answer_correctness_analysis_actual(
                scores.get("answer_correctness", 0)
            ),
        }

    for metric, info in metrics_analysis.items():
        with st.expander(
            f"📝 {metric.replace('_', ' ').title()} 분석 (점수: {info['score']:.3f})"
        ):
            st.markdown(f"**설명:** {info['description']}")

            # 마크다운 렌더링을 위해 텍스트를 직접 표시
            analysis_lines = info["analysis"].split("\n")
            for line in analysis_lines:
                if line.strip():
                    st.markdown(line)

            # 점수 구간별 해석 가이드
            st.markdown("---")
            st.markdown("**점수 해석:**")
            if info["score"] >= 0.9:
                st.success("🌟 우수 (0.9+): 매우 높은 성능")
            elif info["score"] >= 0.8:
                st.success("✅ 양호 (0.8-0.9): 좋은 성능")
            elif info["score"] >= 0.6:
                st.warning("⚠️ 보통 (0.6-0.8): 개선 여지 있음")
            else:
                st.error("❌ 개선필요 (<0.6): 즉시 개선 필요")


def generate_faithfulness_analysis_actual(score):
    """Faithfulness 점수 기반 상세 분석"""
    base_analysis = ""
    improvement_tips = ""
    technical_details = ""

    if score >= 0.9:
        base_analysis = """
        **🌟 탁월한 충실도 (0.9+)**
        - 답변이 제공된 컨텍스트에 매우 충실하게 기반하고 있습니다
        - LLM이 환각(Hallucination) 없이 정확한 정보만을 활용했습니다
        - 컨텍스트에서 직접 추출 가능한 내용만으로 답변을 구성했습니다
        """
        improvement_tips = "✅ 현재 수준을 유지하세요. 이 정도 충실도는 프로덕션 환경에서 이상적입니다."
        technical_details = (
            "컨텍스트 내용과 답변 간 일치도가 90% 이상으로, 신뢰할 수 있는 답변입니다."
        )

    elif score >= 0.8:
        base_analysis = """
        **✅ 우수한 충실도 (0.8-0.9)**
        - 답변의 대부분이 컨텍스트에서 뒷받침됩니다
        - 소수의 추론이나 일반화가 포함되었을 수 있지만 적절한 수준입니다
        - 전반적으로 신뢰할 수 있는 답변을 제공했습니다
        """
        improvement_tips = """
        💡 **개선 방안:**
        - 프롬프트에 "제공된 정보만 사용하여" 같은 제약 조건 추가
        - 불확실한 내용에 대해 명시적으로 언급하도록 유도
        """
        technical_details = f"컨텍스트 일치도: {score:.1%}. 소수의 추론 포함되었지만 허용 범위 내입니다."

    elif score >= 0.6:
        base_analysis = """
        **⚠️ 보통 충실도 (0.6-0.8)**
        - 답변의 일부가 컨텍스트에서 직접 확인됩니다
        - 일부 내용은 컨텍스트를 넘어선 추론이나 외부 지식이 포함되었습니다
        - 검증이 필요한 내용이 포함되어 있을 가능성이 있습니다
        """
        improvement_tips = """
        🔧 **즉시 개선 필요:**
        - 프롬프트에 "오직 제공된 컨텍스트만 사용" 명시
        - Temperature 값을 낮춰 더 보수적인 답변 유도
        - 컨텍스트 외부 정보 사용 시 명시하도록 지시
        """
        technical_details = f"컨텍스트 일치도: {score:.1%}. 약 {(1-score)*100:.0f}%의 내용이 컨텍스트 외부 정보일 가능성이 있습니다."

    elif score >= 0.4:
        base_analysis = """
        **❌ 낮은 충실도 (0.4-0.6)**
        - 답변의 상당 부분이 컨텍스트에서 뒷받침되지 않습니다
        - 환각이나 외부 지식에 의존한 내용이 많이 포함되었습니다
        - 답변의 신뢰성에 심각한 문제가 있습니다
        """
        improvement_tips = """
        🚨 **긴급 수정 필요:**
        - 시스템 프롬프트 전면 재검토
        - "절대 컨텍스트 외부 정보 사용하지 마시오" 명시
        - RAG 파이프라인의 컨텍스트 품질 점검
        - 모델 파라미터 조정 (Top-p, Temperature 등)
        """
        technical_details = f"컨텍스트 일치도: {score:.1%}. 약 {(1-score)*100:.0f}%가 잠재적 환각 또는 외부 지식입니다."

    else:
        base_analysis = """
        **🔴 매우 낮은 충실도 (<0.4)**
        - 답변이 컨텍스트와 거의 관련이 없습니다
        - 심각한 환각 현상이 발생했습니다
        - 이 답변은 사용할 수 없는 수준입니다
        """
        improvement_tips = """
        🆘 **시스템 전면 점검 필요:**
        - RAG 시스템 전체 재설계 고려
        - 프롬프트 엔지니어링 근본적 재검토
        - 다른 모델 사용 검토
        - 컨텍스트 검색 알고리즘 완전 교체
        """
        technical_details = (
            f"컨텍스트 일치도: {score:.1%}. 시스템이 제대로 작동하지 않고 있습니다."
        )

    return f"{base_analysis}\n\n{improvement_tips}\n\n**📊 기술적 분석:** {technical_details}"


def generate_relevancy_analysis_actual(score):
    """Answer Relevancy 점수 기반 상세 분석"""
    base_analysis = ""
    improvement_tips = ""
    technical_details = ""

    if score >= 0.9:
        base_analysis = """
        **🎯 완벽한 관련성 (0.9+)**
        - 답변이 질문의 핵심 의도를 정확히 파악했습니다
        - 불필요한 정보 없이 직접적이고 명확하게 응답했습니다
        - 질문자가 원하는 정보를 완벽하게 제공했습니다
        """
        improvement_tips = "✅ 이상적인 답변입니다. 현재 접근 방식을 유지하세요."
        technical_details = f"질문-답변 관련성: {score:.1%}. 매우 높은 정확도입니다."

    elif score >= 0.8:
        base_analysis = """
        **✅ 높은 관련성 (0.8-0.9)**
        - 답변이 질문과 잘 연관되어 있습니다
        - 질문의 의도를 대체로 잘 이해했습니다
        - 소수의 부가 정보가 포함되었지만 유용한 수준입니다
        """
        improvement_tips = """
        💡 **미세 조정 방안:**
        - 답변을 더 간결하게 만들어 핵심 집중도 향상
        - 질문 키워드에 더 직접적으로 대응하는 답변 구조
        """
        technical_details = (
            f"질문-답변 관련성: {score:.1%}. 약간의 여분 정보가 포함되었습니다."
        )

    elif score >= 0.6:
        base_analysis = """
        **⚠️ 보통 관련성 (0.6-0.8)**
        - 답변이 질문과 관련이 있지만 완전하지 않습니다
        - 일부 불필요한 정보가 포함되었거나 핵심을 완전히 다루지 못했습니다
        - 질문 의도 파악에 개선의 여지가 있습니다
        """
        improvement_tips = """
        🔧 **개선 방안:**
        - 질문 분석 단계 강화 (키워드 추출, 의도 분류)
        - 답변 생성 전 질문 재확인 단계 추가
        - 불필요한 부연 설명 제거하고 핵심만 답변
        - "질문에 직접 답하시오" 프롬프트 추가
        """
        technical_details = f"질문-답변 관련성: {score:.1%}. 약 {(1-score)*100:.0f}%의 내용이 질문과 간접적 관련성을 가집니다."

    elif score >= 0.4:
        base_analysis = """
        **❌ 낮은 관련성 (0.4-0.6)**
        - 답변이 질문의 핵심을 놓쳤습니다
        - 질문과 다른 방향으로 답변했거나 너무 일반적입니다
        - 질문자의 실제 니즈를 제대로 파악하지 못했습니다
        """
        improvement_tips = """
        🚨 **즉시 개선 필요:**
        - 질문 이해 능력 향상 (Few-shot 예시 추가)
        - 답변 생성 전 질문 키워드 명시적 확인
        - 더 구체적이고 직접적인 답변 스타일로 변경
        - 질문 유형별 답변 템플릿 도입
        """
        technical_details = (
            f"질문-답변 관련성: {score:.1%}. 질문 의도 파악에 중대한 오류가 있습니다."
        )

    else:
        base_analysis = """
        **🔴 매우 낮은 관련성 (<0.4)**
        - 답변이 질문과 거의 관련이 없습니다
        - 완전히 다른 주제에 대해 답변했을 가능성이 높습니다
        - 질문 이해 시스템이 제대로 작동하지 않습니다
        """
        improvement_tips = """
        🆘 **시스템 재설계 필요:**
        - 질문 전처리 및 이해 모듈 완전 재구축
        - 프롬프트 엔지니어링 전면 재검토
        - 질문-컨텍스트 매칭 알고리즘 교체
        - 다른 모델 아키텍처 고려
        """
        technical_details = (
            f"질문-답변 관련성: {score:.1%}. 시스템이 질문을 이해하지 못하고 있습니다."
        )

    return f"{base_analysis}\n\n{improvement_tips}\n\n**📊 기술적 분석:** {technical_details}"


def generate_recall_analysis_actual(score):
    """Context Recall 점수 기반 상세 분석"""
    base_analysis = ""
    improvement_tips = ""
    technical_details = ""

    if score >= 0.9:
        base_analysis = """
        **🔍 탁월한 검색 완성도 (0.9+)**
        - Ground truth의 핵심 정보가 모두 검색된 컨텍스트에 포함되었습니다
        - 필요한 정보를 빠뜨리지 않고 완벽하게 수집했습니다
        - 검색 시스템이 매우 효과적으로 작동했습니다
        """
        improvement_tips = "✅ 완벽한 검색 성능입니다. 현재 검색 전략을 유지하세요."
        technical_details = (
            f"정보 검색 완성도: {score:.1%}. 필요한 정보가 모두 수집되었습니다."
        )

    elif score >= 0.8:
        base_analysis = """
        **✅ 우수한 검색 완성도 (0.8-0.9)**
        - Ground truth의 대부분 정보가 컨텍스트에서 발견됩니다
        - 주요 정보는 모두 포함되었고, 일부 세부사항만 누락되었을 수 있습니다
        - 전반적으로 효과적인 정보 검색이 이루어졌습니다
        """
        improvement_tips = """
        💡 **검색 향상 방안:**
        - 검색 쿼리 다양화 (동의어, 관련어 추가)
        - 검색 범위 소폭 확장
        - 하이브리드 검색 (키워드 + 의미적 검색) 도입
        """
        technical_details = (
            f"정보 검색 완성도: {score:.1%}. 대부분의 중요 정보가 수집되었습니다."
        )

    elif score >= 0.6:
        base_analysis = """
        **⚠️ 보통 검색 완성도 (0.6-0.8)**
        - Ground truth의 일부 정보만 컨텍스트에서 발견됩니다
        - 중요한 정보가 일부 누락되었을 가능성이 있습니다
        - 검색 전략의 개선이 필요합니다
        """
        improvement_tips = """
        🔧 **검색 개선 방안:**
        - 검색 키워드 확장 및 다각화
        - 검색 깊이 증가 (더 많은 문서 검색)
        - 다단계 검색 프로세스 도입
        - 검색 인덱스 재구축 고려
        - 의미적 검색 가중치 조정
        """
        technical_details = f"정보 검색 완성도: {score:.1%}. 약 {(1-score)*100:.0f}%의 관련 정보가 누락되었습니다."

    elif score >= 0.4:
        base_analysis = """
        **❌ 낮은 검색 완성도 (0.4-0.6)**
        - Ground truth의 상당 부분이 검색되지 않았습니다
        - 중요한 정보가 많이 누락되어 답변 품질에 영향을 줍니다
        - 검색 시스템의 근본적 개선이 필요합니다
        """
        improvement_tips = """
        🚨 **검색 시스템 재검토 필요:**
        - 검색 알고리즘 전면 재평가
        - 임베딩 모델 변경 고려
        - 문서 청킹 전략 재설계
        - 검색 인덱스 품질 점검
        - 다중 검색 전략 병행 사용
        """
        technical_details = f"정보 검색 완성도: {score:.1%}. 검색 시스템이 충분한 정보를 수집하지 못했습니다."

    else:
        base_analysis = """
        **🔴 매우 낮은 검색 완성도 (<0.4)**
        - Ground truth의 대부분이 검색 결과에 포함되지 않았습니다
        - 검색 시스템이 제대로 작동하지 않고 있습니다
        - 이 수준에서는 유용한 답변 생성이 불가능합니다
        """
        improvement_tips = """
        🆘 **검색 시스템 전면 재구축 필요:**
        - 검색 아키텍처 완전 재설계
        - 다른 검색 기술 스택 도입
        - 문서 전처리 과정 재검토
        - 검색 모델 교체
        - 전문가 컨설팅 고려
        """
        technical_details = (
            f"정보 검색 완성도: {score:.1%}. 검색 시스템 전체가 기능하지 않고 있습니다."
        )

    return f"{base_analysis}\n\n{improvement_tips}\n\n**📊 기술적 분석:** {technical_details}"


def generate_precision_analysis_actual(score):
    """Context Precision 점수 기반 상세 분석"""
    base_analysis = ""
    improvement_tips = ""
    technical_details = ""

    if score >= 0.9:
        base_analysis = """
        **🎯 탁월한 검색 정확도 (0.9+)**
        - 검색된 컨텍스트가 질문과 매우 정확하게 연관되어 있습니다
        - 불필요한 정보가 거의 없어 매우 효율적인 검색입니다
        - 노이즈 없는 고품질 컨텍스트가 제공되었습니다
        """
        improvement_tips = "✅ 완벽한 검색 정확도입니다. 현재 정확도를 유지하세요."
        technical_details = (
            f"검색 정확도: {score:.1%}. 거의 모든 컨텍스트가 관련성이 높습니다."
        )

    elif score >= 0.8:
        base_analysis = """
        **✅ 높은 검색 정확도 (0.8-0.9)**
        - 검색된 컨텍스트가 질문과 잘 관련되어 있습니다
        - 대부분의 정보가 유용하며 소수의 부가 정보만 포함되었습니다
        - 효율적인 검색이 이루어졌습니다
        """
        improvement_tips = """
        💡 **정확도 향상 방안:**
        - 검색 결과 리랭킹 알고리즘 개선
        - 컨텍스트 필터링 규칙 세밀화
        - 질문-문서 유사도 임계값 조정
        """
        technical_details = (
            f"검색 정확도: {score:.1%}. 소량의 부가 정보가 포함되었습니다."
        )

    elif score >= 0.6:
        base_analysis = """
        **⚠️ 보통 검색 정확도 (0.6-0.8)**
        - 컨텍스트가 부분적으로 관련성이 있습니다
        - 일부 불필요한 정보가 포함되어 효율성이 떨어집니다
        - 검색 필터링의 개선이 필요합니다
        """
        improvement_tips = """
        🔧 **정확도 개선 방안:**
        - 검색 결과 후처리 강화
        - 관련성 점수 임계값 상향 조정
        - 중복 제거 및 노이즈 필터링 개선
        - 쿼리-문서 매칭 알고리즘 정교화
        - 컨텍스트 품질 평가 메트릭 도입
        """
        technical_details = f"검색 정확도: {score:.1%}. 약 {(1-score)*100:.0f}%의 컨텍스트가 부분적 관련성을 가집니다."

    elif score >= 0.4:
        base_analysis = """
        **❌ 낮은 검색 정확도 (0.4-0.6)**
        - 검색된 컨텍스트에 무관한 정보가 상당히 많습니다
        - 노이즈가 많아 답변 품질에 부정적 영향을 줍니다
        - 검색 정확도 향상이 시급합니다
        """
        improvement_tips = """
        🚨 **검색 필터링 강화 필요:**
        - 검색 알고리즘 재설계
        - 더 엄격한 관련성 기준 적용
        - 다단계 필터링 프로세스 도입
        - 검색 결과 평가 모델 개선
        - 불용어 및 노이즈 제거 강화
        """
        technical_details = (
            f"검색 정확도: {score:.1%}. 상당량의 무관한 정보가 포함되었습니다."
        )

    else:
        base_analysis = """
        **🔴 매우 낮은 검색 정확도 (<0.4)**
        - 검색된 컨텍스트 대부분이 질문과 무관합니다
        - 검색 시스템이 질문을 제대로 이해하지 못했습니다
        - 이런 낮은 정확도로는 유용한 답변 생성이 불가능합니다
        """
        improvement_tips = """
        🆘 **검색 시스템 전면 재검토 필요:**
        - 검색 엔진 전체 교체 고려
        - 쿼리 이해 모듈 재구축
        - 문서 인덱싱 방식 근본적 변경
        - 검색 품질 평가 체계 재설계
        - 외부 검색 솔루션 도입 검토
        """
        technical_details = (
            f"검색 정확도: {score:.1%}. 검색 시스템이 올바르게 작동하지 않고 있습니다."
        )

    return f"{base_analysis}\n\n{improvement_tips}\n\n**📊 기술적 분석:** {technical_details}"


def generate_answer_correctness_analysis_actual(score):
    """Answer Correctness 점수 기반 상세 분석"""
    base_analysis = ""
    improvement_tips = ""
    technical_details = ""

    if score >= 0.9:
        base_analysis = """
        **🌟 완벽한 정확도 (0.9+)**
        - 생성된 답변이 정답(ground truth)과 거의 완벽하게 일치합니다
        - 의미적, 사실적 일치도가 모두 매우 높습니다
        - 사용자가 기대하는 답변을 정확히 제공했습니다
        """
        improvement_tips = "✅ 이상적인 정확도입니다. 현재 설정을 유지하세요."
        technical_details = f"정답 일치도: {score:.1%}. 매우 높은 정확성을 보입니다."

    elif score >= 0.8:
        base_analysis = """
        **✅ 높은 정확도 (0.8-0.9)**
        - 답변이 정답과 잘 일치합니다
        - 핵심 정보는 모두 포함되었고, 표현 방식에만 차이가 있을 수 있습니다
        - 전반적으로 만족스러운 답변 품질입니다
        """
        improvement_tips = """
        💡 **미세 조정 방안:**
        - 답변 형식을 정답과 더 유사하게 조정
        - 핵심 키워드 사용 빈도 개선
        - 문체나 톤 일치도 향상
        """
        technical_details = f"정답 일치도: {score:.1%}. 표현상 차이가 약간 있지만 내용은 정확합니다."

    elif score >= 0.6:
        base_analysis = """
        **⚠️ 보통 정확도 (0.6-0.8)**
        - 답변이 정답과 부분적으로 일치합니다
        - 주요 내용은 포함되었지만 일부 정보가 누락되거나 부정확할 수 있습니다
        - 답변 품질 개선이 필요합니다
        """
        improvement_tips = """
        🔧 **개선 방안:**
        - Ground truth와 유사한 답변 스타일 학습
        - 핵심 정보 누락 방지 체크리스트 작성
        - 답변 완성도 검증 단계 추가
        - Few-shot 예시에 정답과 유사한 형식 포함
        """
        technical_details = f"정답 일치도: {score:.1%}. 약 {(1-score)*100:.0f}%의 정보가 부정확하거나 누락되었습니다."

    elif score >= 0.4:
        base_analysis = """
        **❌ 낮은 정확도 (0.4-0.6)**
        - 답변이 정답과 상당한 차이를 보입니다
        - 중요한 정보가 많이 누락되었거나 잘못된 정보가 포함되었습니다
        - 답변의 신뢰성에 문제가 있습니다
        """
        improvement_tips = """
        🚨 **즉시 개선 필요:**
        - 답변 생성 프로세스 전반적 재검토
        - Ground truth 기반 훈련 데이터 보강
        - 답변 검증 시스템 도입
        - 정확성 우선의 보수적 답변 전략 채택
        - 모델 파라미터 조정 (Temperature 낮추기)
        """
        technical_details = f"정답 일치도: {score:.1%}. 답변 품질이 기대치에 미치지 못합니다."

    else:
        base_analysis = """
        **🔴 매우 낮은 정확도 (<0.4)**
        - 답변이 정답과 거의 일치하지 않습니다
        - 잘못된 정보가 대부분이거나 완전히 다른 내용입니다
        - 이런 수준의 답변은 사용할 수 없습니다
        """
        improvement_tips = """
        🆘 **시스템 전면 재검토 필요:**
        - RAG 시스템 전체 아키텍처 재설계
        - 다른 LLM 모델 사용 검토
        - 답변 생성 로직 근본적 변경
        - 정답 기반 supervised learning 도입
        - 전문가 리뷰 시스템 구축
        """
        technical_details = f"정답 일치도: {score:.1%}. 시스템이 올바른 답변을 생성하지 못하고 있습니다."

    return f"{base_analysis}\n\n{improvement_tips}\n\n**📊 기술적 분석:** {technical_details}"


def show_metric_distribution_actual(individual_scores, evaluation_data):
    """실제 평가된 데이터의 메트릭 분포"""
    st.subheader("📊 메트릭 분포 분석")

    if not individual_scores:
        st.warning("개별 점수 데이터가 없습니다.")
        return

    # DataFrame 생성
    metrics = [
        "faithfulness",
        "answer_relevancy",
        "context_recall",
        "context_precision",
    ]
    
    # answer_correctness가 포함된 점수가 있는지 확인
    has_answer_correctness = any("answer_correctness" in score for score in individual_scores)
    if has_answer_correctness:
        metrics.append("answer_correctness")
    
    data = {"QA": [f"Q{i+1}" for i in range(len(individual_scores))]}

    for metric in metrics:
        data[metric] = [score.get(metric, 0) for score in individual_scores]

    df = pd.DataFrame(data)

    # 히트맵
    st.markdown("#### 🔥 메트릭 히트맵")

    heatmap_data = df[metrics].values

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data,
            x=[m.replace("_", " ").title() for m in metrics],
            y=df["QA"],
            colorscale="RdYlGn",
            colorbar=dict(title="점수"),
        )
    )

    fig.update_layout(title="실제 평가된 QA별 메트릭 성능", height=400)

    st.plotly_chart(fig, use_container_width=True)

    # 분포 통계
    st.markdown("#### 📈 분포 통계")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**평균 점수**")
        for metric in metrics:
            avg_score = df[metric].mean()
            st.text(f"{metric.replace('_', ' ').title()}: {avg_score:.3f}")

    with col2:
        st.markdown("**표준편차**")
        for metric in metrics:
            std_score = df[metric].std()
            st.text(f"{metric.replace('_', ' ').title()}: {std_score:.3f}")


def show_pattern_analysis_actual(individual_scores, evaluation_data):
    """실제 평가 데이터의 패턴 분석"""
    st.subheader("🎯 성능 패턴 분석")

    qa_count = len(individual_scores)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📝 평가 개요")
        st.metric("실제 평가된 QA 개수", qa_count)

        # 평가 시간
        timestamp = evaluation_data.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                formatted_time = dt.strftime("%Y년 %m월 %d일 %H:%M")
                st.text(f"평가 시간: {formatted_time}")
            except:
                st.text(f"평가 시간: {timestamp}")

    with col2:
        st.markdown("#### 📊 성능 요약")
        ragas_score = evaluation_data.get("ragas_score", 0)
        st.metric("전체 RAGAS 점수", f"{ragas_score:.3f}")

        # 최고/최저 메트릭
        metrics = [
            "faithfulness",
            "answer_relevancy",
            "context_recall",
            "context_precision",
        ]
        
        # answer_correctness가 있으면 추가
        if "answer_correctness" in evaluation_data:
            metrics.append("answer_correctness")
        
        scores = {m: evaluation_data.get(m, 0) for m in metrics}

        if scores:
            best_metric = max(scores, key=scores.get)
            worst_metric = min(scores, key=scores.get)

            st.text(
                f"최고 성능: {best_metric.replace('_', ' ').title()} ({scores[best_metric]:.3f})"
            )
            st.text(
                f"개선 필요: {worst_metric.replace('_', ' ').title()} ({scores[worst_metric]:.3f})"
            )

    # 개선 제안
    st.markdown("#### 💡 이 평가에 대한 개선 제안")

    suggestions = []

    if evaluation_data.get("faithfulness", 0) < 0.7:
        suggestions.append(
            "🎯 Faithfulness 개선: 컨텍스트 충실도 강화, 환각 방지 프롬프트 사용"
        )

    if evaluation_data.get("answer_relevancy", 0) < 0.7:
        suggestions.append(
            "🎯 Answer Relevancy 개선: 질문 의도 파악 강화, 간결한 답변 생성"
        )

    if evaluation_data.get("context_recall", 0) < 0.7:
        suggestions.append(
            "🎯 Context Recall 개선: 검색 범위 확대, 다양한 검색 전략 활용"
        )

    if evaluation_data.get("context_precision", 0) < 0.7:
        suggestions.append(
            "🎯 Context Precision 개선: 무관한 컨텍스트 필터링, 검색 정확도 향상"
        )

    if not suggestions:
        suggestions.append(
            "✅ 모든 메트릭이 양호한 수준입니다! 현재 설정을 유지하세요."
        )

    for suggestion in suggestions:
        st.info(suggestion)


# Historical 페이지와의 연동을 위한 함수
def set_selected_evaluation(evaluation_id):
    """Historical 페이지에서 특정 평가를 선택했을 때 호출"""
    all_evaluations = load_all_evaluations()
    for i, eval_data in enumerate(all_evaluations):
        if eval_data["id"] == evaluation_id:
            st.session_state.selected_evaluation_index = i
            break


# =============================================================================
# 고급 분석 기능들
# =============================================================================

def show_eda_analysis(all_evaluations, selected_evaluation):
    """EDA (Exploratory Data Analysis) - 탐색적 데이터 분석"""
    st.header("📊 EDA (탐색적 데이터 분석)")
    
    if len(all_evaluations) < 2:
        st.warning("📊 EDA 분석을 위해서는 최소 2개 이상의 평가 결과가 필요합니다.")
        return
    
    # 데이터 준비
    df = pd.DataFrame(all_evaluations)
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision', 'answer_correctness']
    
    # 기본 통계 정보
    st.subheader("📈 기초 통계 요약")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 데이터셋 개요**")
        st.metric("총 평가 수", len(df))
        st.metric("평가 기간", f"{df['timestamp'].min()[:10]} ~ {df['timestamp'].max()[:10]}")
        
        # RAGAS 점수 분포
        ragas_scores = df['ragas_score'].dropna()
        if len(ragas_scores) > 0:
            st.metric("평균 RAGAS 점수", f"{ragas_scores.mean():.3f}")
            st.metric("RAGAS 점수 범위", f"{ragas_scores.min():.3f} ~ {ragas_scores.max():.3f}")
    
    with col2:
        st.write("**📋 기초 통계량**")
        stats_df = df[metrics].describe().round(3)
        st.dataframe(stats_df, use_container_width=True)
    
    # 메트릭 분포 시각화
    st.subheader("📊 메트릭 분포 시각화") 
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 히스토그램
        selected_metric = st.selectbox("히스토그램으로 볼 메트릭", metrics, key="eda_hist_metric")
        
        fig = px.histogram(
            df, 
            x=selected_metric, 
            nbins=20,
            title=f"{selected_metric} 분포",
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 박스플롯
        fig = go.Figure()
        
        for metric in metrics:
            fig.add_trace(go.Box(
                y=df[metric].dropna(),
                name=metric,
                boxpoints='outliers'
            ))
        
        fig.update_layout(
            title="메트릭별 박스플롯 (이상치 포함)",
            yaxis_title="점수",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 상관관계 분석
    st.subheader("🔗 메트릭 간 상관관계")
    
    # 상관관계 매트릭스
    correlation_matrix = df[metrics].corr()
    
    fig = px.imshow(
        correlation_matrix,
        text_auto=True,
        aspect="auto",
        color_continuous_scale='RdBu_r',
        title="메트릭 간 상관관계 히트맵"
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # 상관관계 해석
    st.write("**🔍 상관관계 해석:**")
    strong_correlations = []
    for i in range(len(metrics)):
        for j in range(i+1, len(metrics)):
            corr_val = correlation_matrix.iloc[i, j]
            if abs(corr_val) > 0.7:
                relationship = "강한 양의 상관관계" if corr_val > 0.7 else "강한 음의 상관관계"
                strong_correlations.append(f"• {metrics[i]} ↔ {metrics[j]}: {relationship} ({corr_val:.3f})")
    
    if strong_correlations:
        for corr in strong_correlations:
            st.info(corr)
    else:
        st.info("📊 강한 상관관계(|r| > 0.7)를 보이는 메트릭 쌍이 없습니다.")
    
    # 산점도 매트릭스
    st.subheader("📈 산점도 매트릭스")
    
    # 선택된 메트릭들로 산점도 매트릭스 생성
    selected_metrics = st.multiselect(
        "분석할 메트릭 선택 (2-4개 권장)", 
        metrics, 
        default=metrics[:3],
        key="eda_scatter_metrics"
    )
    
    if len(selected_metrics) >= 2:
        fig = px.scatter_matrix(
            df,
            dimensions=selected_metrics,
            title="선택된 메트릭들의 산점도 매트릭스",
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)


def show_time_series_analysis(all_evaluations, selected_evaluation):
    """시계열 분석 - 시간에 따른 성능 변화"""
    st.header("📈 시계열 분석")
    
    if len(all_evaluations) < 3:
        st.warning("📈 시계열 분석을 위해서는 최소 3개 이상의 평가 결과가 필요합니다.")
        return
    
    # 데이터 준비
    df = pd.DataFrame(all_evaluations)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision', 'answer_correctness', 'ragas_score']
    
    # 시계열 트렌드 분석
    st.subheader("📊 성능 트렌드")
    
    # 메트릭 선택
    selected_metrics = st.multiselect(
        "분석할 메트릭 선택", 
        metrics, 
        default=['ragas_score', 'faithfulness', 'answer_relevancy'],
        key="ts_metrics"
    )
    
    if selected_metrics:
        fig = go.Figure()
        
        for metric in selected_metrics:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[metric],
                mode='lines+markers',
                name=metric,
                line=dict(width=2),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title="시간에 따른 메트릭 변화",
            xaxis_title="시간",
            yaxis_title="점수",
            height=500,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 이동평균 분석
    st.subheader("📊 이동평균 분석")
    
    window_size = st.slider("이동평균 윈도우 크기", 2, min(10, len(df)-1), 3, key="ts_window")
    
    if len(selected_metrics) > 0:
        fig = go.Figure()
        
        for metric in selected_metrics:
            # 원본 데이터
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[metric],
                mode='markers',
                name=f'{metric} (원본)',
                opacity=0.5,
                marker=dict(size=6)
            ))
            
            # 이동평균
            moving_avg = df[metric].rolling(window=window_size, center=True).mean()
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=moving_avg,
                mode='lines',
                name=f'{metric} (이동평균)',
                line=dict(width=3)
            ))
        
        fig.update_layout(
            title=f"{window_size}-포인트 이동평균",
            xaxis_title="시간",
            yaxis_title="점수",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 변화율 분석
    st.subheader("📈 변화율 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 최근 개선/악화 추세**")
        
        for metric in metrics:
            if len(df[metric].dropna()) >= 2:
                recent_values = df[metric].dropna().tail(3)
                if len(recent_values) >= 2:
                    change = recent_values.iloc[-1] - recent_values.iloc[0]
                    change_pct = (change / recent_values.iloc[0]) * 100 if recent_values.iloc[0] != 0 else 0
                    
                    if abs(change_pct) > 5:  # 5% 이상 변화
                        emoji = "📈" if change > 0 else "📉"
                        st.metric(
                            metric, 
                            f"{recent_values.iloc[-1]:.3f}",
                            f"{change:+.3f} ({change_pct:+.1f}%)"
                        )
    
    with col2:
        # 변동성 분석
        st.write("**📊 변동성 분석 (표준편차)**")
        
        volatility_data = []
        for metric in metrics:
            std_val = df[metric].std()
            mean_val = df[metric].mean()
            cv = (std_val / mean_val) * 100 if mean_val != 0 else 0  # 변동계수
            volatility_data.append({
                'Metric': metric,
                'Standard Deviation': f"{std_val:.3f}",
                'Coefficient of Variation': f"{cv:.1f}%"
            })
        
        volatility_df = pd.DataFrame(volatility_data)
        st.dataframe(volatility_df, use_container_width=True, hide_index=True)
    
    # 주기성 분석
    if len(df) >= 7:
        st.subheader("🔄 주기성 분석")
        
        # 요일별 패턴 (시간 데이터가 있는 경우)
        df['weekday'] = df['timestamp'].dt.day_name()
        df['hour'] = df['timestamp'].dt.hour
        
        col1, col2 = st.columns(2)
        
        with col1:
            if len(df['weekday'].value_counts()) > 1:
                weekday_avg = df.groupby('weekday')['ragas_score'].mean().reset_index()
                
                fig = px.bar(
                    weekday_avg,
                    x='weekday',
                    y='ragas_score',
                    title="요일별 평균 RAGAS 점수"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if len(df['hour'].value_counts()) > 1:
                hour_avg = df.groupby('hour')['ragas_score'].mean().reset_index()
                
                fig = px.line(
                    hour_avg,
                    x='hour',
                    y='ragas_score',
                    title="시간대별 평균 RAGAS 점수"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)


def show_anomaly_detection(all_evaluations, selected_evaluation):
    """이상치 탐지 - 비정상적인 평가 결과 식별"""
    st.header("🚨 이상치 탐지")
    
    if len(all_evaluations) < 5:
        st.warning("🚨 이상치 탐지를 위해서는 최소 5개 이상의 평가 결과가 필요합니다.")
        return
    
    # 데이터 준비
    df = pd.DataFrame(all_evaluations)
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision', 'answer_correctness']
    
    # 이상치 탐지 방법 선택
    st.subheader("🔧 이상치 탐지 설정")
    
    detection_method = st.selectbox(
        "탐지 방법 선택",
        ["IQR (Interquartile Range)", "Z-Score", "Isolation Forest"],
        key="anomaly_method"
    )
    
    # 메트릭 선택
    selected_metrics = st.multiselect(
        "분석할 메트릭 선택",
        metrics,
        default=metrics,
        key="anomaly_metrics"
    )
    
    if not selected_metrics:
        st.warning("분석할 메트릭을 선택해주세요.")
        return
    
    # 이상치 탐지 실행
    anomalies = {}
    anomaly_scores = {}
    
    for metric in selected_metrics:
        metric_data = df[metric].dropna()
        
        if detection_method == "IQR (Interquartile Range)":
            Q1 = metric_data.quantile(0.25)
            Q3 = metric_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = metric_data[(metric_data < lower_bound) | (metric_data > upper_bound)]
            anomalies[metric] = outliers.index.tolist()
            
            # 이상치 점수 계산
            scores = []
            for val in metric_data:
                if val < lower_bound:
                    scores.append(abs(val - lower_bound) / IQR)
                elif val > upper_bound:
                    scores.append(abs(val - upper_bound) / IQR)
                else:
                    scores.append(0)
            anomaly_scores[metric] = scores
            
        elif detection_method == "Z-Score":
            z_threshold = st.slider(f"Z-Score 임계값", 1.5, 3.5, 2.5, 0.1, key=f"zscore_{metric}")
            
            z_scores = np.abs(stats.zscore(metric_data))
            outliers_mask = z_scores > z_threshold
            anomalies[metric] = metric_data[outliers_mask].index.tolist()
            anomaly_scores[metric] = z_scores.tolist()
            
        elif detection_method == "Isolation Forest":
            contamination = st.slider("오염도 (이상치 비율)", 0.05, 0.3, 0.1, 0.01, key=f"isolation_{metric}")
            
            isolation_forest = IsolationForest(contamination=contamination, random_state=42)
            outlier_labels = isolation_forest.fit_predict(metric_data.values.reshape(-1, 1))
            
            anomalies[metric] = [i for i, label in enumerate(outlier_labels) if label == -1]
            anomaly_scores[metric] = isolation_forest.decision_function(metric_data.values.reshape(-1, 1)).tolist()
    
    # 이상치 결과 표시
    st.subheader("📊 이상치 탐지 결과")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🚨 탐지된 이상치 개수**")
        for metric in selected_metrics:
            anomaly_count = len(anomalies[metric])
            total_count = len(df[metric].dropna())
            percentage = (anomaly_count / total_count) * 100 if total_count > 0 else 0
            
            st.metric(
                metric,
                f"{anomaly_count}개",
                f"{percentage:.1f}%"
            )
    
    with col2:
        # 이상치 점수 분포
        st.write("**📈 이상치 점수 분포**")
        
        selected_metric_viz = st.selectbox(
            "시각화할 메트릭",
            selected_metrics,
            key="anomaly_viz_metric"
        )
        
        if selected_metric_viz in anomaly_scores:
            scores = anomaly_scores[selected_metric_viz]
            fig = px.histogram(
                x=scores,
                nbins=20,
                title=f"{selected_metric_viz} 이상치 점수 분포"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    # 이상치 상세 분석
    st.subheader("🔍 이상치 상세 분석")
    
    # 전체 이상치 평가 목록
    all_anomaly_indices = set()
    for metric_anomalies in anomalies.values():
        all_anomaly_indices.update(metric_anomalies)
    
    if all_anomaly_indices:
        st.write(f"**🚨 총 {len(all_anomaly_indices)}개의 평가에서 이상치가 발견되었습니다:**")
        
        anomalous_evaluations = []
        for idx in sorted(all_anomaly_indices):
            if idx < len(df):
                eval_data = df.iloc[idx]
                anomalous_metrics = [metric for metric in selected_metrics if idx in anomalies[metric]]
                
                anomalous_evaluations.append({
                    'Evaluation ID': eval_data['id'],
                    'Timestamp': eval_data['timestamp'][:19] if eval_data['timestamp'] else 'N/A',
                    'RAGAS Score': f"{eval_data['ragas_score']:.3f}" if eval_data['ragas_score'] else 'N/A',
                    'Anomalous Metrics': ', '.join(anomalous_metrics)
                })
        
        anomaly_df = pd.DataFrame(anomalous_evaluations)
        st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
        
        # 이상치 시각화
        st.subheader("📊 이상치 시각화")
        
        # 시계열 이상치 표시
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df_sorted = df.sort_values('timestamp').reset_index(drop=True)
        
        fig = go.Figure()
        
        for metric in selected_metrics:
            # 정상 데이터
            normal_mask = ~df_sorted.index.isin(anomalies[metric])
            fig.add_trace(go.Scatter(
                x=df_sorted[normal_mask]['timestamp'],
                y=df_sorted[normal_mask][metric],
                mode='markers',
                name=f'{metric} (정상)',
                marker=dict(size=8),
                opacity=0.7
            ))
            
            # 이상치 데이터
            anomaly_mask = df_sorted.index.isin(anomalies[metric])
            if anomaly_mask.any():
                fig.add_trace(go.Scatter(
                    x=df_sorted[anomaly_mask]['timestamp'],
                    y=df_sorted[anomaly_mask][metric],
                    mode='markers',
                    name=f'{metric} (이상치)',
                    marker=dict(size=12, symbol='x', line=dict(width=2)),
                ))
        
        fig.update_layout(
            title="시간에 따른 이상치 분포",
            xaxis_title="시간",
            yaxis_title="점수",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.success("✅ 선택된 메트릭에서 이상치가 발견되지 않았습니다!")
    
    # 이상치 원인 분석 및 권장사항
    st.subheader("💡 이상치 원인 분석 및 권장사항")
    
    if all_anomaly_indices:
        st.write("**🔍 가능한 원인들:**")
        st.info("• **데이터 품질 문제**: 입력 데이터나 Ground Truth의 품질 이슈")
        st.info("• **모델 성능 변화**: LLM 모델이나 설정의 변경")
        st.info("• **평가 환경 변화**: 네트워크 상태, API 응답 시간 등")
        st.info("• **특이한 질문 유형**: 모델이 처리하기 어려운 특수한 질문")
        
        st.write("**🛠️ 권장 조치사항:**")
        st.info("• 이상치 평가 결과를 개별적으로 검토")
        st.info("• 해당 시점의 평가 환경이나 설정 변경사항 확인")
        st.info("• 반복적으로 이상치가 나타나는 패턴이 있는지 분석")
        st.info("• 필요시 해당 평가 결과를 제외하고 재분석")


def show_advanced_statistics(individual_scores, selected_evaluation, all_evaluations):
    """고급 통계 분석 - 심화 통계 분석 및 검정"""
    st.header("🔍 고급 통계 분석")
    
    if not individual_scores or len(all_evaluations) < 2:
        st.warning("🔍 고급 통계 분석을 위해서는 개별 점수 데이터와 여러 평가 결과가 필요합니다.")  
        return
    
    # 데이터 준비
    df_all = pd.DataFrame(all_evaluations)
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision', 'answer_correctness']
    
    # 현재 평가의 개별 점수
    current_scores = pd.DataFrame(individual_scores)
    
    # 1. 정규성 검정
    st.subheader("📊 정규성 검정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📈 Shapiro-Wilk 정규성 검정**")
        normality_results = []
        
        for metric in metrics:
            if metric in current_scores.columns:
                metric_data = current_scores[metric].dropna()
                if len(metric_data) >= 3:
                    statistic, p_value = stats.shapiro(metric_data)
                    is_normal = p_value > 0.05
                    
                    normality_results.append({
                        'Metric': metric,
                        'Statistic': f"{statistic:.4f}",
                        'P-Value': f"{p_value:.4f}",
                        'Normal': "✅ Yes" if is_normal else "❌ No"
                    })
        
        if normality_results:
            normality_df = pd.DataFrame(normality_results)
            st.dataframe(normality_df, use_container_width=True, hide_index=True)
        else:
            st.info("개별 점수 데이터가 부족합니다.")
    
    with col2:
        # Q-Q 플롯
        st.write("**📊 Q-Q 플롯 (정규성 시각화)**")
        
        selected_metric_qq = st.selectbox(
            "Q-Q 플롯을 볼 메트릭",
            [m for m in metrics if m in current_scores.columns],
            key="qq_metric"
        )
        
        if selected_metric_qq and selected_metric_qq in current_scores.columns:
            metric_data = current_scores[selected_metric_qq].dropna()
            if len(metric_data) >= 3:
                # Q-Q 플롯 생성
                theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(metric_data)))
                sample_quantiles = np.sort(metric_data)
                
                fig = go.Figure()
                
                # 실제 데이터 점들
                fig.add_trace(go.Scatter(
                    x=theoretical_quantiles,
                    y=sample_quantiles,
                    mode='markers',
                    name='실제 데이터',
                    marker=dict(size=8)
                ))
                
                # 이론적 직선
                fig.add_trace(go.Scatter(
                    x=theoretical_quantiles,
                    y=theoretical_quantiles * np.std(sample_quantiles) + np.mean(sample_quantiles),
                    mode='lines',
                    name='이론적 정규분포',
                    line=dict(color='red', dash='dash')
                ))
                
                fig.update_layout(
                    title=f"{selected_metric_qq} Q-Q 플롯",
                    xaxis_title="이론적 분위수",
                    yaxis_title="표본 분위수",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # 2. 신뢰구간 분석
    st.subheader("📊 신뢰구간 분석")
    
    confidence_level = st.slider("신뢰도 수준", 0.90, 0.99, 0.95, 0.01, key="confidence_level")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**📈 {confidence_level*100:.0f}% 신뢰구간**")
        
        ci_results = []
        for metric in metrics:
            if metric in current_scores.columns:
                metric_data = current_scores[metric].dropna()
                if len(metric_data) >= 2:
                    mean_val = np.mean(metric_data)
                    sem = stats.sem(metric_data)  # 표준오차
                    ci = stats.t.interval(confidence_level, df=len(metric_data)-1, loc=mean_val, scale=sem)
                    
                    ci_results.append({
                        'Metric': metric,
                        'Mean': f"{mean_val:.4f}",
                        'Lower CI': f"{ci[0]:.4f}",
                        'Upper CI': f"{ci[1]:.4f}",
                        'Width': f"{ci[1] - ci[0]:.4f}"
                    })
        
        if ci_results:
            ci_df = pd.DataFrame(ci_results)
            st.dataframe(ci_df, use_container_width=True, hide_index=True)
    
    with col2:
        # 신뢰구간 시각화
        if ci_results:
            metrics_names = [r['Metric'] for r in ci_results]
            means = [float(r['Mean']) for r in ci_results]
            lower_cis = [float(r['Lower CI']) for r in ci_results]
            upper_cis = [float(r['Upper CI']) for r in ci_results]
            
            fig = go.Figure()
            
            for i, metric in enumerate(metrics_names):
                fig.add_trace(go.Scatter(
                    x=[means[i]],
                    y=[metric],
                    error_x=dict(
                        type='data',
                        symmetric=False,
                        array=[upper_cis[i] - means[i]],
                        arrayminus=[means[i] - lower_cis[i]]
                    ),
                    mode='markers',
                    marker=dict(size=10),
                    name=metric
                ))
            
            fig.update_layout(
                title=f"{confidence_level*100:.0f}% 신뢰구간 시각화",
                xaxis_title="점수",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 3. 가설 검정
    if len(all_evaluations) >= 2:
        st.subheader("🧪 가설 검정")
        
        # 현재 평가 vs 과거 평가들 비교
        st.write("**📊 현재 평가 vs 과거 평가 성능 비교**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # t-검정
            st.write("**📈 독립표본 t-검정**")
            
            ttest_results = []
            for metric in metrics:
                if metric in current_scores.columns:
                    current_data = current_scores[metric].dropna()
                    historical_data = df_all[df_all['id'] != selected_evaluation['id']][metric].dropna()
                    
                    if len(current_data) >= 2 and len(historical_data) >= 2:
                        # 등분산 검정
                        levene_stat, levene_p = stats.levene(current_data, historical_data)
                        equal_var = levene_p > 0.05
                        
                        # t-검정
                        t_stat, p_value = stats.ttest_ind(current_data, historical_data, equal_var=equal_var)
                        
                        significance = "유의함" if p_value < 0.05 else "유의하지 않음"
                        direction = "향상" if np.mean(current_data) > np.mean(historical_data) else "하락"
                        
                        ttest_results.append({
                            'Metric': metric,
                            'T-Statistic': f"{t_stat:.4f}",
                            'P-Value': f"{p_value:.4f}",
                            'Result': f"{direction} ({significance})"
                        })
            
            if ttest_results:
                ttest_df = pd.DataFrame(ttest_results)
                st.dataframe(ttest_df, use_container_width=True, hide_index=True)
        
        with col2:
            # 효과 크기 (Cohen's d)
            st.write("**📊 효과 크기 (Cohen's d)**")
            
            effect_size_results = []
            for metric in metrics:
                if metric in current_scores.columns:
                    current_data = current_scores[metric].dropna()
                    historical_data = df_all[df_all['id'] != selected_evaluation['id']][metric].dropna()
                    
                    if len(current_data) >= 2 and len(historical_data) >= 2:
                        # Cohen's d 계산
                        pooled_std = np.sqrt(((len(current_data) - 1) * np.var(current_data, ddof=1) +
                                            (len(historical_data) - 1) * np.var(historical_data, ddof=1)) /
                                           (len(current_data) + len(historical_data) - 2))
                        
                        cohens_d = (np.mean(current_data) - np.mean(historical_data)) / pooled_std
                        
                        # 효과 크기 해석
                        if abs(cohens_d) < 0.2:
                            interpretation = "작은 효과"
                        elif abs(cohens_d) < 0.5:
                            interpretation = "중간 효과"
                        elif abs(cohens_d) < 0.8:
                            interpretation = "큰 효과"
                        else:
                            interpretation = "매우 큰 효과"
                        
                        effect_size_results.append({
                            'Metric': metric,
                            "Cohen's d": f"{cohens_d:.4f}",
                            'Interpretation': interpretation
                        })
            
            if effect_size_results:
                effect_df = pd.DataFrame(effect_size_results)
                st.dataframe(effect_df, use_container_width=True, hide_index=True)
    
    # 4. 분포 분석
    st.subheader("📊 고급 분포 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 왜도와 첨도
        st.write("**📈 왜도(Skewness)와 첨도(Kurtosis)**")
        
        distribution_results = []
        for metric in metrics:
            if metric in current_scores.columns:
                metric_data = current_scores[metric].dropna()
                if len(metric_data) >= 3:
                    skewness = stats.skew(metric_data)
                    kurtosis = stats.kurtosis(metric_data)
                    
                    # 해석
                    skew_interpretation = "좌편향" if skewness < -0.5 else "우편향" if skewness > 0.5 else "대칭적"
                    kurt_interpretation = "뾰족함" if kurtosis > 0.5 else "평평함" if kurtosis < -0.5 else "정상"
                    
                    distribution_results.append({
                        'Metric': metric,
                        'Skewness': f"{skewness:.4f}",
                        'Skew Type': skew_interpretation,
                        'Kurtosis': f"{kurtosis:.4f}",
                        'Kurt Type': kurt_interpretation
                    })
        
        if distribution_results:
            dist_df = pd.DataFrame(distribution_results)
            st.dataframe(dist_df, use_container_width=True, hide_index=True)
    
    with col2:
        # 분포 적합도 검정
        st.write("**🧪 분포 적합도 검정**")
        
        selected_metric_dist = st.selectbox(
            "검정할 메트릭",
            [m for m in metrics if m in current_scores.columns],
            key="dist_test_metric"
        )
        
        if selected_metric_dist and selected_metric_dist in current_scores.columns:
            metric_data = current_scores[selected_metric_dist].dropna()
            
            if len(metric_data) >= 8:  # KS 검정을 위한 최소 샘플 수
                # Kolmogorov-Smirnov 검정 (정규분포)
                ks_stat, ks_p = stats.kstest(
                    (metric_data - np.mean(metric_data)) / np.std(metric_data),
                    'norm'
                )
                
                # Anderson-Darling 검정 (정규분포)
                ad_stat, ad_critical, ad_significance = stats.anderson(metric_data, dist='norm')
                
                st.write(f"**K-S 검정 (정규분포):**")
                st.write(f"• 통계량: {ks_stat:.4f}")
                st.write(f"• p-값: {ks_p:.4f}")
                st.write(f"• 결과: {'정규분포를 따름' if ks_p > 0.05 else '정규분포를 따르지 않음'}")
                
                st.write(f"**Anderson-Darling 검정:**")
                st.write(f"• 통계량: {ad_stat:.4f}")
                st.write(f"• 5% 임계값: {ad_critical[2]:.4f}")
                st.write(f"• 결과: {'정규분포를 따름' if ad_stat < ad_critical[2] else '정규분포를 따르지 않음'}")
    
    # 5. 요약 및 권장사항
    st.subheader("💡 통계 분석 요약 및 권장사항")
    
    summary_points = []
    
    # 데이터 품질 평가
    if ci_results:
        avg_ci_width = np.mean([float(r['Width']) for r in ci_results])
        if avg_ci_width < 0.1:
            summary_points.append("✅ **높은 정밀도**: 신뢰구간이 좁아 추정이 정확합니다.")
        elif avg_ci_width > 0.3:
            summary_points.append("⚠️ **낮은 정밀도**: 신뢰구간이 넓어 더 많은 데이터가 필요합니다.")
        else:
            summary_points.append("📊 **적정 정밀도**: 현재 데이터 양이 적절한 수준입니다.")
    
    # 정규성 검정 결과 요약
    if normality_results:
        normal_count = sum(1 for r in normality_results if "Yes" in r['Normal'])
        if normal_count >= len(normality_results) * 0.8:
            summary_points.append("✅ **정규분포 가정 만족**: 대부분의 메트릭이 정규분포를 따릅니다.")
        else:
            summary_points.append("⚠️ **비정규분포**: 비모수 통계 방법 사용을 고려하세요.")
    
    # 성능 비교 결과
    if ttest_results:
        significant_improvements = sum(1 for r in ttest_results if "향상" in r['Result'] and "유의함" in r['Result'])
        if significant_improvements > 0:
            summary_points.append(f"📈 **성능 향상 감지**: {significant_improvements}개 메트릭에서 유의한 향상이 있습니다.")
        else:
            summary_points.append("📊 **성능 안정성**: 현재 성능이 과거와 유사한 수준을 유지하고 있습니다.")
    
    for point in summary_points:
        st.info(point)
    
    if not summary_points:
        st.info("📊 통계 분석을 위해 더 많은 데이터가 필요합니다. 추가 평가를 실행해주세요.")
