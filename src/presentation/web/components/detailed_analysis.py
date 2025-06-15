"""
상세 분석 컴포넌트 - 실제 평가 데이터 기반
실제로 평가된 QA 데이터만 표시하고 Historical 페이지와 연동
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import sqlite3
from pathlib import Path
from datetime import datetime


def get_db_path():
    """데이터베이스 경로 반환"""
    # 프로젝트 루트에서 data/db/evaluations.db로 경로 수정
    project_root = Path(__file__).parent.parent.parent.parent.parent
    return project_root / "data" / "db" / "evaluations.db"


def load_all_evaluations():
    """모든 평가 결과 로드 (Historical 페이지 연동용)"""
    try:
        db_path = get_db_path()
        if not db_path.exists():
            return []
        
        conn = sqlite3.connect(str(db_path))
        
        query = '''
            SELECT id, timestamp, faithfulness, answer_relevancy, 
                   context_recall, context_precision, ragas_score, raw_data
            FROM evaluations 
            ORDER BY timestamp DESC
        '''
        
        cursor = conn.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        evaluations = []
        for row in results:
            evaluation = {
                'id': row[0],
                'timestamp': row[1],
                'faithfulness': row[2],
                'answer_relevancy': row[3],
                'context_recall': row[4],
                'context_precision': row[5],
                'ragas_score': row[6],
                'raw_data': json.loads(row[7]) if row[7] else None
            }
            evaluations.append(evaluation)
        
        return evaluations
        
    except Exception as e:
        st.error(f"평가 결과 로드 중 오류: {e}")
        return []


def load_evaluation_by_id(evaluation_id):
    """특정 평가 ID로 평가 결과 로드"""
    try:
        db_path = get_db_path()
        if not db_path.exists():
            return None, []
        
        conn = sqlite3.connect(str(db_path))
        
        query = '''
            SELECT raw_data 
            FROM evaluations 
            WHERE id = ?
        '''
        
        result = conn.execute(query, (evaluation_id,)).fetchone()
        conn.close()
        
        if result and result[0]:
            raw_data = json.loads(result[0])
            individual_scores = raw_data.get('individual_scores', [])
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
            path = "/Users/isle/PycharmProjects/ragas-test/data/evaluation_data_variant1.json"
        else:
            path = "/Users/isle/PycharmProjects/ragas-test/data/evaluation_data.json"
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data[:qa_count]
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None

def load_actual_qa_data_from_dataset(dataset_name, qa_count):
    """데이터셋 파일에서 실제 QA 데이터 로드"""
    import os
    
    # 디버그: 현재 파일 위치 확인
    current_file = Path(__file__).resolve()
    print(f"[DEBUG] Current file: {current_file}")
    
    # 다양한 방법으로 project root 찾기
    # 방법 1: 현재 파일에서 상대 경로
    project_root = current_file.parent.parent.parent.parent
    
    # 방법 2: cwd에서 찾기  
    cwd = Path.cwd()
    if 'ragas-test' in cwd.parts:
        # cwd가 ragas-test 내부에 있으면
        idx = cwd.parts.index('ragas-test')
        project_root_alt = Path(*cwd.parts[:idx+1])
    else:
        project_root_alt = cwd
    
    # 방법 3: 절대 경로 사용 (하드코딩)
    absolute_data_paths = [
        Path("/Users/isle/PycharmProjects/ragas-test/data") / dataset_name,
        Path("/Users/isle/PycharmProjects/ragas-test/data/evaluation_data.json"),
        Path("/Users/isle/PycharmProjects/ragas-test/data/evaluation_data_variant1.json")
    ]
    
    print(f"[DEBUG] Project root (method 1): {project_root}")
    print(f"[DEBUG] Project root (method 2): {project_root_alt}")
    print(f"[DEBUG] Current working directory: {cwd}")
    
    # 모든 가능한 경로 조합
    all_possible_paths = []
    
    # 각 project root 방법에 대해
    for root in [project_root, project_root_alt]:
        all_possible_paths.extend([
            root / "data" / dataset_name,
            root / "data" / "evaluation_data.json",
            root / "data" / "evaluation_data_variant1.json"
        ])
    
    # 절대 경로 추가
    all_possible_paths.extend(absolute_data_paths)
    
    # 중복 제거
    unique_paths = list(dict.fromkeys(all_possible_paths))
    
    print(f"[DEBUG] Looking for dataset: {dataset_name}")
    print(f"[DEBUG] QA count requested: {qa_count}")
    print(f"[DEBUG] Checking {len(unique_paths)} unique paths")
    
    # 모든 경로 시도
    for i, path in enumerate(unique_paths):
        print(f"[DEBUG] Checking path {i+1}: {path}")
        
        try:
            if path.exists() and path.is_file():
                print(f"[DEBUG] Found file at: {path}")
                with open(path, "r", encoding="utf-8") as f:
                    all_qa_data = json.load(f)
                
                print(f"[DEBUG] Successfully loaded JSON from {path}")
                print(f"[DEBUG] Total QA items in file: {len(all_qa_data) if isinstance(all_qa_data, list) else 'Not a list'}")
                
                if isinstance(all_qa_data, list) and len(all_qa_data) > 0:
                    # qa_count만큼만 반환 (실제 평가된 개수)
                    result = all_qa_data[:qa_count]
                    print(f"[DEBUG] Returning {len(result)} QA items")
                    print(f"[DEBUG] First QA item preview: {result[0].get('question', 'No question')[:50] if result else 'No data'}")
                    return result
                else:
                    print(f"[DEBUG] File loaded but invalid format or empty")
                    
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON decode error for {path}: {e}")
        except Exception as e:
            print(f"[DEBUG] Error with {path}: {type(e).__name__}: {e}")
    
    # 모든 경로에서 찾지 못한 경우
    print("[DEBUG] Failed to load QA data from any path")
    print(f"[DEBUG] Final attempt: listing files in likely directories...")
    
    # 마지막 시도: 가능한 data 디렉토리 내용 표시
    for root in [project_root, project_root_alt, Path("/Users/isle/PycharmProjects/ragas-test")]:
        data_dir = root / "data"
        if data_dir.exists():
            print(f"[DEBUG] Found data dir at: {data_dir}")
            print(f"[DEBUG] Contents: {list(data_dir.iterdir())}")
    
    return None


def get_actual_qa_data_from_evaluation(raw_data, evaluation_db_id):
    """평가 결과에서 실제 사용된 QA 데이터 추출"""
    if not raw_data:
        return None
    
    # raw_data에서 실제 평가에 사용된 QA 데이터 찾기
    metadata = raw_data.get('metadata', {})
    
    # individual_scores의 개수가 실제 평가된 QA 개수
    individual_scores = raw_data.get('individual_scores', [])
    actual_qa_count = len(individual_scores)
    
    # 메타데이터에서 정보 추출, 없으면 DB ID 사용
    evaluation_id = metadata.get('evaluation_id', f"DB#{evaluation_db_id}")
    model_info = metadata.get('model', 'Gemini-2.5-Flash')
    dataset_info = metadata.get('dataset', 'evaluation_data.json')
    
    # 데이터셋에서 파일명만 추출
    if '/' in dataset_info:
        dataset_name = dataset_info.split('/')[-1]
    else:
        dataset_name = dataset_info
    
    # 실제 QA 데이터 로드 - 간단한 버전 사용
    actual_qa_data = load_actual_qa_data_from_dataset_simple(dataset_name, actual_qa_count)
    
    return {
        'qa_count': actual_qa_count,
        'dataset_size': metadata.get('dataset_size', actual_qa_count),
        'evaluation_id': evaluation_id,
        'timestamp': metadata.get('timestamp', 'unknown'),
        'model': model_info,
        'dataset': dataset_name,
        'qa_data': actual_qa_data
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
        timestamp = eval_data['timestamp']
        qa_count = 0
        if eval_data['raw_data'] and eval_data['raw_data'].get('individual_scores'):
            qa_count = len(eval_data['raw_data']['individual_scores'])
        
        # timestamp를 더 읽기 쉬운 형태로 변환
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
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
        key="evaluation_selector"
    )
    
    # 선택된 평가 데이터 로드
    selected_evaluation = all_evaluations[selected_eval_idx]
    evaluation_id = selected_evaluation['id']
    
    # 선택된 평가의 상세 데이터 로드
    raw_data, individual_scores = load_evaluation_by_id(evaluation_id)
    
    if not raw_data:
        st.error(f"❌ 평가 ID {evaluation_id}의 상세 데이터를 로드할 수 없습니다.")
        return
    
    # 실제 평가된 QA 데이터 정보
    qa_info = get_actual_qa_data_from_evaluation(raw_data, evaluation_id)
    
    if not qa_info or qa_info['qa_count'] == 0:
        st.error("❌ 이 평가에는 개별 QA 데이터가 없습니다.")
        return
    
    # 평가 정보 표시
    st.success(f"✅ 평가 #{evaluation_id} 로드 완료")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("QA 개수", qa_info['qa_count'])
    with col2:
        st.metric("평가 ID", qa_info['evaluation_id'])
    with col3:
        st.metric("모델", qa_info['model'])
    with col4:
        st.metric("데이터셋", qa_info['dataset'])
    with col5:
        ragas_score = selected_evaluation.get('ragas_score', 0)
        st.metric("RAGAS 점수", f"{ragas_score:.3f}")
    
    # 개별 점수가 있는 경우에만 분석 진행
    if not individual_scores:
        st.warning("⚠️ 이 평가에는 개별 QA 점수가 없습니다.")
        show_overall_metrics_only(selected_evaluation)
        return
    
    # 탭으로 구분
    tab1, tab2, tab3 = st.tabs(["📊 QA 개별 분석", "📈 메트릭 분포", "🎯 패턴 분석"])
    
    with tab1:
        # 디버그: qa_info 상태 확인
        if qa_info and 'qa_data' in qa_info:
            if qa_info['qa_data']:
                st.info(f"📊 QA 데이터 상태: 로드됨 ({len(qa_info['qa_data'])}개)")
            else:
                st.warning("📊 QA 데이터 상태: 비어있음")
                # 터미널 출력 확인 안내
                st.info("💡 터미널에서 디버그 로그를 확인하세요.")
        show_qa_analysis_actual(individual_scores, evaluation_id, qa_info.get('qa_data'))
    
    with tab2:
        show_metric_distribution_actual(individual_scores, selected_evaluation)
    
    with tab3:
        show_pattern_analysis_actual(individual_scores, selected_evaluation)


def show_overall_metrics_only(evaluation_data):
    """개별 점수가 없을 때 전체 메트릭만 표시"""
    st.subheader("📊 전체 평가 결과")
    
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
    col1, col2, col3, col4 = st.columns(4)
    
    for i, metric in enumerate(metrics):
        with [col1, col2, col3, col4][i]:
            score = evaluation_data.get(metric, 0)
            st.metric(
                label=metric.replace('_', ' ').title(),
                value=f"{score:.3f}"
            )


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
            st.markdown("""
            **가능한 원인:**
            1. 평가 데이터 파일이 `/Users/isle/PycharmProjects/ragas-test/data/` 경로에 없음
            2. 파일 이름이 `evaluation_data.json` 또는 `evaluation_data_variant1.json`이 아님
            3. 파일 권한 문제
            
            **해결 방법:**
            - 터미널에서 `ls -la /Users/isle/PycharmProjects/ragas-test/data/` 명령으로 파일 확인
            - 필요한 경우 파일 권한 수정: `chmod 644 /Users/isle/PycharmProjects/ragas-test/data/*.json`
            - 터미널에서 [DEBUG] 로그를 확인하여 정확한 오류 위치 파악
            """)
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
            avg_score = sum(qa_score.values()) / len(qa_score) if qa_score.values() else 0
        
        # 질문 내용 미리보기 추가
        question_preview = "질문 정보 없음"
        if qa_data and i < len(qa_data):
            question = qa_data[i].get('question', '')
            if question:
                # 질문 길이에 따라 동적으로 처리
                if len(question) > 50:
                    question_preview = question[:47] + "..."
                else:
                    question_preview = question
        
        qa_options.append(f"QA #{i+1}: {question_preview} (평균: {avg_score:.3f})")
    
    selected_qa_idx = st.selectbox(
        "분석할 QA 선택", 
        range(len(qa_options)), 
        format_func=lambda x: qa_options[x]
    )
    
    if selected_qa_idx is not None and selected_qa_idx < len(individual_scores):
        qa_scores = individual_scores[selected_qa_idx]
        qa_content = qa_data[selected_qa_idx] if qa_data and selected_qa_idx < len(qa_data) else None
        show_individual_qa_details_actual(selected_qa_idx + 1, qa_scores, evaluation_id, qa_content)


def show_individual_qa_details_actual(qa_number, qa_scores, evaluation_id, qa_content=None):
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
            st.info(qa_content.get('question', '질문 정보 없음'))
            
            st.markdown("**💡 생성된 답변:**")
            st.success(qa_content.get('answer', '답변 정보 없음'))
        
        with col2:
            st.markdown("**📚 제공된 컨텍스트:**")
            contexts = qa_content.get('contexts', [])
            for i, context in enumerate(contexts, 1):
                with st.expander(f"컨텍스트 {i}"):
                    st.text(context)
            
            st.markdown("**✅ 정답 (Ground Truth):**")
            st.info(qa_content.get('ground_truth', '정답 정보 없음'))
        
        st.markdown("---")
    
    # 점수 카드 표시
    st.markdown("#### 📊 평가 점수")
    
    score_cols = st.columns(4)
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
    
    for i, metric in enumerate(metrics):
        with score_cols[i]:
            score = qa_scores.get(metric, 0)
            color = "green" if score >= 0.8 else "orange" if score >= 0.6 else "red"
            st.metric(
                label=metric.replace('_', ' ').title(),
                value=f"{score:.3f}"
            )
    
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


def show_evaluation_reasoning_actual(qa_number, scores, qa_content=None):
    """실제 평가 점수 기반 평가 근거"""
    st.markdown("#### 🧠 평가 근거")
    
    # QA 내용 요약 표시 (평가 근거에서 참고용)
    if qa_content:
        st.info(f"**참고:** 이 분석은 '{qa_content.get('question', '')[:50]}...' 질문에 대한 평가입니다.")
    
    # 각 메트릭별 분석
    metrics_analysis = {
        'faithfulness': {
            'description': '답변이 제공된 컨텍스트에 얼마나 충실한지 측정',
            'score': scores.get('faithfulness', 0),
            'analysis': generate_faithfulness_analysis_actual(scores.get('faithfulness', 0))
        },
        'answer_relevancy': {
            'description': '답변이 질문과 얼마나 관련이 있는지 측정',
            'score': scores.get('answer_relevancy', 0),
            'analysis': generate_relevancy_analysis_actual(scores.get('answer_relevancy', 0))
        },
        'context_recall': {
            'description': 'Ground truth의 정보가 컨텍스트에서 얼마나 발견되는지 측정',
            'score': scores.get('context_recall', 0),
            'analysis': generate_recall_analysis_actual(scores.get('context_recall', 0))
        },
        'context_precision': {
            'description': '검색된 컨텍스트가 질문과 얼마나 관련이 있는지 측정',
            'score': scores.get('context_precision', 0),
            'analysis': generate_precision_analysis_actual(scores.get('context_precision', 0))
        }
    }
    
    for metric, info in metrics_analysis.items():
        with st.expander(f"📝 {metric.replace('_', ' ').title()} 분석 (점수: {info['score']:.3f})"):
            st.markdown(f"**설명:** {info['description']}")
            
            # 마크다운 렌더링을 위해 텍스트를 직접 표시
            analysis_lines = info['analysis'].split('\n')
            for line in analysis_lines:
                if line.strip():
                    st.markdown(line)
            
            # 점수 구간별 해석 가이드
            st.markdown("---")
            st.markdown("**점수 해석:**")
            if info['score'] >= 0.9:
                st.success("🌟 우수 (0.9+): 매우 높은 성능")
            elif info['score'] >= 0.8:
                st.success("✅ 양호 (0.8-0.9): 좋은 성능")
            elif info['score'] >= 0.6:
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
        technical_details = "컨텍스트 내용과 답변 간 일치도가 90% 이상으로, 신뢰할 수 있는 답변입니다."
        
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
        technical_details = f"컨텍스트 일치도: {score:.1%}. 시스템이 제대로 작동하지 않고 있습니다."
    
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
        technical_details = f"질문-답변 관련성: {score:.1%}. 약간의 여분 정보가 포함되었습니다."
        
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
        technical_details = f"질문-답변 관련성: {score:.1%}. 질문 의도 파악에 중대한 오류가 있습니다."
        
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
        technical_details = f"질문-답변 관련성: {score:.1%}. 시스템이 질문을 이해하지 못하고 있습니다."
    
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
        technical_details = f"정보 검색 완성도: {score:.1%}. 필요한 정보가 모두 수집되었습니다."
        
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
        technical_details = f"정보 검색 완성도: {score:.1%}. 대부분의 중요 정보가 수집되었습니다."
        
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
        technical_details = f"정보 검색 완성도: {score:.1%}. 검색 시스템 전체가 기능하지 않고 있습니다."
    
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
        technical_details = f"검색 정확도: {score:.1%}. 거의 모든 컨텍스트가 관련성이 높습니다."
        
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
        technical_details = f"검색 정확도: {score:.1%}. 소량의 부가 정보가 포함되었습니다."
        
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
        technical_details = f"검색 정확도: {score:.1%}. 상당량의 무관한 정보가 포함되었습니다."
        
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
        technical_details = f"검색 정확도: {score:.1%}. 검색 시스템이 올바르게 작동하지 않고 있습니다."
    
    return f"{base_analysis}\n\n{improvement_tips}\n\n**📊 기술적 분석:** {technical_details}"


def show_metric_distribution_actual(individual_scores, evaluation_data):
    """실제 평가된 데이터의 메트릭 분포"""
    st.subheader("📊 메트릭 분포 분석")
    
    if not individual_scores:
        st.warning("개별 점수 데이터가 없습니다.")
        return
    
    # DataFrame 생성
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
    data = {'QA': [f'Q{i+1}' for i in range(len(individual_scores))]}
    
    for metric in metrics:
        data[metric] = [score.get(metric, 0) for score in individual_scores]
    
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
        title="실제 평가된 QA별 메트릭 성능",
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


def show_pattern_analysis_actual(individual_scores, evaluation_data):
    """실제 평가 데이터의 패턴 분석"""
    st.subheader("🎯 성능 패턴 분석")
    
    qa_count = len(individual_scores)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📝 평가 개요")
        st.metric("실제 평가된 QA 개수", qa_count)
        
        # 평가 시간
        timestamp = evaluation_data.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y년 %m월 %d일 %H:%M')
                st.text(f"평가 시간: {formatted_time}")
            except:
                st.text(f"평가 시간: {timestamp}")
    
    with col2:
        st.markdown("#### 📊 성능 요약")
        ragas_score = evaluation_data.get('ragas_score', 0)
        st.metric("전체 RAGAS 점수", f"{ragas_score:.3f}")
        
        # 최고/최저 메트릭
        metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
        scores = {m: evaluation_data.get(m, 0) for m in metrics}
        
        if scores:
            best_metric = max(scores, key=scores.get)
            worst_metric = min(scores, key=scores.get)
            
            st.text(f"최고 성능: {best_metric.replace('_', ' ').title()} ({scores[best_metric]:.3f})")
            st.text(f"개선 필요: {worst_metric.replace('_', ' ').title()} ({scores[worst_metric]:.3f})")
    
    # 개선 제안
    st.markdown("#### 💡 이 평가에 대한 개선 제안")
    
    suggestions = []
    
    if evaluation_data.get('faithfulness', 0) < 0.7:
        suggestions.append("🎯 Faithfulness 개선: 컨텍스트 충실도 강화, 환각 방지 프롬프트 사용")
    
    if evaluation_data.get('answer_relevancy', 0) < 0.7:
        suggestions.append("🎯 Answer Relevancy 개선: 질문 의도 파악 강화, 간결한 답변 생성")
    
    if evaluation_data.get('context_recall', 0) < 0.7:
        suggestions.append("🎯 Context Recall 개선: 검색 범위 확대, 다양한 검색 전략 활용")
    
    if evaluation_data.get('context_precision', 0) < 0.7:
        suggestions.append("🎯 Context Precision 개선: 무관한 컨텍스트 필터링, 검색 정확도 향상")
    
    if not suggestions:
        suggestions.append("✅ 모든 메트릭이 양호한 수준입니다! 현재 설정을 유지하세요.")
    
    for suggestion in suggestions:
        st.info(suggestion)


# Historical 페이지와의 연동을 위한 함수
def set_selected_evaluation(evaluation_id):
    """Historical 페이지에서 특정 평가를 선택했을 때 호출"""
    all_evaluations = load_all_evaluations()
    for i, eval_data in enumerate(all_evaluations):
        if eval_data['id'] == evaluation_id:
            st.session_state.selected_evaluation_index = i
            break