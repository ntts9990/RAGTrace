"""
메트릭 설명 컴포넌트
RAGAS 평가 지표에 대한 직관적이고 쉬운 설명 제공
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def show_metrics_explanation():
    """메트릭 설명 메인 화면"""
    st.header("📚 RAGAS 평가 지표 완전 가이드")
    
    st.markdown("""
    🎯 **RAG 시스템의 성능을 정확히 평가하는 4가지 핵심 지표**
    
    RAG(Retrieval-Augmented Generation) 시스템이 얼마나 잘 작동하는지 측정하는 
    네 가지 중요한 점수입니다. 각 지표는 서로 다른 측면을 평가합니다.
    """)
    
    # 한눈에 보는 요약
    show_quick_summary()
    
    # 탭으로 구분된 상세 설명
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✅ Faithfulness", "🎯 Answer Relevancy", 
        "🔄 Context Recall", "📍 Context Precision", "💡 실전 가이드"
    ])
    
    with tab1:
        show_faithfulness_explanation()
    
    with tab2:
        show_answer_relevancy_explanation()
    
    with tab3:
        show_context_recall_explanation()
    
    with tab4:
        show_context_precision_explanation()
    
    with tab5:
        show_practical_guide()

def show_quick_summary():
    """한눈에 보는 요약"""
    st.markdown("### 🚀 한눈에 보는 요약")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        #### ✅ **Faithfulness**
        **🔍 답변이 거짓말을 하지 않는가?**
        - 제공된 정보만 사용했는가
        - 지어낸 내용이 없는가
        - **목표**: 1.0 (완벽)
        """)
    
    with col2:
        st.markdown("""
        #### 🎯 **Answer Relevancy**
        **💬 질문에 정확히 답했는가?**
        - 질문과 관련이 있는가
        - 불필요한 설명이 없는가
        - **목표**: 0.8 이상
        """)
    
    with col3:
        st.markdown("""
        #### 🔄 **Context Recall**
        **📚 필요한 정보를 모두 찾았는가?**
        - 정답에 필요한 모든 정보
        - 검색이 충분했는가
        - **목표**: 0.9 이상
        """)
    
    with col4:
        st.markdown("""
        #### 📍 **Context Precision**
        **🗂️ 불필요한 정보는 없는가?**
        - 관련 있는 정보만 제공
        - 노이즈가 적은가
        - **목표**: 0.8 이상
        """)
    
    # 시각적 요약
    show_metrics_overview_chart()

