"""
상세 분석 컴포넌트 - 완전 재작성
개별 QA 쌍의 상세 평가 결과 분석
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import sqlite3
from pathlib import Path
import os


def get_project_root():
    """프로젝트 루트 경로 반환"""
    # 현재 파일에서 프로젝트 루트까지의 경로 계산
    current_file = Path(__file__).resolve()
    # src/presentation/web/components/detailed_analysis_new.py에서 프로젝트 루트로
    project_root = current_file.parent.parent.parent.parent
    return project_root


def load_evaluation_data():
    """평가용 데이터 로드 - 경로 문제 해결"""
    project_root = get_project_root()
    
    # 여러 경로 시도
    possible_paths = [
        project_root / "data" / "evaluation_data.json",
        project_root / "data" / "evaluation_data_variant1.json",
        Path.cwd() / "data" / "evaluation_data.json",
        Path.cwd() / "data" / "evaluation_data_variant1.json"
    ]
    
    for path in possible_paths:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                st.success(f"✅ 데이터 로드 성공: {path.name}")
                return data
            except Exception as e:
                st.error(f"데이터 파일 읽기 오류 ({path.name}): {e}")
                continue
    
    # 모든 경로 실패시 디버그 정보
    st.error("❌ 평가 데이터를 찾을 수 없습니다.")
    st.info("확인된 경로:")
    for i, path in enumerate(possible_paths, 1):
        exists = "✅" if path.exists() else "❌"
        st.text(f"{i}. {exists} {path}")
    
    return None


def get_db_path():
    """데이터베이스 경로 반환"""
    return Path(__file__).parent.parent / "evaluations.db"


def load_latest_evaluation_results():
    """최신 평가 결과와 개별 QA 점수 로드"""
    try:
        db_path = get_db_path()
        if not db_path.exists():
            st.warning("📊 평가 결과 데이터베이스가 없습니다.")
            return None, []
        
        conn = sqlite3.connect(str(db_path))
        
        # 최신 평가 결과 가져오기
        query = '''
            SELECT raw_data 
            FROM evaluations 
            ORDER BY timestamp DESC 
            LIMIT 1
        '''
        
        result = conn.execute(query).fetchone()
        conn.close()
        
        if result and result[0]:
            raw_data = json.loads(result[0])
            individual_scores = raw_data.get('individual_scores', [])
            st.success(f"✅ 평가 결과 로드 성공: {len(individual_scores)}개 QA 점수")
            return raw_data, individual_scores
        
        st.warning("📊 평가 결과가 비어있습니다.")
        return None, []
        
    except Exception as e:
        st.error(f"평가 결과 로드 중 오류: {e}")
        return None, []


def show_detailed_analysis():
    """상세 분석 메인 화면 - 전면 재작성"""
    st.header("🔍 상세 분석")
    
    # 데이터 로드 상태 확인
    st.subheader("📊 데이터 로드 상태")
    
    with st.expander("데이터 로드 진단", expanded=False):
        # 1. 평가 데이터 로드 테스트
        st.markdown("#### 1. 평가 데이터 파일 확인")
        evaluation_data = load_evaluation_data()
        
        if evaluation_data:
            st.success(f"✅ 평가 데이터 로드 성공: {len(evaluation_data)}개 QA 쌍")
        else:
            st.error("❌ 평가 데이터 로드 실패")
            return
        
        # 2. 평가 결과 로드 테스트
        st.markdown("#### 2. 평가 결과 데이터베이스 확인")
        latest_results, individual_scores = load_latest_evaluation_results()
        
        if latest_results:
            st.success(f"✅ 평가 결과 로드 성공")
            st.json({
                "전체 메트릭": {k: v for k, v in latest_results.items() if k in ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision', 'ragas_score']},
                "개별 점수 개수": len(individual_scores)
            })
        else:
            st.error("❌ 평가 결과 로드 실패")
    
    # 실제 데이터가 모두 로드된 경우에만 분석 진행
    if not evaluation_data:
        st.error("❌ 평가 데이터가 없습니다. 먼저 evaluation_data.json 파일을 확인해주세요.")
        return
    
    if not latest_results:
        st.error("❌ 평가 결과가 없습니다. 먼저 평가를 실행해주세요.")
        st.info("💡 Overview 페이지에서 '새 평가 실행' 버튼을 클릭하세요.")
        return
    
    # 성공적으로 데이터가 로드된 경우 분석 시작
    st.success("🎉 모든 데이터가 성공적으로 로드되었습니다!")
    
    # 탭으로 구분
    tab1, tab2, tab3 = st.tabs(["📊 QA 개별 분석", "📈 메트릭 분포", "🎯 패턴 분석"])
    
    with tab1:
        show_qa_analysis_new(evaluation_data, individual_scores)
    
    with tab2:
        show_metric_distribution_new(evaluation_data, latest_results, individual_scores)
    
    with tab3:
        show_pattern_analysis_new(evaluation_data, latest_results, individual_scores)


def show_qa_analysis_new(evaluation_data, individual_scores):
    """개별 QA 분석 - 재작성"""
    st.subheader("📋 질문-답변 쌍별 상세 분석")
    
    # QA 쌍 선택
    qa_count = len(evaluation_data)
    st.info(f"📊 총 {qa_count}개의 QA 쌍이 있습니다.")
    
    qa_options = []
    for i, qa in enumerate(evaluation_data):
        question_preview = qa['question'][:50] + "..." if len(qa['question']) > 50 else qa['question']
        qa_options.append(f"Q{i+1}: {question_preview}")
    
    selected_qa_idx = st.selectbox(
        "분석할 QA 선택", 
        range(len(qa_options)), 
        format_func=lambda x: qa_options[x]
    )
    
    if selected_qa_idx is not None:
        qa_data = evaluation_data[selected_qa_idx]
        
        # 해당 QA의 개별 점수 가져오기 (안전하게)
        qa_scores = None
        if individual_scores and selected_qa_idx < len(individual_scores):
            qa_scores = individual_scores[selected_qa_idx]
        
        show_individual_qa_details_new(qa_data, selected_qa_idx + 1, qa_scores)


def show_individual_qa_details_new(qa_data, qa_number, qa_scores=None):
    """개별 QA 상세 정보 표시 - 재작성"""
    st.markdown(f"### 📝 QA {qa_number} 상세 분석")
    
    # 기본 정보 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🤔 질문")
        st.info(qa_data['question'])
        
        st.markdown("#### 💡 생성된 답변")
        st.success(qa_data['answer'])
    
    with col2:
        st.markdown("#### 📚 제공된 컨텍스트")
        for i, context in enumerate(qa_data['contexts'], 1):
            with st.expander(f"컨텍스트 {i}"):
                st.text(context)
        
        st.markdown("#### ✅ 정답 (Ground Truth)")
        st.info(qa_data['ground_truth'])
    
    # 평가 점수 표시
    st.markdown("#### 📊 이 QA의 평가 점수")
    
    if qa_scores:
        # 실제 평가 결과 사용
        scores = qa_scores
        st.success("✅ 개별 평가 점수 사용")
    else:
        # 평가 결과가 없을 때 전체 평균 사용
        st.warning("⚠️ 개별 평가 점수가 없어 전체 평균 점수를 표시합니다.")
        latest_results, _ = load_latest_evaluation_results()
        if latest_results:
            scores = {
                'faithfulness': latest_results.get('faithfulness', 0),
                'answer_relevancy': latest_results.get('answer_relevancy', 0),
                'context_recall': latest_results.get('context_recall', 0),
                'context_precision': latest_results.get('context_precision', 0)
            }
        else:
            st.error("❌ 평가 결과를 찾을 수 없습니다.")
            return
    
    # 점수 카드 표시
    if scores:
        score_cols = st.columns(4)
        metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
        
        for i, metric in enumerate(metrics):
            with score_cols[i]:
                score = scores.get(metric, 0)
                color = "green" if score >= 0.8 else "orange" if score >= 0.6 else "red"
                st.metric(
                    label=metric.replace('_', ' ').title(),
                    value=f"{score:.3f}"
                )
        
        # 점수 시각화
        show_qa_score_chart_new(scores, qa_number)
        
        # 평가 근거
        show_evaluation_reasoning_new(qa_data, qa_number, scores)


def show_qa_score_chart_new(scores, qa_number):
    """개별 QA 점수 차트 - 재작성"""
    st.markdown("#### 📈 점수 시각화")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 바 차트
        metrics = list(scores.keys())
        values = list(scores.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=metrics, 
                y=values, 
                marker_color=['green' if v >= 0.8 else 'orange' if v >= 0.6 else 'red' for v in values],
                text=[f"{v:.3f}" for v in values],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title=f"QA {qa_number} 메트릭 점수",
            yaxis_title="점수",
            yaxis=dict(range=[0, 1]),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 레이더 차트
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],  # 차트를 닫기 위해 첫 번째 값 추가
            theta=metrics + [metrics[0]],
            fill='toself',
            name=f'QA {qa_number}',
            line_color='rgb(32, 201, 151)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title=f"QA {qa_number} 메트릭 균형도",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)


def show_evaluation_reasoning_new(qa_data, qa_number, scores):
    """평가 근거 표시 - 재작성"""
    st.markdown("#### 🧠 평가 근거")
    
    # 실제 텍스트 데이터
    question = qa_data['question']
    answer = qa_data['answer']
    contexts = qa_data['contexts']
    ground_truth = qa_data['ground_truth']
    
    # 각 메트릭별 분석
    metrics_analysis = {
        'faithfulness': {
            'description': '답변이 제공된 컨텍스트에 얼마나 충실한지 측정',
            'score': scores.get('faithfulness', 0),
            'analysis': generate_faithfulness_analysis(answer, contexts, scores.get('faithfulness', 0))
        },
        'answer_relevancy': {
            'description': '답변이 질문과 얼마나 관련이 있는지 측정',
            'score': scores.get('answer_relevancy', 0),
            'analysis': generate_relevancy_analysis(question, answer, scores.get('answer_relevancy', 0))
        },
        'context_recall': {
            'description': 'Ground truth의 정보가 컨텍스트에서 얼마나 발견되는지 측정',
            'score': scores.get('context_recall', 0),
            'analysis': generate_recall_analysis(ground_truth, contexts, scores.get('context_recall', 0))
        },
        'context_precision': {
            'description': '검색된 컨텍스트가 질문과 얼마나 관련이 있는지 측정',
            'score': scores.get('context_precision', 0),
            'analysis': generate_precision_analysis(question, contexts, scores.get('context_precision', 0))
        }
    }
    
    for metric, info in metrics_analysis.items():
        with st.expander(f"📝 {metric.replace('_', ' ').title()} 분석 (점수: {info['score']:.3f})"):
            st.markdown(f"**설명:** {info['description']}")
            st.markdown(f"**분석:** {info['analysis']}")


def generate_faithfulness_analysis(answer, contexts, score):
    """Faithfulness 분석 생성"""
    context_text = " ".join(contexts)
    if score >= 0.8:
        return f"답변이 컨텍스트에 잘 기반하고 있습니다. 컨텍스트에서 확인할 수 있는 정보를 중심으로 답변이 구성되었습니다."
    elif score >= 0.5:
        return f"답변의 일부가 컨텍스트에서 확인됩니다. 일부 내용은 컨텍스트에서 직접적으로 뒷받침되지 않을 수 있습니다."
    else:
        return f"답변이 컨텍스트에서 충분히 뒷받침되지 않습니다. 컨텍스트에 없는 정보가 포함되었을 가능성이 높습니다."


def generate_relevancy_analysis(question, answer, score):
    """Answer Relevancy 분석 생성"""
    if score >= 0.8:
        return f"답변이 질문의 핵심 의도를 잘 파악하고 적절하게 응답했습니다."
    elif score >= 0.5:
        return f"답변이 질문과 관련이 있지만, 일부 불필요한 정보가 포함되었거나 핵심을 완전히 다루지 못했을 수 있습니다."
    else:
        return f"답변이 질문의 의도와 맞지 않거나 관련성이 낮습니다. 질문을 다시 분석하여 더 직접적인 답변이 필요합니다."


def generate_recall_analysis(ground_truth, contexts, score):
    """Context Recall 분석 생성"""
    if score >= 0.8:
        return f"Ground truth의 핵심 정보가 제공된 컨텍스트에서 잘 발견됩니다. 필요한 정보 검색이 충분히 이루어졌습니다."
    elif score >= 0.5:
        return f"Ground truth의 일부 정보만 컨텍스트에서 발견됩니다. 추가적인 관련 정보 검색이 필요할 수 있습니다."
    else:
        return f"Ground truth의 중요한 정보가 컨텍스트에서 누락되었습니다. 검색 범위나 전략을 개선해야 합니다."


def generate_precision_analysis(question, contexts, score):
    """Context Precision 분석 생성"""
    if score >= 0.8:
        return f"검색된 컨텍스트가 질문과 매우 관련성이 높습니다. 불필요한 정보가 적고 효율적인 검색이 이루어졌습니다."
    elif score >= 0.5:
        return f"컨텍스트가 부분적으로 관련성이 있지만, 일부 불필요한 정보가 포함되었을 수 있습니다."
    else:
        return f"검색된 컨텍스트에 질문과 관련 없는 정보가 많이 포함되었습니다. 더 정확한 검색이 필요합니다."


def show_metric_distribution_new(evaluation_data, latest_results, individual_scores):
    """메트릭 분포 분석 - 재작성"""
    st.subheader("📊 메트릭 분포 분석")
    
    if not individual_scores:
        st.warning("📊 개별 QA 점수가 없습니다. 전체 평가 결과만 표시합니다.")
        
        # 전체 결과 표시
        if latest_results:
            metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
            col1, col2, col3, col4 = st.columns(4)
            
            for i, metric in enumerate(metrics):
                with [col1, col2, col3, col4][i]:
                    score = latest_results.get(metric, 0)
                    st.metric(
                        label=metric.replace('_', ' ').title(),
                        value=f"{score:.3f}"
                    )
        return
    
    # 개별 점수가 있는 경우 분포 분석
    num_qa = len(evaluation_data)
    num_scores = len(individual_scores)
    
    st.info(f"📊 QA 개수: {num_qa}, 개별 점수 개수: {num_scores}")
    
    # 안전한 길이로 조정
    safe_length = min(num_qa, num_scores)
    
    if safe_length == 0:
        st.error("분석할 데이터가 없습니다.")
        return
    
    # DataFrame 생성
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
    data = {'QA': [f'Q{i+1}' for i in range(safe_length)]}
    
    for metric in metrics:
        data[metric] = []
        for i in range(safe_length):
            if i < len(individual_scores) and individual_scores[i]:
                score = individual_scores[i].get(metric, 0)
            else:
                score = 0
            data[metric].append(score)
    
    df = pd.DataFrame(data)
    
    # 히트맵
    st.markdown("#### 🔥 메트릭 히트맵")
    
    heatmap_data = df[metrics].values
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=[m.replace('_', ' ').title() for m in metrics],
        y=df['QA'],
        colorscale='RdYlGn',
        colorbar=dict(title="점수")
    ))
    
    fig.update_layout(
        title="QA별 메트릭 성능 히트맵",
        height=400
    )
    
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


def show_pattern_analysis_new(evaluation_data, latest_results, individual_scores):
    """패턴 분석 - 재작성"""
    st.subheader("🎯 성능 패턴 분석")
    
    # 간단한 통계 분석
    qa_count = len(evaluation_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📝 데이터셋 개요")
        st.metric("총 QA 개수", qa_count)
        
        # 질문 길이 분석
        question_lengths = [len(qa['question'].split()) for qa in evaluation_data]
        avg_q_length = sum(question_lengths) / len(question_lengths)
        st.metric("평균 질문 길이", f"{avg_q_length:.1f} 단어")
        
        # 컨텍스트 개수 분석
        context_counts = [len(qa['contexts']) for qa in evaluation_data]
        avg_context_count = sum(context_counts) / len(context_counts)
        st.metric("평균 컨텍스트 개수", f"{avg_context_count:.1f}개")
    
    with col2:
        st.markdown("#### 📊 성능 요약")
        if latest_results:
            st.metric("전체 RAGAS 점수", f"{latest_results.get('ragas_score', 0):.3f}")
            
            # 최고/최저 메트릭
            metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
            scores = {m: latest_results.get(m, 0) for m in metrics}
            
            best_metric = max(scores, key=scores.get)
            worst_metric = min(scores, key=scores.get)
            
            st.text(f"최고 성능: {best_metric.replace('_', ' ').title()} ({scores[best_metric]:.3f})")
            st.text(f"개선 필요: {worst_metric.replace('_', ' ').title()} ({scores[worst_metric]:.3f})")
    
    # 개선 제안
    st.markdown("#### 💡 개선 제안")
    
    if latest_results:
        suggestions = []
        
        if latest_results.get('faithfulness', 0) < 0.7:
            suggestions.append("🎯 Faithfulness 개선: 컨텍스트 충실도 강화, 환각 방지 프롬프트 사용")
        
        if latest_results.get('answer_relevancy', 0) < 0.7:
            suggestions.append("🎯 Answer Relevancy 개선: 질문 의도 파악 강화, 간결한 답변 생성")
        
        if latest_results.get('context_recall', 0) < 0.7:
            suggestions.append("🎯 Context Recall 개선: 검색 범위 확대, 다양한 검색 전략 활용")
        
        if latest_results.get('context_precision', 0) < 0.7:
            suggestions.append("🎯 Context Precision 개선: 무관한 컨텍스트 필터링, 검색 정확도 향상")
        
        if not suggestions:
            suggestions.append("✅ 모든 메트릭이 양호한 수준입니다!")
        
        for suggestion in suggestions:
            st.info(suggestion)