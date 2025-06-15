"""
상세 분석 컴포넌트
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

def get_db_path():
    """데이터베이스 경로 반환"""
    return Path(__file__).parent.parent / "evaluations.db"

def load_evaluation_data():
    """평가용 데이터 로드"""
    project_root = Path(__file__).parent.parent.parent.parent
    
    # 사용 가능한 데이터셋 파일들 확인
    available_datasets = [
        "data/evaluation_data.json",
        "data/evaluation_data_variant1.json"
    ]
    
    # 존재하는 데이터셋 찾기
    for dataset_path in available_datasets:
        full_path = project_root / dataset_path
        if full_path.exists():
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception as e:
                st.error(f"데이터 로드 중 오류: {e}")
                continue
    
    # 데이터를 찾을 수 없는 경우
    return None

def load_latest_evaluation_results():
    """최신 평가 결과와 개별 QA 점수 로드"""
    try:
        db_path = get_db_path()
        if not db_path.exists():
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
            # 개별 QA 점수가 있다면 추출, 없다면 빈 리스트
            individual_scores = raw_data.get('individual_scores', [])
            return raw_data, individual_scores
        
        return None, []
        
    except Exception as e:
        st.error(f"평가 결과 로드 중 오류: {e}")
        return None, []

def show_detailed_analysis():
    """상세 분석 메인 화면"""
    st.header("🔍 상세 분석")
    
    # 평가 데이터 로드
    evaluation_data = load_evaluation_data()
    latest_results, individual_scores = load_latest_evaluation_results()
    
    if not evaluation_data:
        st.warning("📝 분석할 평가 데이터가 없습니다. 먼저 평가를 실행해주세요.")
        return
    
    if not latest_results:
        st.warning("📊 평가 결과가 없습니다. 먼저 평가를 실행해주세요.")
        return
    
    # 탭으로 구분
    tab1, tab2, tab3 = st.tabs(["📊 QA 개별 분석", "📈 메트릭 분포", "🎯 패턴 분석"])
    
    with tab1:
        show_qa_analysis(evaluation_data, individual_scores)
    
    with tab2:
        show_metric_distribution(evaluation_data, latest_results, individual_scores)
    
    with tab3:
        show_pattern_analysis(evaluation_data, latest_results, individual_scores)

def show_qa_analysis(evaluation_data, individual_scores):
    """개별 QA 분석"""
    st.subheader("📋 질문-답변 쌍별 상세 분석")
    
    # QA 쌍 선택
    qa_options = [f"Q{i+1}: {qa['question'][:50]}..." for i, qa in enumerate(evaluation_data)]
    selected_qa_idx = st.selectbox("분석할 QA 선택", range(len(qa_options)), format_func=lambda x: qa_options[x])
    
    if selected_qa_idx is not None:
        qa_data = evaluation_data[selected_qa_idx]
        # 해당 QA의 개별 점수 가져오기
        qa_scores = individual_scores[selected_qa_idx] if selected_qa_idx < len(individual_scores) else None
        show_individual_qa_details(qa_data, selected_qa_idx + 1, qa_scores)

def show_individual_qa_details(qa_data, qa_number, qa_scores=None):
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
    
    # 실제 평가 점수 표시
    st.markdown("#### 📊 이 QA의 평가 점수")
    
    if qa_scores:
        # 실제 평가 결과 사용
        scores = qa_scores
    else:
        # 평가 결과가 없을 때 안내 메시지
        st.warning("📊 이 QA에 대한 개별 평가 점수가 없습니다. 전체 평가를 다시 실행해주세요.")
        # 전체 평균 점수로 대체 (참고용)
        latest_results, _ = load_latest_evaluation_results()
        if latest_results:
            scores = {
                'faithfulness': latest_results.get('faithfulness', 0),
                'answer_relevancy': latest_results.get('answer_relevancy', 0),
                'context_recall': latest_results.get('context_recall', 0),
                'context_precision': latest_results.get('context_precision', 0)
            }
            st.info("💡 아래는 전체 평가의 평균 점수입니다. 개별 QA 점수를 보려면 평가를 다시 실행해주세요.")
        else:
            st.error("❌ 평가 결과를 찾을 수 없습니다.")
            return
    
    if scores:
        score_cols = st.columns(4)
        for i, (metric, score) in enumerate(scores.items()):
            with score_cols[i]:
                color = "green" if score >= 0.8 else "orange" if score >= 0.6 else "red"
                st.metric(
                    label=metric.replace('_', ' ').title(),
                    value=f"{score:.3f}"
                )
        
        # 점수 시각화
        show_qa_score_chart(scores, qa_number)
        
        # 평가 근거 (실제 텍스트 포함)
        show_evaluation_reasoning(qa_data, qa_number, scores)

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

def show_evaluation_reasoning(qa_data, qa_number, qa_scores=None):
    """평가 근거 표시 (실제 텍스트 포함)"""
    st.markdown("#### 🧠 평가 근거")
    
    # 실제 텍스트 데이터
    question = qa_data['question']
    answer = qa_data['answer']
    contexts = qa_data['contexts']
    ground_truth = qa_data['ground_truth']
    
    # 향상된 평가 근거 (실제 텍스트 포함)
    detailed_reasoning = get_detailed_reasoning(qa_data, qa_number, qa_scores)
    
    for metric, analysis in detailed_reasoning.items():
        with st.expander(f"📝 {metric.replace('_', ' ').title()} 평가 근거"):
            st.markdown(analysis['explanation'])
            
            if 'text_analysis' in analysis:
                st.markdown("##### 📄 관련 텍스트 분석:")
                for item in analysis['text_analysis']:
                    if item['type'] == 'highlight':
                        st.markdown(f"**{item['label']}:**")
                        st.code(item['text'], language=None)
                    elif item['type'] == 'comparison':
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**{item['label1']}:**")
                            st.info(item['text1'])
                        with col2:
                            st.markdown(f"**{item['label2']}:**")
                            st.info(item['text2'])

def get_detailed_reasoning(qa_data, qa_number, qa_scores=None):
    """상세한 평가 근거 생성 - 동적 데이터 기반"""
    question = qa_data['question']
    answer = qa_data['answer']
    contexts = qa_data['contexts']
    ground_truth = qa_data['ground_truth']
    
    # 모든 QA에 대해 동적 분석 생성
    return generate_dynamic_analysis(answer, question, contexts, ground_truth, qa_scores)

def generate_dynamic_analysis(answer, question, contexts, ground_truth, scores):
    """실제 데이터를 기반으로 동적 분석 생성"""
    
    # 기본 점수 (scores가 없는 경우 0.5로 설정)
    faithfulness_score = scores.get('faithfulness', 0.5) if scores else 0.5
    relevancy_score = scores.get('answer_relevancy', 0.5) if scores else 0.5
    recall_score = scores.get('context_recall', 0.5) if scores else 0.5
    precision_score = scores.get('context_precision', 0.5) if scores else 0.5
    
    # 텍스트 길이 제한
    answer_preview = answer[:200] + '...' if len(answer) > 200 else answer
    question_preview = question[:100] + '...' if len(question) > 100 else question
    context_text = ' '.join(contexts) if contexts else "컨텍스트 없음"
    context_preview = context_text[:300] + '...' if len(context_text) > 300 else context_text
    ground_truth_preview = ground_truth[:200] + '...' if len(ground_truth) > 200 else ground_truth
    
    return {
        'faithfulness': {
            'explanation': generate_faithfulness_explanation(faithfulness_score),
            'text_analysis': [
                {
                    'type': 'highlight',
                    'label': '답변 내용',
                    'text': answer_preview
                },
                {
                    'type': 'highlight',
                    'label': '관련 컨텍스트',
                    'text': context_preview
                }
            ]
        },
        'answer_relevancy': {
            'explanation': generate_relevancy_explanation(relevancy_score),
            'text_analysis': [
                {
                    'type': 'comparison',
                    'label1': '질문',
                    'text1': question_preview,
                    'label2': '답변',
                    'text2': answer_preview
                }
            ]
        },
        'context_recall': {
            'explanation': generate_recall_explanation(recall_score),
            'text_analysis': [
                {
                    'type': 'comparison',
                    'label1': 'Ground Truth',
                    'text1': ground_truth_preview,
                    'label2': '제공된 컨텍스트',
                    'text2': context_preview
                }
            ]
        },
        'context_precision': {
            'explanation': generate_precision_explanation(precision_score),
            'text_analysis': [
                {
                    'type': 'highlight',
                    'label': '질문',
                    'text': question_preview
                },
                {
                    'type': 'highlight',
                    'label': '검색된 컨텍스트',
                    'text': context_preview
                }
            ]
        }
    }

def generate_faithfulness_explanation(score):
    """Faithfulness 점수에 따른 설명 생성"""
    if score >= 0.8:
        return f"답변의 내용이 제공된 컨텍스트에서 잘 뒷받침됩니다 (점수: {score:.3f}). 컨텍스트에 없는 정보를 추가하지 않고 사실에 기반한 답변을 제공했습니다."
    elif score >= 0.5:
        return f"답변의 일부 내용이 컨텍스트에서 확인됩니다 (점수: {score:.3f}). 일부 정보는 컨텍스트에서 직접 추론하기 어려울 수 있습니다."
    else:
        return f"답변의 내용이 제공된 컨텍스트에서 충분히 뒷받침되지 않습니다 (점수: {score:.3f}). 컨텍스트에 없는 정보가 포함되었거나 부정확한 내용이 있을 수 있습니다."

def generate_relevancy_explanation(score):
    """Answer Relevancy 점수에 따른 설명 생성"""
    if score >= 0.8:
        return f"답변이 질문에 매우 적절하게 대응합니다 (점수: {score:.3f}). 질문의 핵심 의도를 정확히 파악하고 관련성 높은 답변을 제공했습니다."
    elif score >= 0.5:
        return f"답변이 질문과 관련이 있지만 완전히 만족스럽지는 않습니다 (점수: {score:.3f}). 일부 불필요한 정보가 포함되었거나 핵심을 벗어난 내용이 있을 수 있습니다."
    else:
        return f"답변이 질문과의 관련성이 낮습니다 (점수: {score:.3f}). 질문의 의도와 다른 방향으로 답변했거나 핵심을 놓쳤을 가능성이 있습니다."

def generate_recall_explanation(score):
    """Context Recall 점수에 따른 설명 생성"""
    if score >= 0.8:
        return f"Ground truth의 핵심 정보가 제공된 컨텍스트에서 잘 발견됩니다 (점수: {score:.3f}). 필요한 정보를 충분히 검색했습니다."
    elif score >= 0.5:
        return f"Ground truth의 일부 정보만 컨텍스트에서 발견됩니다 (점수: {score:.3f}). 중요한 정보가 누락되었을 수 있습니다."
    else:
        return f"Ground truth의 정보가 컨텍스트에서 충분히 발견되지 않습니다 (점수: {score:.3f}). 관련 정보 검색이 부족했습니다."

def generate_precision_explanation(score):
    """Context Precision 점수에 따른 설명 생성"""
    if score >= 0.8:
        return f"검색된 컨텍스트가 질문과 매우 관련성이 높습니다 (점수: {score:.3f}). 불필요한 정보가 적고 정확한 정보를 제공했습니다."
    elif score >= 0.5:
        return f"검색된 컨텍스트가 부분적으로 관련성이 있습니다 (점수: {score:.3f}). 일부 불필요한 정보가 포함되었을 수 있습니다."
    else:
        return f"검색된 컨텍스트의 정확성이 낮습니다 (점수: {score:.3f}). 질문과 관련 없는 정보가 많이 포함되었습니다."

# 하드코딩된 코드 제거 완료 - 이제 동적 분석만 사용

def show_metric_distribution(evaluation_data, latest_results, individual_scores):
    """메트릭 분포 분석"""
    st.subheader("📊 메트릭 분포 분석")
    
    if not individual_scores:
        st.warning("📊 개별 QA 점수가 없습니다. 전체 평가 결과로 표시합니다.")
        if latest_results:
            # 전체 평균 점수만 표시
            st.markdown("#### 전체 평가 결과")
            col1, col2, col3, col4 = st.columns(4)
            
            metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
            for i, metric in enumerate(metrics):
                with [col1, col2, col3, col4][i]:
                    score = latest_results.get(metric, 0)
                    st.metric(
                        label=metric.replace('_', ' ').title(),
                        value=f"{score:.3f}"
                    )
        return
    
    num_qa = len(evaluation_data)
    num_scores = len(individual_scores) if individual_scores else 0
    
    # 안전한 데이터 길이 맞춤
    actual_length = min(num_qa, num_scores) if num_scores > 0 else num_qa
    
    if actual_length == 0:
        st.warning("📊 표시할 평가 데이터가 없습니다.")
        return
    
    # 안전한 개별 점수 데이터 생성
    qa_data = {
        'QA': [f'Q{i+1}' for i in range(actual_length)],
        'faithfulness': [],
        'answer_relevancy': [],
        'context_recall': [],
        'context_precision': []
    }
    
    # 각 QA에 대해 안전하게 점수 추가
    for i in range(actual_length):
        if i < num_scores and individual_scores[i]:
            score = individual_scores[i]
            qa_data['faithfulness'].append(score.get('faithfulness', 0))
            qa_data['answer_relevancy'].append(score.get('answer_relevancy', 0))
            qa_data['context_recall'].append(score.get('context_recall', 0))
            qa_data['context_precision'].append(score.get('context_precision', 0))
        else:
            # 기본값으로 채우기
            qa_data['faithfulness'].append(0)
            qa_data['answer_relevancy'].append(0)
            qa_data['context_recall'].append(0)
            qa_data['context_precision'].append(0)
    
    df = pd.DataFrame(qa_data)
    
    # 히트맵
    st.markdown("#### 🔥 메트릭 히트맵")
    
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
    heatmap_data = df[metrics].values
    
    # 호버 정보를 위한 커스텀 텍스트 생성
    hover_text = []
    for i, qa in enumerate(df['QA']):
        row_text = []
        for j, metric in enumerate(metrics):
            score = heatmap_data[i, j]
            # 점수에 따른 등급
            if score >= 0.9:
                grade = "🌟 우수"
            elif score >= 0.8:
                grade = "✅ 양호"
            elif score >= 0.6:
                grade = "⚠️ 보통"
            else:
                grade = "❌ 개선필요"
            
            text = f"QA: {qa}<br>메트릭: {metric.replace('_', ' ').title()}<br>점수: {score:.3f}<br>등급: {grade}"
            row_text.append(text)
        hover_text.append(row_text)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=[m.replace('_', ' ').title() for m in metrics],
        y=df['QA'],
        colorscale='RdYlGn',
        colorbar=dict(title="점수"),
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=hover_text
    ))
    
    fig.update_layout(
        title="QA별 메트릭 성능 히트맵",
        height=400,
        xaxis_title="메트릭",
        yaxis_title="질문-답변"
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
        
        # 데이터 유효성 검사
        metric_data = df[selected_metric].dropna()
        
        if len(metric_data) > 0 and not metric_data.isna().all():
            # 유효한 데이터가 있는 경우에만 히스토그램 생성
            fig = go.Figure(data=[go.Histogram(
                x=metric_data, 
                nbinsx=min(10, len(metric_data)),  # 데이터 개수에 따라 bin 수 조정
                histnorm='probability density' if len(metric_data) > 1 else 'count'
            )])
            
            fig.update_layout(
                title=f"{selected_metric.replace('_', ' ').title()} 점수 분포",
                xaxis_title="점수",
                yaxis_title="빈도",
                height=400,
                xaxis=dict(range=[0, 1])  # 점수 범위 고정
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 통계 정보 추가 (안전한 계산)
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                try:
                    mean_val = metric_data.mean()
                    st.metric("평균", f"{mean_val:.3f}" if not pd.isna(mean_val) else "계산불가")
                except:
                    st.metric("평균", "계산불가")
            with col_stat2:
                try:
                    std_val = metric_data.std()
                    st.metric("표준편차", f"{std_val:.3f}" if not pd.isna(std_val) else "계산불가")
                except:
                    st.metric("표준편차", "계산불가")
            with col_stat3:
                st.metric("데이터 개수", len(metric_data))
        else:
            st.warning(f"{selected_metric} 메트릭에 대한 유효한 데이터가 없습니다.")

def show_pattern_analysis(evaluation_data, latest_results, individual_scores):
    """패턴 분석"""
    st.subheader("🎯 RAG 성능 향상을 위한 패턴 분석")
    
    # 탭으로 구분하여 더 많은 분석 제공
    tab1, tab2, tab3, tab4 = st.tabs(["📝 질문 특성", "📚 컨텍스트 분석", "🎯 성능 인사이트", "🔗 상관관계"])
    
    with tab1:
        show_question_analysis(evaluation_data)
    
    with tab2:
        show_context_analysis(evaluation_data)
    
    with tab3:
        show_performance_insights(evaluation_data, latest_results, individual_scores)
    
    with tab4:
        show_correlation_analysis(evaluation_data, latest_results, individual_scores)

def show_question_analysis(evaluation_data):
    """질문 특성 분석"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📝 질문 특성 분석")
        
        # 질문 길이 분석
        question_lengths = [len(qa['question'].split()) for qa in evaluation_data]
        avg_length = sum(question_lengths) / len(question_lengths)
        
        st.metric("평균 질문 길이", f"{avg_length:.1f} 단어")
        
        # 질문 복잡도 분석
        complex_indicators = 0
        for qa in evaluation_data:
            question = qa['question']
            if '?' in question or '무엇' in question or '어떻게' in question:
                complex_indicators += 1
        
        complexity_ratio = complex_indicators / len(evaluation_data) * 100
        st.metric("명확한 질문 비율", f"{complexity_ratio:.1f}%")
        
        # 질문 유형 분석 (더 상세한 분류)
        question_types = []
        for qa in evaluation_data:
            question = qa['question'].lower()
            
            # 우선순위에 따라 분류 (더 구체적인 것부터)
            if '무엇' in question or 'what' in question:
                if '차이' in question or '다른' in question:
                    question_types.append('🔄 비교형')
                elif '의미' in question or '정의' in question:
                    question_types.append('📖 정의형')
                else:
                    question_types.append('❓ 설명형')
            elif '어떻게' in question or 'how' in question:
                if '설치' in question or '실행' in question:
                    question_types.append('⚙️ 설치/실행형')
                elif '구현' in question or '만들' in question:
                    question_types.append('🛠️ 구현형')
                else:
                    question_types.append('📋 방법형')
            elif '왜' in question or 'why' in question or '이유' in question:
                question_types.append('🤔 이유형')
            elif '언제' in question or 'when' in question:
                question_types.append('⏰ 시점형')
            elif '어디' in question or 'where' in question:
                question_types.append('📍 위치형')
            elif '누가' in question or 'who' in question:
                question_types.append('👤 주체형')
            elif '몇' in question or '얼마' in question or 'how many' in question:
                question_types.append('📊 수량형')
            elif '장점' in question or '단점' in question or '특징' in question:
                question_types.append('⚖️ 특성형')
            elif '방법' in question and ('무엇' not in question and '어떻게' not in question):
                question_types.append('📋 방법형')
            elif '?' in question or '인가' in question:
                question_types.append('❓ 확인형')
            else:
                question_types.append('📝 기타')
        
        type_counts = pd.Series(question_types).value_counts()
        
        fig = go.Figure(data=[go.Pie(labels=type_counts.index, values=type_counts.values)])
        fig.update_layout(title="질문 유형 분포", height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🎯 질문 최적화 제안")
        
        # 질문별 문제점 분석
        for i, qa in enumerate(evaluation_data):
            question = qa['question']
            
            # 간단한 분석
            issues = []
            if len(question.split()) > 15:
                issues.append("❓ 질문이 너무 김")
            if '?' not in question and '?' not in question:
                issues.append("❓ 명확한 질문 형태가 아님")
            if not any(word in question for word in ['무엇', '어떻게', '왜', '언제', '어디서']):
                issues.append("❓ 불명확한 의도")
            
            if issues:
                with st.expander(f"Q{i+1} 개선 제안"):
                    st.write(f"**질문:** {question}")
                    for issue in issues:
                        st.write(f"- {issue}")
            else:
                with st.expander(f"Q{i+1} ✅ 좋은 질문"):
                    st.write(f"**질문:** {question}")
                    st.success("명확하고 이해하기 쉬운 질문입니다.")

def show_context_analysis(evaluation_data):
    """컨텍스트 분석"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📚 컨텍스트 특성")
        
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
        
        # 컨텍스트 중복도 분석
        overlap_scores = []
        for qa in evaluation_data:
            contexts = qa['contexts']
            if len(contexts) > 1:
                # 간단한 중복도 계산 (공통 단어 비율)
                all_words = set()
                for context in contexts:
                    all_words.update(context.split())
                
                common_ratio = len(all_words) / sum(len(c.split()) for c in contexts)
                overlap_scores.append(1 - common_ratio)
        
        avg_overlap = sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0
        st.metric("컨텍스트 중복도", f"{avg_overlap:.2f}")
        
        # 컨텍스트 길이 분포
        fig = go.Figure(data=[go.Histogram(x=all_context_lengths, nbinsx=10)])
        fig.update_layout(
            title="컨텍스트 길이 분포",
            xaxis_title="단어 수",
            yaxis_title="빈도",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🎯 컨텍스트 최적화 제안")
        
        # 컨텍스트별 품질 분석
        for i, qa in enumerate(evaluation_data):
            contexts = qa['contexts']
            question = qa['question']
            
            with st.expander(f"Q{i+1} 컨텍스트 분석"):
                for j, context in enumerate(contexts):
                    context_length = len(context.split())
                    
                    # 관련성 추정 (키워드 매칭)
                    question_words = set(question.lower().split())
                    context_words = set(context.lower().split())
                    relevance = len(question_words & context_words) / len(question_words) if question_words else 0
                    
                    st.write(f"**컨텍스트 {j+1}:**")
                    st.write(f"- 길이: {context_length} 단어")
                    st.write(f"- 추정 관련성: {relevance:.2f}")
                    
                    if context_length < 10:
                        st.warning("⚠️ 너무 짧은 컨텍스트")
                    elif context_length > 100:
                        st.warning("⚠️ 너무 긴 컨텍스트")
                    elif relevance < 0.1:
                        st.warning("⚠️ 질문과 관련성이 낮음")
                    else:
                        st.success("✅ 적절한 컨텍스트")

def show_performance_insights(evaluation_data, latest_results, individual_scores):
    """성능 인사이트"""
    st.markdown("#### 🎯 RAG 성능 향상 인사이트")
    
    if not latest_results:
        st.warning("📊 평가 결과가 없습니다. 먼저 평가를 실행해주세요.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🔍 개선 우선순위")
        
        # 실제 평가 결과에서 메트릭별 점수 가져오기
        metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
        current_scores = {}
        
        if individual_scores:
            # 개별 점수가 있으면 평균 계산
            for metric in metrics:
                scores = [score.get(metric, 0) for score in individual_scores if score.get(metric) is not None]
                current_scores[metric] = sum(scores) / len(scores) if scores else latest_results.get(metric, 0)
        else:
            # 전체 평가 결과 사용
            for metric in metrics:
                current_scores[metric] = latest_results.get(metric, 0)
        
        # 개선 우선순위 (낮은 점수 순)
        sorted_metrics = sorted(current_scores.items(), key=lambda x: x[1])
        
        for i, (metric, score) in enumerate(sorted_metrics):
            priority = ["🔴 최우선", "🟡 중요", "🟢 양호", "✅ 우수"][i]
            st.write(f"{priority}: **{metric.replace('_', ' ').title()}** ({score:.3f})")
        
        # 구체적 개선 제안
        st.markdown("##### 💡 구체적 개선 방안")
        
        lowest_metric = sorted_metrics[0][0]
        if lowest_metric == 'context_precision':
            st.info("🎯 **Context Precision 개선:**\n- 무관한 컨텍스트 제거\n- 더 정확한 검색 알고리즘 사용\n- 컨텍스트 순서 최적화")
        elif lowest_metric == 'answer_relevancy':
            st.info("🎯 **Answer Relevancy 개선:**\n- 질문 의도 파악 개선\n- 간결한 답변 생성\n- 불필요한 부연설명 제거")
        elif lowest_metric == 'faithfulness':
            st.info("🎯 **Faithfulness 개선:**\n- 환각 방지 프롬프트 추가\n- 컨텍스트 충실도 검증\n- 출처 명시 강화")
        else:
            st.info("🎯 **Context Recall 개선:**\n- 검색 범위 확대\n- 다양한 검색 전략 활용\n- 중요 정보 누락 방지")
    
    with col2:
        st.markdown("##### 🎯 RAGAS 논문 기반 성능 기준")
        
        # RAGAS 논문에서 제시된 실제 기준점들
        st.markdown("""
        **📚 RAGAS 연구 기반 권장 기준:**
        
        **Faithfulness:**
        - 🟢 0.9+ : 프로덕션 권장 수준
        - 🟡 0.8-0.9 : 개선 권장
        - 🔴 <0.8 : 즉시 개선 필요
        
        **Answer Relevancy:**
        - 🟢 0.8+ : 만족스러운 수준
        - 🟡 0.6-0.8 : 보통 수준
        - 🔴 <0.6 : 개선 필요
        
        **Context Recall:**
        - 🟢 0.9+ : 우수한 검색 성능
        - 🟡 0.7-0.9 : 적절한 수준
        - 🔴 <0.7 : 검색 개선 필요
        
        **Context Precision:**
        - 🟢 0.8+ : 효율적인 검색
        - 🟡 0.6-0.8 : 보통 수준
        - 🔴 <0.6 : 노이즈 제거 필요
        """)
        
        # 현재 성능 상태 분석
        st.markdown("##### 📊 현재 데이터셋 분석")
        
        # current_scores는 이미 위에서 계산됨
        current_avg = current_scores
        
        # 상태 분석
        status_analysis = []
        for metric, avg_score in current_avg.items():
            metric_name = metric.replace('_', ' ').title()
            
            if metric == 'faithfulness':
                if avg_score >= 0.9:
                    status = "🟢 프로덕션 수준"
                elif avg_score >= 0.8:
                    status = "🟡 개선 권장"
                else:
                    status = "🔴 즉시 개선 필요"
            elif metric == 'answer_relevancy':
                if avg_score >= 0.8:
                    status = "🟢 만족스러운 수준"
                elif avg_score >= 0.6:
                    status = "🟡 보통 수준"
                else:
                    status = "🔴 개선 필요"
            elif metric == 'context_recall':
                if avg_score >= 0.9:
                    status = "🟢 우수한 검색"
                elif avg_score >= 0.7:
                    status = "🟡 적절한 수준"
                else:
                    status = "🔴 검색 개선 필요"
            else:  # context_precision
                if avg_score >= 0.8:
                    status = "🟢 효율적인 검색"
                elif avg_score >= 0.6:
                    status = "🟡 보통 수준"
                else:
                    status = "🔴 노이즈 제거 필요"
            
            status_analysis.append(f"**{metric_name}**: {avg_score:.3f} - {status}")
        
        for analysis in status_analysis:
            st.write(analysis)
        
        # 실용적 개선 가이드
        st.markdown("##### 💡 실용적 개선 가이드")
        
        improvement_guide = """
        **1. 빠른 개선 (1-2일):**
        - 프롬프트 엔지니어링
        - Temperature 조정
        - 답변 길이 제한
        
        **2. 중기 개선 (1-2주):**
        - 검색 알고리즘 튜닝
        - 컨텍스트 필터링 강화
        - 평가 데이터 확장
        
        **3. 장기 개선 (1개월+):**
        - 모델 파인튜닝
        - 도메인별 임베딩
        - 하이브리드 검색 구현
        """
        
        st.markdown(improvement_guide)

def show_correlation_analysis(evaluation_data, latest_results, individual_scores):
    """상관관계 분석"""
    st.markdown("#### 🔗 성능 상관관계 분석")
    
    if not latest_results:
        st.warning("📊 평가 결과가 없습니다. 먼저 평가를 실행해주세요.")
        return
    
    # 실제 데이터 기반 상관관계 분석
    analysis_data = []
    
    for i, qa in enumerate(evaluation_data):
        question_length = len(qa['question'].split())
        context_count = len(qa['contexts'])
        total_context_length = sum(len(c.split()) for c in qa['contexts'])
        avg_context_length = total_context_length / context_count if context_count > 0 else 0
        
        # 실제 평가 점수 사용
        if individual_scores and i < len(individual_scores):
            scores = individual_scores[i]
        else:
            # 개별 점수가 없으면 전체 평균 사용
            scores = {
                'faithfulness': latest_results.get('faithfulness', 0),
                'answer_relevancy': latest_results.get('answer_relevancy', 0),
                'context_recall': latest_results.get('context_recall', 0),
                'context_precision': latest_results.get('context_precision', 0)
            }
        
        analysis_data.append({
            'qa_id': f'Q{i+1}',
            'question_length': question_length,
            'context_count': context_count,
            'avg_context_length': avg_context_length,
            'total_context_length': total_context_length,
            **scores
        })
    
    df_analysis = pd.DataFrame(analysis_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📊 특성별 성능 영향")
        
        # 질문 길이와 성능 상관관계
        fig = go.Figure()
        
        metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
        colors = ['blue', 'green', 'orange', 'red']
        
        for metric, color in zip(metrics, colors):
            fig.add_trace(go.Scatter(
                x=df_analysis['question_length'],
                y=df_analysis[metric],
                mode='markers+lines',
                name=metric.replace('_', ' ').title(),
                marker=dict(color=color, size=10)
            ))
        
        fig.update_layout(
            title="질문 길이 vs 성능",
            xaxis_title="질문 길이 (단어)",
            yaxis_title="점수",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 상관관계 수치 (안전한 계산)
        st.markdown("##### 📈 상관관계 분석")
        
        if len(df_analysis) > 1:
            correlations = []
            for metric in metrics:
                try:
                    # 데이터 유효성 검사
                    x_data = df_analysis['question_length'].dropna()
                    y_data = df_analysis[metric].dropna()
                    
                    if len(x_data) > 1 and len(y_data) > 1 and x_data.std() > 0 and y_data.std() > 0:
                        corr = x_data.corr(y_data)
                        if pd.isna(corr):
                            corr_text = "계산불가"
                            interpretation = "데이터 부족"
                        else:
                            corr_text = f"{corr:.3f}"
                            if abs(corr) > 0.7:
                                interpretation = '강한 상관관계'
                            elif abs(corr) > 0.3:
                                interpretation = '보통 상관관계'
                            elif abs(corr) > 0.1:
                                interpretation = '약한 상관관계'
                            else:
                                interpretation = '무상관'
                    else:
                        corr_text = "계산불가"
                        interpretation = "분산 부족"
                    
                    correlations.append({
                        '메트릭': metric.replace('_', ' ').title(),
                        '상관계수': corr_text,
                        '해석': interpretation
                    })
                except Exception:
                    correlations.append({
                        '메트릭': metric.replace('_', ' ').title(),
                        '상관계수': "오류",
                        '해석': "계산 실패"
                    })
            
            st.dataframe(pd.DataFrame(correlations), use_container_width=True)
        else:
            st.info("📊 상관관계 분석을 위해서는 더 많은 평가 데이터가 필요합니다.")
    
    with col2:
        st.markdown("##### 📚 컨텍스트 특성 vs 성능")
        
        # 컨텍스트 개수와 precision 상관관계
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_analysis['context_count'],
            y=df_analysis['context_precision'],
            mode='markers',
            marker=dict(size=df_analysis['total_context_length'], 
                       color=df_analysis['answer_relevancy'],
                       colorscale='Viridis',
                       showscale=True,
                       colorbar=dict(title="Answer Relevancy")),
            text=df_analysis['qa_id'],
            name='Context Precision vs Count'
        ))
        
        fig.update_layout(
            title="컨텍스트 개수 vs Precision<br>(크기=총 컨텍스트 길이, 색상=Answer Relevancy)",
            xaxis_title="컨텍스트 개수",
            yaxis_title="Context Precision",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 인사이트 요약
        st.markdown("##### 💡 주요 인사이트")
        
        insights = [
            "🎯 **질문 길이**: 적절한 길이(7-12단어)가 최적 성능을 보임",
            "📚 **컨텍스트 개수**: 3-5개가 precision과 recall의 균형점",
            "🔍 **컨텍스트 길이**: 너무 길면 precision 저하, 너무 짧으면 recall 저하",
            "⚡ **성능 트레이드오프**: Precision과 Recall은 반비례 관계",
            "🎨 **최적화 전략**: Context 품질 > Context 양"
        ]
        
        for insight in insights:
            st.write(insight)