def show_metrics_overview_chart():
    """메트릭 개요 차트 - 깔끔하고 직관적인 디자인"""
    st.markdown("#### 📊 RAG 시스템과 RAGAS 메트릭")
    
    # Streamlit 네이티브 컴포넌트로 깔끔한 프로세스 플로우
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 1단계: 질문 입력
        st.markdown("#### 🤔 1단계: 질문 입력")
        st.info("사용자가 질문을 합니다")
        
        # 화살표
        st.markdown("<div style='text-align: center; font-size: 30px; margin: 10px 0;'>⬇️</div>", unsafe_allow_html=True)
        
        # 2단계: 컨텍스트 검색
        st.markdown("#### 🔍 2단계: 컨텍스트 검색")
        st.success("관련 문서들을 검색합니다")
        
        with st.container():
            st.markdown("**평가되는 메트릭:**")
            st.markdown("🟠 **Context Precision**: 검색된 문서가 얼마나 관련있는가?")
            st.markdown("🟣 **Context Recall**: 필요한 문서를 모두 찾았는가?")
        
        # 화살표
        st.markdown("<div style='text-align: center; font-size: 30px; margin: 10px 0;'>⬇️</div>", unsafe_allow_html=True)
        
        # 3단계: 답변 생성
        st.markdown("#### 🤖 3단계: 답변 생성")
        st.warning("AI가 검색된 문서를 바탕으로 답변을 생성합니다")
        
        with st.container():
            st.markdown("**평가되는 메트릭:**")
            st.markdown("🔴 **Faithfulness**: 답변이 문서 내용에 충실한가?")
            st.markdown("🟢 **Answer Relevancy**: 질문에 정확히 답했는가?")
        
        # 화살표
        st.markdown("<div style='text-align: center; font-size: 30px; margin: 10px 0;'>⬇️</div>", unsafe_allow_html=True)
        
        # 4단계: 품질 평가
        st.markdown("#### ✅ 4단계: 품질 평가")
        st.error("RAGAS가 답변의 품질을 종합 평가합니다")
    
    # 메트릭 중요도 차트
    st.markdown("#### 🎯 메트릭별 중요도와 특징")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # RAGAS 논문 기반 메트릭 특성
        st.markdown("##### 📚 RAGAS 논문 기반 메트릭 특성")
        
        ragas_characteristics = {
            '메트릭': ['Faithfulness', 'Context Recall', 'Answer Relevancy', 'Context Precision'],
            '측정 방식': ['LLM 기반 검증', '정보 완성도', '의미적 유사도', '검색 정확도'],
            '계산 복잡도': ['높음', '중간', '낮음', '낮음'],
            '신뢰도': ['매우 높음', '높음', '중간', '높음']
        }
        
        df_characteristics = pd.DataFrame(ragas_characteristics)
        st.dataframe(df_characteristics, use_container_width=True, hide_index=True)
        
        st.markdown("""
        **📖 RAGAS 설계 원칙:**
        - Faithfulness: 환각 방지가 최우선
        - Context Recall: 정보 누락 최소화
        - Answer Relevancy: 사용자 만족도 직결
        - Context Precision: 효율성과 속도 최적화
        """)
    
    with col2:
        # RAGAS 논문의 실제 성능 기준
        st.markdown("##### 🎯 RAGAS 논문 권장 기준점")
        
        performance_standards = pd.DataFrame({
            '메트릭': ['Faithfulness', 'Context Recall', 'Answer Relevancy', 'Context Precision'],
            '프로덕션 수준': ['0.9+', '0.9+', '0.8+', '0.8+'],
            '개선 권장': ['0.8-0.9', '0.7-0.9', '0.6-0.8', '0.6-0.8'],
            '즉시 개선 필요': ['<0.8', '<0.7', '<0.6', '<0.6']
        })
        
        st.dataframe(performance_standards, use_container_width=True, hide_index=True)
        
        st.markdown("""
        **⚡ 실제 RAG 시스템 개발 경험:**
        - Faithfulness 0.9+ 달성이 가장 어려움
        - Context Precision은 상대적으로 빠른 개선 가능
        - Answer Relevancy는 프롬프트 개선으로 즉시 향상
        - Context Recall은 검색 시스템 아키텍처에 의존적
        """)

def show_faithfulness_explanation():
    """Faithfulness 상세 설명"""
    st.markdown("## ✅ Faithfulness (충실성)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🤔 **이게 뭔가요?**
        
        **"AI가 거짓말을 하지 않았나요?"**를 측정하는 지표입니다.
        
        AI가 답변을 만들 때, 제공된 문서(컨텍스트)에 없는 내용을 지어내지 않고 
        정확히 문서의 내용만 사용했는지를 확인합니다.
        
        ### 📝 **구체적인 예시**
        
        **질문**: "우리 회사의 휴가 정책은 무엇인가요?"
        
        **제공된 문서**: "직원은 연간 15일의 유급휴가를 사용할 수 있습니다."
        
        ✅ **좋은 답변 (Faithfulness = 1.0)**:
        "직원은 연간 15일의 유급휴가를 사용할 수 있습니다."
        
        ❌ **나쁜 답변 (Faithfulness = 0.3)**:
        "직원은 연간 15일의 유급휴가를 사용할 수 있으며, 병가는 10일까지 가능합니다."
        → 병가 정보는 문서에 없는데 지어냈습니다!
        """)
    
    with col2:
        # 점수 게이지
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = 1.0,
            title = {'text': "Faithfulness 점수"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 1]},
                'bar': {'color': "green"},
                'steps': [
                    {'range': [0, 0.7], 'color': "lightgray"},
                    {'range': [0.7, 0.9], 'color': "yellow"},
                    {'range': [0.9, 1], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0.95
                }
            }
        ))
        
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        ### 🎯 **목표 점수**
        - **1.0**: 완벽 (환각 없음)
        - **0.9+**: 우수
        - **0.8+**: 양호
        - **0.7-**: 개선 필요
        """)
    
    st.markdown("""
    ### 🔧 **개선 방법**
    
    1. **프롬프트 개선**
       - "제공된 문서의 정보만 사용하세요"
       - "모르는 내용은 '모르겠습니다'라고 답하세요"
    
    2. **모델 설정**
       - Temperature를 낮춰서 (0.1-0.3) 창의성 줄이기
       - 더 신뢰할 수 있는 모델 사용
    
    3. **후처리**
       - 답변에서 문서에 없는 내용 자동 제거
       - 출처 표시 기능 추가
    """)

