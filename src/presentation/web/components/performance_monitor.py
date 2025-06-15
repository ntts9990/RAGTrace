"""
성능 모니터링 컴포넌트
RAGAS 평가 시스템의 성능 및 리소스 사용량 모니터링
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import json

def show_performance_monitor():
    """성능 모니터링 메인 화면"""
    st.header("⚡ 성능 모니터링")
    
    st.markdown("""
    🎯 **RAGAS 평가 시스템의 실제 데이터 기반 모니터링**
    
    실제 평가 실행 데이터를 바탕으로 성능을 추적합니다.
    """)
    
    # 실제 데이터 확인
    evaluation_history = load_evaluation_history_for_performance()
    
    if not evaluation_history:
        st.warning("📊 성능 모니터링을 위한 평가 데이터가 부족합니다. 먼저 몇 번의 평가를 실행해주세요.")
        st.info("💡 최소 3회 이상의 평가 실행 후 의미있는 성능 분석이 가능합니다.")
        return
    
    # 탭으로 구분 (실제 데이터만)
    tab1, tab2 = st.tabs(["⏱️ 평가 이력", "📊 API 사용현황"])
    
    with tab1:
        show_evaluation_history_analysis(evaluation_history)
    
    with tab2:
        show_api_usage_analysis(evaluation_history)

def load_evaluation_history_for_performance():
    """성능 모니터링을 위한 평가 이력 로드"""
    try:
        # 메인 대시보드와 동일한 DB 경로 사용
        # 프로젝트 루트에서 data/db/evaluations.db로 경로 수정
        project_root = Path(__file__).parent.parent.parent.parent.parent
        db_path = project_root / "data" / "db" / "evaluations.db"
        
        if not db_path.exists():
            return []
        
        conn = sqlite3.connect(str(db_path))
        
        query = '''
            SELECT timestamp, faithfulness, answer_relevancy, 
                   context_recall, context_precision, ragas_score
            FROM evaluations 
            ORDER BY timestamp DESC
            LIMIT 50
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) == 0:
            return []
        
        # timestamp를 datetime으로 변환
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.to_dict('records')
        
    except Exception as e:
        st.error(f"데이터 로드 중 오류: {e}")
        return []

def show_evaluation_history_analysis(evaluation_history):
    """평가 이력 분석 (실제 데이터)"""
    st.subheader("📈 평가 실행 이력")
    
    if len(evaluation_history) < 2:
        st.info("📊 트렌드 분석을 위해 더 많은 평가 데이터가 필요합니다.")
        return
    
    df = pd.DataFrame(evaluation_history)
    
    # 기본 통계
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 평가 횟수", len(evaluation_history))
    
    with col2:
        days_span = (df['timestamp'].max() - df['timestamp'].min()).days
        st.metric("평가 기간", f"{days_span}일")
    
    with col3:
        avg_score = df['ragas_score'].mean()
        st.metric("평균 RAGAS 점수", f"{avg_score:.3f}")
    
    with col4:
        if days_span > 0:
            frequency = len(evaluation_history) / days_span
            st.metric("일평균 평가 횟수", f"{frequency:.1f}회")
        else:
            st.metric("일평균 평가 횟수", "계산불가")
    
    # 점수 추이 차트
    st.markdown("#### 📊 점수 추이")
    
    fig = go.Figure()
    
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision', 'ragas_score']
    colors = ['blue', 'green', 'orange', 'red', 'purple']
    
    for metric, color in zip(metrics, colors):
        if metric in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[metric],
                mode='lines+markers',
                name=metric.replace('_', ' ').title(),
                line=dict(color=color)
            ))
    
    fig.update_layout(
        title="평가 점수 시간별 추이",
        xaxis_title="시간",
        yaxis_title="점수",
        yaxis=dict(range=[0, 1]),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 최신 결과 요약
    if len(evaluation_history) > 0:
        latest = evaluation_history[0]
        st.markdown("#### 📋 최신 평가 결과")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**실행 시간**: {latest['timestamp']}")
            st.write(f"**RAGAS 점수**: {latest['ragas_score']:.3f}")
        
        with col2:
            st.write(f"**Faithfulness**: {latest['faithfulness']:.3f}")
            st.write(f"**Answer Relevancy**: {latest['answer_relevancy']:.3f}")

def show_api_usage_analysis(evaluation_history):
    """API 사용량 분석 (실제 데이터 기반)"""
    st.subheader("🔌 API 사용 현황")
    
    df = pd.DataFrame(evaluation_history)
    
    # 기본 추정치 (실제 데이터가 아닌 계산된 값)
    st.markdown("#### 📊 예상 API 사용량")
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_evaluations = len(evaluation_history)
        # RAGAS 평가당 평균 API 호출 추정
        estimated_llm_calls = total_evaluations * 8  # 평가당 약 8회 LLM 호출
        estimated_embedding_calls = total_evaluations * 4  # 평가당 약 4회 임베딩 호출
        
        st.metric("총 평가 횟수", total_evaluations)
        st.metric("예상 LLM API 호출", estimated_llm_calls)
        st.metric("예상 임베딩 API 호출", estimated_embedding_calls)
    
    with col2:
        # 현재 설정된 rate limit 정보
        st.markdown("**현재 API 설정:**")
        st.write("- Gemini LLM: 1000 RPM (Tier 1)")
        st.write("- Gemini Embeddings: 10 RPM (Tier 1)")
        st.write("- Temperature: 0.0 (평가 일관성)")
        
        # 예상 처리 시간
        if total_evaluations > 0:
            # 임베딩이 병목이므로 임베딩 기준으로 계산
            estimated_time = (estimated_embedding_calls * 60) / 10  # 10 RPM
            st.metric("예상 처리 시간", f"{estimated_time/60:.1f}분")
    
    # 사용량 추이 (실제 평가 횟수 기반)
    if len(df) > 1:
        st.markdown("#### 📈 평가 빈도 추이")
        
        # 일별 평가 횟수 계산
        df['date'] = df['timestamp'].dt.date
        daily_counts = df.groupby('date').size().reset_index(name='count')
        daily_counts['date'] = pd.to_datetime(daily_counts['date'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=daily_counts['date'],
            y=daily_counts['count'],
            name='일별 평가 횟수',
            marker_color='lightblue'
        ))
        
        fig.update_layout(
            title="일별 평가 실행 횟수",
            xaxis_title="날짜",
            yaxis_title="평가 횟수",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # API 최적화 팁
    st.markdown("#### 💡 API 사용 최적화 팁")
    
    optimization_tips = [
        "🎯 **배치 평가**: 여러 QA를 한 번에 평가하여 API 호출 최적화",
        "⏰ **Rate Limit 관리**: 현재 10 RPM 임베딩 제한이 주요 병목",
        "💰 **비용 추정**: 평가당 약 $0.01-0.05 예상 (모델 및 길이에 따라 변동)",
        "🔄 **재평가 방지**: 동일한 데이터셋 반복 평가 주의"
    ]
    
    for tip in optimization_tips:
        st.write(tip)

# 기존 모의 데이터 함수들 제거됨 - 실제 데이터만 사용