"""
RAGAS 평가 결과 대시보드
직관적이고 비교 가능한 시각화 제공
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.application.services import EvaluationService
from src.infrastructure.llm.gemini_adapter import GeminiAdapter
from src.infrastructure.repository.file_adapter import FileRepositoryAdapter
from src.infrastructure.ragas_eval import RagasEvalAdapter

# 대시보드 컴포넌트
try:
    from dashboard.components.detailed_analysis import show_detailed_analysis as show_detailed_component
except ImportError:
    # 개발 환경에서 직접 실행할 때 대비
    sys.path.append(str(project_root / "dashboard"))
    from components.detailed_analysis import show_detailed_analysis as show_detailed_component

# 페이지 설정
st.set_page_config(
    page_title="RAGAS 평가 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 네비게이션
st.sidebar.title("📊 RAGAS 대시보드")
page = st.sidebar.selectbox(
    "페이지 선택",
    ["🎯 Overview", "📈 Historical", "🔍 Detailed Analysis", "⚡ Performance"]
)

# 메인 타이틀
st.title("🎯 RAGAS 평가 결과 대시보드")
st.markdown("---")

def main():
    if page == "🎯 Overview":
        show_overview()
    elif page == "📈 Historical":
        show_historical()
    elif page == "🔍 Detailed Analysis":
        show_detailed_analysis()
    elif page == "⚡ Performance":
        show_performance()

def show_overview():
    """메인 오버뷰 대시보드"""
    st.header("📊 평가 결과 개요")
    
    # 새 평가 실행 버튼
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚀 새 평가 실행", type="primary"):
            run_new_evaluation()
    
    with col2:
        if st.button("🔄 결과 새로고침"):
            st.rerun()
    
    # 최신 평가 결과 로드
    latest_result = load_latest_result()
    
    if latest_result:
        show_metric_cards(latest_result)
        show_metric_charts(latest_result)
        show_recent_trends()
    else:
        st.info("📝 아직 평가 결과가 없습니다. '새 평가 실행' 버튼을 클릭하여 첫 평가를 시작하세요!")

def show_metric_cards(result):
    """메트릭 카드 표시"""
    st.subheader("🎯 핵심 지표")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    metrics = [
        ("종합 점수", result.get('ragas_score', 0), "🏆"),
        ("Faithfulness", result.get('faithfulness', 0), "✅"),
        ("Answer Relevancy", result.get('answer_relevancy', 0), "🎯"),
        ("Context Recall", result.get('context_recall', 0), "🔄"),
        ("Context Precision", result.get('context_precision', 0), "📍")
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
            
            st.metric(
                label=f"{icon} {name}",
                value=f"{value:.3f}",
                delta=f"{(value-0.5):.3f}" if value > 0 else None
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
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
    values = [result.get(metric, 0) for metric in metrics]
    labels = ['Faithfulness', 'Answer Relevancy', 'Context Recall', 'Context Precision']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],  # 첫 번째 값을 마지막에 추가하여 차트를 닫음
        theta=labels + [labels[0]],
        fill='toself',
        name='RAGAS 점수',
        line_color='rgb(32, 201, 151)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=True,
        title="📊 메트릭 균형도",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_bar_chart(result):
    """바 차트 생성"""
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
    values = [result.get(metric, 0) for metric in metrics]
    labels = ['Faithfulness', 'Answer Relevancy', 'Context Recall', 'Context Precision']
    
    # 색상 매핑
    colors = ['green' if v >= 0.8 else 'orange' if v >= 0.6 else 'red' for v in values]
    
    fig = go.Figure(data=[
        go.Bar(x=labels, y=values, marker_color=colors)
    ])
    
    fig.update_layout(
        title="📊 메트릭별 성능",
        yaxis_title="점수",
        yaxis=dict(range=[0, 1]),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_recent_trends():
    """최근 트렌드 표시"""
    st.subheader("📈 최근 트렌드")
    
    # 히스토리 데이터 로드
    history = load_evaluation_history(limit=10)
    
    if len(history) > 1:
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 트렌드 차트
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
            title="📈 평가 점수 트렌드",
            xaxis_title="시간",
            yaxis_title="점수",
            yaxis=dict(range=[0, 1]),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 트렌드 표시를 위해 더 많은 평가 데이터가 필요합니다.")

def run_new_evaluation():
    """새로운 평가 실행"""
    with st.spinner("🔄 평가를 실행 중입니다..."):
        try:
            # 기존 평가 서비스 활용
            llm_adapter = GeminiAdapter(
                model_name="gemini-2.5-flash-preview-05-20", 
                requests_per_minute=1000
            )
            
            repository_adapter = FileRepositoryAdapter(
                file_path="data/evaluation_data.json"
            )
            
            ragas_eval_adapter = RagasEvalAdapter()
            
            evaluation_service = EvaluationService(
                llm_port=llm_adapter,
                repository_port=repository_adapter,
                evaluation_runner=ragas_eval_adapter,
            )
            
            # 평가 실행
            result = evaluation_service.run_evaluation()
            
            # 결과 저장
            save_evaluation_result(result)
            
            st.success("✅ 평가가 완료되었습니다!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 평가 중 오류 발생: {str(e)}")

def show_historical():
    """히스토리 페이지"""
    st.header("📈 평가 이력")
    
    history = load_evaluation_history()
    
    if history:
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 테이블 표시
        st.subheader("📋 평가 이력 테이블")
        st.dataframe(df, use_container_width=True)
        
        # 상세 비교 차트
        st.subheader("📊 상세 비교")
        
        if len(df) > 1:
            # 사용자가 비교할 평가 선택
            col1, col2 = st.columns(2)
            
            with col1:
                eval1_idx = st.selectbox("첫 번째 평가", range(len(df)), format_func=lambda x: f"{df.iloc[x]['timestamp']} (ID: {x})")
            
            with col2:
                eval2_idx = st.selectbox("두 번째 평가", range(len(df)), index=min(1, len(df)-1), format_func=lambda x: f"{df.iloc[x]['timestamp']} (ID: {x})")
            
            if eval1_idx != eval2_idx:
                show_comparison_chart(df.iloc[eval1_idx], df.iloc[eval2_idx])
        
    else:
        st.info("📝 아직 평가 이력이 없습니다.")

def show_comparison_chart(eval1, eval2):
    """두 평가 결과 비교 차트"""
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision', 'ragas_score']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name=f'평가 1 ({eval1["timestamp"]})',
        x=metrics,
        y=[eval1.get(m, 0) for m in metrics],
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name=f'평가 2 ({eval2["timestamp"]})',
        x=metrics,
        y=[eval2.get(m, 0) for m in metrics],
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title="📊 평가 결과 비교",
        barmode='group',
        yaxis=dict(range=[0, 1]),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_detailed_analysis():
    """상세 분석 페이지"""
    show_detailed_component()

def show_performance():
    """성능 모니터링 페이지"""
    st.header("⚡ 성능 모니터링")
    st.info("🚧 성능 모니터링 기능은 곧 추가될 예정입니다.")

# 데이터 저장/로드 함수들
def get_db_path():
    """데이터베이스 경로 반환"""
    return project_root / "dashboard" / "evaluations.db"

def init_db():
    """데이터베이스 초기화"""
    db_path = get_db_path()
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute('''
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
    ''')
    
    conn.commit()
    conn.close()

def save_evaluation_result(result):
    """평가 결과 저장"""
    init_db()
    
    conn = sqlite3.connect(str(get_db_path()))
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO evaluations (
            timestamp, faithfulness, answer_relevancy, 
            context_recall, context_precision, ragas_score, raw_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        result.get('faithfulness', 0),
        result.get('answer_relevancy', 0),
        result.get('context_recall', 0),
        result.get('context_precision', 0),
        result.get('ragas_score', 0),
        json.dumps(result)
    ))
    
    conn.commit()
    conn.close()

def load_latest_result():
    """최신 평가 결과 로드"""
    history = load_evaluation_history(limit=1)
    return history[0] if history else None

def load_evaluation_history(limit=None):
    """평가 이력 로드"""
    init_db()
    
    conn = sqlite3.connect(str(get_db_path()))
    
    query = '''
        SELECT timestamp, faithfulness, answer_relevancy, 
               context_recall, context_precision, ragas_score
        FROM evaluations 
        ORDER BY timestamp DESC
    '''
    
    if limit:
        query += f" LIMIT {limit}"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df.to_dict('records')

if __name__ == "__main__":
    main()