def show_answer_relevancy_explanation():
    """Answer Relevancy 상세 설명"""
    st.markdown("## 🎯 Answer Relevancy (답변 관련성)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🤔 **이게 뭔가요?**
        
        **"질문에 정확히 답했나요?"**를 측정하는 지표입니다.
        
        질문자가 원하는 답을 정확히 주었는지, 불필요한 설명이나 
        관련 없는 내용은 없는지를 확인합니다.
        
        ### 📝 **구체적인 예시**
        
        **질문**: "파이썬에서 리스트를 정렬하는 방법은?"
        
        ✅ **좋은 답변 (Relevancy = 0.95)**:
        "파이썬에서 리스트를 정렬하려면 sort() 메서드나 sorted() 함수를 사용하세요."
        
        ⚠️ **보통 답변 (Relevancy = 0.75)**:
        "파이썬에서 리스트를 정렬하려면 sort() 메서드를 사용하세요. 파이썬은 1991년에 만들어진 프로그래밍 언어로..."
        → 파이썬 역사는 질문과 관련이 없습니다!
        
        ❌ **나쁜 답변 (Relevancy = 0.3)**:
        "프로그래밍에는 다양한 언어가 있습니다. Java, C++, Python 등이 있죠..."
        → 질문에 전혀 답하지 않았습니다!
        """)
    
    with col2:
        # 관련성 차트
        categories = ['질문 의도 파악', '직접적 답변', '간결성', '완성도']
        scores = [0.9, 0.8, 0.7, 0.9]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name='Answer Relevancy',
            line_color='rgb(32, 201, 151)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=False,
            title="관련성 구성 요소",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    ### 🎯 **평가 기준**
    
    1. **질문 의도 파악** (30%): 질문자가 정말 원하는 게 뭔지 이해했나?
    2. **직접적 답변** (40%): 질문에 바로 답했나?
    3. **간결성** (20%): 불필요한 내용은 없나?
    4. **완성도** (10%): 답변이 충분한가?
    
    ### 🔧 **개선 방법**
    
    1. **질문 분석 강화**
       - 질문의 핵심 키워드 식별
       - 질문 유형 분류 (정의, 방법, 이유 등)
    
    2. **답변 구조화**
       - 핵심 답변을 먼저
       - 부연설명은 나중에 또는 별도 구분
    
    3. **답변 검증**
       - "이 답변이 질문에 직접 답하는가?" 체크
       - 불필요한 부분 제거
    """)

