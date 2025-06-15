"""
상세 분석 컴포넌트
개별 QA 쌍의 상세 평가 결과 분석
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from pathlib import Path

def show_detailed_analysis():
    """상세 분석 메인 화면"""
    st.header("🔍 상세 분석")
    
    # 평가 데이터 로드
    evaluation_data = load_evaluation_data()
    
    if not evaluation_data:
        st.warning("📝 분석할 평가 데이터가 없습니다. 먼저 평가를 실행해주세요.")
        return
    
    # 탭으로 구분
    tab1, tab2, tab3 = st.tabs(["📊 QA 개별 분석", "📈 메트릭 분포", "🎯 패턴 분석"])
    
    with tab1:
        show_qa_analysis(evaluation_data)
    
    with tab2:
        show_metric_distribution(evaluation_data)
    
    with tab3:
        show_pattern_analysis(evaluation_data)

def show_qa_analysis(evaluation_data):
    """개별 QA 분석"""
    st.subheader("📋 질문-답변 쌍별 상세 분석")
    
    # QA 쌍 선택
    qa_options = [f"Q{i+1}: {qa['question'][:50]}..." for i, qa in enumerate(evaluation_data)]
    selected_qa_idx = st.selectbox("분석할 QA 선택", range(len(qa_options)), format_func=lambda x: qa_options[x])
    
    if selected_qa_idx is not None:
        qa_data = evaluation_data[selected_qa_idx]
        show_individual_qa_details(qa_data, selected_qa_idx + 1)

def show_individual_qa_details(qa_data, qa_number):
    """개별 QA 상세 정보 표시"""
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
            st.markdown(f"**컨텍스트 {i}:**")
            st.text_area(f"context_{i}", context, height=80, disabled=True, key=f"context_{qa_number}_{i}")
        
        st.markdown("#### ✅ 정답 (Ground Truth)")
        st.info(qa_data['ground_truth'])
    
    # 가상의 개별 점수 (실제로는 최신 평가 결과에서 가져와야 함)
    st.markdown("#### 📊 이 QA의 평가 점수")
    
    # 실제 구현에서는 저장된 상세 결과에서 가져와야 함
    mock_scores = {
        'faithfulness': 1.0 if qa_number == 1 else 1.0,
        'answer_relevancy': 0.861 if qa_number == 1 else 0.741,
        'context_recall': 1.0,
        'context_precision': 0.5 if qa_number == 1 else 1.0
    }
    
    score_cols = st.columns(4)
    for i, (metric, score) in enumerate(mock_scores.items()):
        with score_cols[i]:
            color = "green" if score >= 0.8 else "orange" if score >= 0.6 else "red"
            st.metric(
                label=metric.replace('_', ' ').title(),
                value=f"{score:.3f}",
                delta=f"{score - 0.5:.3f}"
            )
    
    # 점수 시각화
    show_qa_score_chart(mock_scores, qa_number)
    
    # 평가 근거 (모의 데이터)
    show_evaluation_reasoning(qa_number)

def show_qa_score_chart(scores, qa_number):
    """개별 QA 점수 차트"""
    st.markdown("#### 📈 점수 시각화")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 바 차트
        metrics = list(scores.keys())
        values = list(scores.values())
        
        fig = go.Figure(data=[
            go.Bar(x=metrics, y=values, 
                  marker_color=['green' if v >= 0.8 else 'orange' if v >= 0.6 else 'red' for v in values])
        ])
        
        fig.update_layout(
            title=f"QA {qa_number} 메트릭 점수",
            yaxis_title="점수",
            yaxis=dict(range=[0, 1]),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 게이지 차트 (평균 점수)
        avg_score = sum(values) / len(values)
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = avg_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"QA {qa_number} 종합 점수"},
            delta = {'reference': 0.5},
            gauge = {
                'axis': {'range': [None, 1]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 0.5], 'color': "lightgray"},
                    {'range': [0.5, 0.8], 'color': "yellow"},
                    {'range': [0.8, 1], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0.9
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def show_evaluation_reasoning(qa_number):
    """평가 근거 표시 (모의 데이터)"""
    st.markdown("#### 🧠 평가 근거")
    
    # 실제로는 RAGAS traces에서 가져와야 함
    mock_reasoning = {
        1: {
            'faithfulness': "답변의 모든 내용이 제공된 컨텍스트에서 뒷받침됩니다. 의존성 규칙에 대한 설명이 정확합니다.",
            'answer_relevancy': "질문에 직접적으로 답변하고 있으나, 일부 추가적인 설명이 포함되어 관련성이 약간 낮습니다.",
            'context_recall': "Ground truth의 모든 정보가 제공된 컨텍스트에서 발견됩니다.",
            'context_precision': "첫 번째 컨텍스트는 일반적인 설명이고, 두 번째가 핵심 답변을 포함합니다."
        },
        2: {
            'faithfulness': "답변이 컨텍스트의 정보와 완전히 일치하며 추가 정보를 만들어내지 않았습니다.",
            'answer_relevancy': "질문과 직접 관련된 답변이지만 일부 표현이 다소 복잡합니다.",
            'context_recall': "Ground truth의 모든 요소가 컨텍스트에서 확인됩니다.",
            'context_precision': "모든 컨텍스트가 답변에 직접적으로 기여합니다."
        }
    }
    
    reasoning = mock_reasoning.get(qa_number, mock_reasoning[1])
    
    for metric, explanation in reasoning.items():
        with st.expander(f"📝 {metric.replace('_', ' ').title()} 평가 근거"):
            st.write(explanation)

def show_metric_distribution(evaluation_data):
    """메트릭 분포 분석"""
    st.subheader("📊 메트릭 분포 분석")
    
    # 모의 점수 데이터 (실제로는 저장된 결과에서)
    mock_data = {
        'QA': [f'Q{i+1}' for i in range(len(evaluation_data))],
        'faithfulness': [1.0, 1.0],
        'answer_relevancy': [0.861, 0.741],
        'context_recall': [1.0, 1.0], 
        'context_precision': [0.5, 1.0]
    }
    
    df = pd.DataFrame(mock_data)
    
    # 히트맵
    st.markdown("#### 🔥 메트릭 히트맵")
    
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
    heatmap_data = df[metrics].values
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=metrics,
        y=df['QA'],
        colorscale='RdYlGn',
        colorbar=dict(title="점수")
    ))
    
    fig.update_layout(
        title="QA별 메트릭 성능 히트맵",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 분포 차트
    st.markdown("#### 📈 점수 분포")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 박스플롯
        fig = go.Figure()
        
        for metric in metrics:
            fig.add_trace(go.Box(
                y=df[metric],
                name=metric.replace('_', ' ').title(),
                boxpoints='all'
            ))
        
        fig.update_layout(
            title="메트릭별 점수 분포",
            yaxis_title="점수",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 히스토그램
        selected_metric = st.selectbox("분포를 볼 메트릭 선택", metrics)
        
        fig = go.Figure(data=[go.Histogram(x=df[selected_metric], nbinsx=10)])
        
        fig.update_layout(
            title=f"{selected_metric.replace('_', ' ').title()} 점수 분포",
            xaxis_title="점수",
            yaxis_title="빈도",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_pattern_analysis(evaluation_data):
    """패턴 분석"""
    st.subheader("🎯 패턴 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📝 질문 특성 분석")
        
        # 질문 길이 분석
        question_lengths = [len(qa['question'].split()) for qa in evaluation_data]
        avg_length = sum(question_lengths) / len(question_lengths)
        
        st.metric("평균 질문 길이", f"{avg_length:.1f} 단어")
        
        # 질문 유형 분석 (간단한 키워드 기반)
        question_types = []
        for qa in evaluation_data:
            question = qa['question'].lower()
            if '무엇' in question:
                question_types.append('정의형')
            elif '어떻게' in question:
                question_types.append('방법형')
            elif '왜' in question:
                question_types.append('이유형')
            else:
                question_types.append('기타')
        
        type_counts = pd.Series(question_types).value_counts()
        
        fig = go.Figure(data=[go.Pie(labels=type_counts.index, values=type_counts.values)])
        fig.update_layout(title="질문 유형 분포", height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📚 컨텍스트 특성 분석")
        
        # 컨텍스트 개수 분석
        context_counts = [len(qa['contexts']) for qa in evaluation_data]
        avg_contexts = sum(context_counts) / len(context_counts)
        
        st.metric("평균 컨텍스트 개수", f"{avg_contexts:.1f} 개")
        
        # 컨텍스트 길이 분석
        all_context_lengths = []
        for qa in evaluation_data:
            for context in qa['contexts']:
                all_context_lengths.append(len(context.split()))
        
        avg_context_length = sum(all_context_lengths) / len(all_context_lengths)
        st.metric("평균 컨텍스트 길이", f"{avg_context_length:.1f} 단어")
        
        # 컨텍스트 길이 분포
        fig = go.Figure(data=[go.Histogram(x=all_context_lengths, nbinsx=10)])
        fig.update_layout(
            title="컨텍스트 길이 분포",
            xaxis_title="단어 수",
            yaxis_title="빈도",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 성능 상관관계 분석
    st.markdown("#### 🔗 성능 상관관계")
    
    # 모의 상관관계 데이터
    st.info("📊 질문 길이와 성능 간의 상관관계, 컨텍스트 개수와 precision 간의 관계 등을 분석할 수 있습니다.")

def load_evaluation_data():
    """평가 데이터 로드"""
    try:
        project_root = Path(__file__).parent.parent.parent
        data_path = project_root / "data" / "evaluation_data.json"
        
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"데이터 로드 중 오류: {e}")
        return None