def show_context_recall_explanation():
    """Context Recall 상세 설명"""
    st.markdown("## 🔄 Context Recall (컨텍스트 재현율)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🤔 **이게 뭔가요?**
        
        **"필요한 정보를 모두 찾았나요?"**를 측정하는 지표입니다.
        
        정답을 만들기 위해 필요한 모든 정보가 검색된 문서들 안에 
        포함되어 있는지를 확인합니다. 즉, 검색이 얼마나 완전했는지를 평가합니다.
        
        ### 📝 **구체적인 예시**
        
        **질문**: "우리 회사의 출장 정책과 비용 처리 방법은?"
        
        **정답에 필요한 정보**:
        1. 출장 신청 절차
        2. 출장비 지급 기준  
        3. 영수증 제출 방법
        
        ✅ **좋은 검색 (Recall = 1.0)**:
        - 문서 1: 출장 신청 절차 설명
        - 문서 2: 출장비 지급 기준과 영수증 제출 방법
        → 필요한 정보 100% 포함!
        
        ❌ **나쁜 검색 (Recall = 0.33)**:
        - 문서 1: 출장 신청 절차만 설명
        → 출장비와 영수증 정보가 누락됨!
        """)
    
    with col2:
        # 검색 완성도 시각화
        found_info = 3
        total_info = 3
        missing_info = total_info - found_info
        
        fig = go.Figure(data=[
            go.Pie(
                labels=['찾은 정보', '놓친 정보'],
                values=[found_info, missing_info] if missing_info > 0 else [found_info, 0.1],
                hole=.3,
                marker_colors=['lightgreen', 'lightcoral']
            )
        ])
        
        fig.update_layout(
            title=f"정보 발견율: {found_info}/{total_info}",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        ### 🎯 **목표 점수**
        - **1.0**: 완벽 (정보 누락 없음)
        - **0.9+**: 우수
        - **0.8+**: 양호  
        - **0.7-**: 검색 개선 필요
        """)
    
    st.markdown("""
    ### 🔍 **실제 평가 과정**
    
    1. **정답 분석**: 정답을 만들기 위해 필요한 모든 정보 조각들을 식별
    2. **문서 검색**: 각 정보 조각이 검색된 문서들 안에 있는지 확인
    3. **점수 계산**: (찾은 정보 / 전체 필요 정보) × 100
    
    ### 🔧 **개선 방법**
    
    1. **검색 범위 확대**
       - 더 많은 문서 소스 활용
       - 검색 키워드 다양화
       - 유사어, 동의어 검색 포함
    
    2. **검색 전략 개선**
       - 하이브리드 검색 (키워드 + 의미적 검색)
       - 멀티 스텝 검색 (연관 검색)
       - 질문 분해 후 단계적 검색
    
    3. **문서 품질 향상**
       - 중요 정보가 누락되지 않도록 문서 보완
       - 정보 간 연결 강화
    """)

def show_context_precision_explanation():
    """Context Precision 상세 설명"""
    st.markdown("## 📍 Context Precision (컨텍스트 정확성)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🤔 **이게 뭔가요?**
        
        **"불필요한 정보는 없나요?"**를 측정하는 지표입니다.
        
        검색된 문서들이 질문에 얼마나 관련이 있는지, 
        쓸데없는 정보나 노이즈가 얼마나 적은지를 확인합니다.
        
        ### 📝 **구체적인 예시**
        
        **질문**: "파이썬에서 딕셔너리를 정렬하는 방법은?"
        
        ✅ **좋은 검색 (Precision = 1.0)**:
        - 문서 1: 파이썬 딕셔너리 정렬 방법 설명
        - 문서 2: sorted() 함수와 딕셔너리 예제
        → 모든 문서가 질문과 직접 관련!
        
        ❌ **나쁜 검색 (Precision = 0.33)**:
        - 문서 1: 파이썬 딕셔너리 정렬 방법 (관련 있음)
        - 문서 2: 파이썬 역사와 특징 (관련 없음)  
        - 문서 3: Java 프로그래밍 기초 (관련 없음)
        → 3개 중 1개만 유용함!
        """)
    
    with col2:
        # 정확도 시각화
        relevant_docs = 2
        total_docs = 3
        irrelevant_docs = total_docs - relevant_docs
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=['관련 있는 문서', '관련 없는 문서'],
            y=[relevant_docs, irrelevant_docs],
            marker_color=['lightgreen', 'lightcoral']
        ))
        
        fig.update_layout(
            title=f"문서 관련성: {relevant_docs}/{total_docs}",
            yaxis_title="문서 수",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        ### 📊 **점수 의미**
        - **1.0**: 모든 문서가 유용
        - **0.8+**: 대부분 관련 있음
        - **0.6+**: 절반 정도 유용
        - **0.5-**: 노이즈가 너무 많음
        """)
    
    st.markdown("""
    ### 🎯 **왜 중요한가요?**
    
    1. **AI 혼란 방지**: 관련 없는 정보가 많으면 AI가 헷갈려서 잘못된 답변 생성
    2. **처리 속도**: 불필요한 문서가 많으면 답변 생성이 느려짐
    3. **비용 절약**: 관련 있는 정보만 처리하면 API 비용 절약
    4. **사용자 경험**: 정확하고 빠른 답변으로 만족도 향상
    
    ### 🔧 **개선 방법**
    
    1. **검색 정확도 향상**
       - 더 정밀한 검색 알고리즘 사용
       - 질문-문서 유사도 임계값 조정
       - 검색 키워드 정제
    
    2. **문서 필터링**
       - 관련성 점수 기반 필터링
       - 중복 문서 제거
       - 문서 순서 최적화 (관련성 높은 순)
    
    3. **피드백 학습**
       - 사용자 피드백으로 검색 품질 개선
       - A/B 테스트로 최적 설정 찾기
    """)

def show_practical_guide():
    """실전 가이드"""
    st.markdown("## 💡 실전 활용 가이드")
    
    # 점수 해석 가이드 (RAGAS 공식 기준 반영)
    st.markdown("### 📊 점수 해석 및 액션 가이드")
    
    score_guide = {
        "점수 구간": ["0.9 - 1.0", "0.7 - 0.9", "0.5 - 0.7", "0.3 - 0.5", "0.0 - 0.3"],
        "평가": ["🌟 우수", "✅ 양호", "⚠️ 보통", "🔴 개선필요", "❌ 심각"],
        "의미": [
            "프로덕션 수준의 품질",
            "실용적으로 사용 가능",
            "개선이 필요하지만 작동",
            "기본 기능만 작동",
            "시스템 재검토 필요"
        ],
        "액션": [
            "현재 상태 유지, 미세 조정",
            "일부 개선으로 우수 등급 달성",
            "구체적 개선 계획 수립",
            "즉시 개선 작업 시작",
            "전면적 재검토 필요"
        ]
    }
    
    st.dataframe(pd.DataFrame(score_guide), use_container_width=True)
    
    # 개선 우선순위
    st.markdown("### 🎯 개선 우선순위 전략")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 📈 **단계별 개선 전략**
        
        **1단계: Faithfulness 확보 (최우선)**
        - 환각(hallucination) 방지가 가장 중요
        - 신뢰할 수 없는 정보는 모든 것을 무의미하게 만듦
        - 목표: 0.9 이상 (프로덕션 최소 기준)
        
        **2단계: Answer Relevancy 개선**
        - 사용자 질문에 정확히 답하는 것이 핵심
        - 사용자 경험에 직접적 영향
        - 목표: 0.8 이상
        
        **3단계: Context Recall 개선**
        - 필요한 정보를 모두 찾아야 완전한 답변 가능
        - 검색 시스템의 완성도
        - 목표: 0.8 이상
        
        **4단계: Context Precision 최적화**
        - 효율성과 속도 향상
        - 비용 최적화 효과
        - 목표: 0.7 이상
        """)
    
    with col2:
        st.markdown("""
        #### ⚡ **빠른 개선 팁**
        
        **Faithfulness 빠른 개선**
        - 프롬프트에 "제공된 정보만 사용" 추가
        - Temperature 0.1로 설정
        
        **Answer Relevancy 빠른 개선**
        - "간결하게 답변하세요" 프롬프트 추가
        - 질문 의도 파악 프롬프트 강화
        
        **Context Recall 빠른 개선**
        - 검색 키워드 확장
        - 검색 결과 개수 증가 (5→10개)
        
        **Context Precision 빠른 개선**
        - 유사도 임계값 상향 조정
        - 중복 문서 자동 제거
        """)
    
    # RAGAS 논문 기반 성능 기준
    st.markdown("### 🏆 RAGAS 논문 기반 성능 기준")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 📚 RAGAS 연구 결과
        
        **Faithfulness (환각 방지):**
        - 🟢 0.9+ : 프로덕션 환경 권장
        - 🟡 0.8+ : 개발/테스트 환경 적합
        - 🔴 <0.8 : 즉시 개선 필요
        
        **Answer Relevancy (관련성):**
        - 🟢 0.8+ : 사용자 만족도 높음
        - 🟡 0.6+ : 기본적인 요구사항 충족
        - 🔴 <0.6 : 사용자 경험 저하
        """)
    
    with col2:
        st.markdown("""
        #### 🔍 실제 개발 경험 기반
        
        **Context Recall (완성도):**
        - 🟢 0.9+ : 정보 누락 거의 없음
        - 🟡 0.7+ : 일반적인 사용에 적합
        - 🔴 <0.7 : 검색 시스템 개선 필요
        
        **Context Precision (정확도):**
        - 🟢 0.8+ : 효율적인 처리 성능
        - 🟡 0.6+ : 적절한 수준
        - 🔴 <0.6 : 노이즈 제거 필요
        """)
    
    # 실제 RAGAS 논문에서 언급된 중요 포인트들
    st.markdown("""
    #### 🎯 RAGAS 논문의 핵심 인사이트
    
    1. **Faithfulness가 가장 중요**: 정확하지 않은 정보는 모든 것을 무의미하게 만듦
    2. **Context 메트릭의 균형**: Recall과 Precision의 트레이드오프 관계
    3. **도메인별 차이**: 의료, 법률 등 전문 분야는 더 높은 기준 필요
    4. **LLM 의존성**: 평가 자체가 LLM 기반이므로 평가용 모델 선택이 중요
    
    **📖 참고**: Shahul Es, Jithin James, Luis Espinosa-Anke, Steven Schockaert. 
    "RAGAS: Automated Evaluation of Retrieval Augmented Generation." arXiv:2309.15217
    """)
    
    # 트러블슈팅
    st.markdown("### 🔧 자주 묻는 문제와 해결책")
    
    troubleshooting = [
        {
            "문제": "모든 점수가 0.5 이하로 매우 낮아요 😢",
            "원인": "시스템 기본 설정 문제 또는 데이터 품질 이슈",
            "해결책": "1) API 키 확인 2) 프롬프트 템플릿 점검 3) 평가 데이터 형식 검증 4) 모델 설정 확인"
        },
        {
            "문제": "Faithfulness가 0.7 이하로 낮아요",
            "원인": "AI가 컨텍스트에 없는 정보를 생성 (환각 현상)",
            "해결책": "1) Temperature를 0.1-0.3으로 낮추기 2) '제공된 문서만 사용하세요' 프롬프트 추가 3) 더 안정적인 모델 사용"
        },
        {
            "문제": "Context Precision이 0.6 이하로 낮아요",
            "원인": "검색된 문서 중 관련 없는 내용이 너무 많음",
            "해결책": "1) 검색 유사도 임계값 높이기 2) 검색 결과 개수 줄이기 3) 검색 알고리즘 개선"
        },
        {
            "문제": "Context Recall이 0.7 이하로 낮아요",
            "원인": "필요한 정보를 충분히 검색하지 못함",
            "해결책": "1) 검색 범위 확대 2) 다양한 키워드로 검색 3) 하이브리드 검색 (키워드+의미) 활용"
        },
        {
            "문제": "Answer Relevancy가 0.6 이하로 낮아요",
            "원인": "질문에 직접 답하지 않거나 불필요한 내용 포함",
            "해결책": "1) '질문에 직접 답하세요' 프롬프트 추가 2) 답변 길이 제한 3) 질문 의도 파악 개선"
        },
        {
            "문제": "점수는 높은데 실제 답변이 이상해요",
            "원인": "평가 데이터와 실제 사용 패턴의 차이",
            "해결책": "1) 실제 사용자 질문으로 추가 평가 2) 도메인별 맞춤 평가 3) 사용자 피드백 수집"
        }
    ]
    
    for item in troubleshooting:
        with st.expander(f"❓ {item['문제']}"):
            st.write(f"**원인**: {item['원인']}")
            st.write(f"**해결책**: {item['해결책']}")