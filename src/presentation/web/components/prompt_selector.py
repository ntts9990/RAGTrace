"""
프롬프트 선택 컴포넌트

RAGAS 평가에 사용할 프롬프트 타입을 선택할 수 있는 UI 컴포넌트
"""

import streamlit as st
from typing import Optional

from src.domain.prompts import PromptType, PROMPT_TYPE_DESCRIPTIONS
from src.infrastructure.evaluation.custom_prompts import CustomPromptFactory


def show_prompt_selector() -> Optional[PromptType]:
    """프롬프트 타입 선택 UI"""
    
    st.markdown("### 🎯 평가 프롬프트 선택")
    
    # 프롬프트 타입 옵션 준비
    prompt_options = {}
    for prompt_type in CustomPromptFactory.get_available_prompt_types():
        description = CustomPromptFactory.get_prompt_type_description(prompt_type)
        prompt_options[description] = prompt_type
    
    # session_state에 기본값 설정
    if "selected_prompt_type" not in st.session_state:
        st.session_state.selected_prompt_type = PromptType.DEFAULT
    
    # 현재 선택된 프롬프트 타입의 설명 찾기
    current_description = None
    for desc, ptype in prompt_options.items():
        if ptype == st.session_state.selected_prompt_type:
            current_description = desc
            break
    
    if current_description is None:
        current_description = list(prompt_options.keys())[0]
        st.session_state.selected_prompt_type = prompt_options[current_description]
    
    # 선택 박스 (key를 사용하여 상태 유지)
    selected_description = st.selectbox(
        "사용할 프롬프트 타입을 선택하세요:",
        options=list(prompt_options.keys()),
        index=list(prompt_options.keys()).index(current_description),
        key="prompt_selector_box",
        help="평가에 사용할 프롬프트 종류를 선택합니다. 도메인과 언어에 따라 최적화된 프롬프트를 사용할 수 있습니다."
    )
    
    # 선택이 변경되면 session_state 업데이트
    selected_prompt_type = prompt_options[selected_description]
    st.session_state.selected_prompt_type = selected_prompt_type
    
    # 선택된 프롬프트 타입에 대한 상세 정보 표시
    show_prompt_type_details(selected_prompt_type)
    
    return selected_prompt_type


def show_prompt_type_details(prompt_type: PromptType):
    """선택된 프롬프트 타입의 상세 정보 표시"""
    
    st.markdown("#### 📋 선택된 프롬프트 정보")
    
    if prompt_type == PromptType.DEFAULT:
        st.info("""
        **🌐 기본 RAGAS 프롬프트 (영어)**
        
        - RAGAS 라이브러리의 기본 프롬프트 사용
        - 영어 기반 평가에 최적화
        - 다양한 도메인에서 범용적으로 사용 가능
        - 안정적이고 검증된 프롬프트
        """)
        
    elif prompt_type == PromptType.NUCLEAR_HYDRO_TECH:
        st.success("""
        **⚛️ 원자력/수력 기술 문서 특화 프롬프트**
        
        **특징:**
        - 원자력/수력 발전 기술 문서 평가에 최적화
        - 안전 관련 절차와 규정의 정확성 평가
        - 물리적/화학적 수식과 단위의 정밀성 검증
        - 한영 혼용 전문 용어의 일관성 확인
        - 시스템 구성요소와 운영 매개변수 평가
        
        **적용 영역:**
        - 원자력 발전소 운영 문서
        - 수력 발전 시스템 문서
        - 안전 분석 보고서 (SAR/FSAR)
        - 기술 사양서 및 절차서
        - 규제 요구사항 문서
        """)
        
        # 예시 표시
        with st.expander("📖 프롬프트 예시 보기"):
            st.code("""
            예시 질문: "원자로 냉각재 온도 측정 시 주의사항은?"
            답변: "RTD (Resistance Temperature Detector) 센서를 사용하여 측정하며, 허용 오차는 ±0.5°C 이내여야 합니다. Safety Class 1E 등급이 요구됩니다."
            
            평가 기준:
            - RTD 센서 사용의 정확성
            - 허용 오차 ±0.5°C의 정밀성
            - Safety Class 1E 등급 요구사항
            - 온도 측정 절차의 완전성
            """, language="text")
    
    
    # 성능 비교 정보
    show_prompt_performance_info(prompt_type)


def show_prompt_performance_info(prompt_type: PromptType):
    """프롬프트 타입별 성능 정보 표시"""
    
    st.markdown("#### 📊 예상 성능 특성")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="정확도",
            value=get_accuracy_rating(prompt_type),
            help="해당 도메인에서의 평가 정확도"
        )
    
    with col2:
        st.metric(
            label="속도",
            value=get_speed_rating(prompt_type),
            help="평가 처리 속도"
        )
    
    with col3:
        st.metric(
            label="특화도",
            value=get_specialization_rating(prompt_type),
            help="특정 도메인에 대한 특화 정도"
        )


def get_accuracy_rating(prompt_type: PromptType) -> str:
    """프롬프트 타입별 정확도 등급"""
    ratings = {
        PromptType.DEFAULT: "보통",
        PromptType.NUCLEAR_HYDRO_TECH: "매우 높음",
        PromptType.KOREAN_FORMAL: "높음"
    }
    return ratings.get(prompt_type, "알 수 없음")


def get_speed_rating(prompt_type: PromptType) -> str:
    """프롬프트 타입별 속도 등급"""
    ratings = {
        PromptType.DEFAULT: "빠름",
        PromptType.NUCLEAR_HYDRO_TECH: "보통", 
        PromptType.KOREAN_FORMAL: "보통"
    }
    return ratings.get(prompt_type, "알 수 없음")


def get_specialization_rating(prompt_type: PromptType) -> str:
    """프롬프트 타입별 특화도 등급"""
    ratings = {
        PromptType.DEFAULT: "범용",
        PromptType.NUCLEAR_HYDRO_TECH: "원자력/수력",
        PromptType.KOREAN_FORMAL: "공식문서"
    }
    return ratings.get(prompt_type, "알 수 없음")


def show_prompt_comparison():
    """프롬프트 타입 비교 표시"""
    
    st.markdown("### 📊 프롬프트 타입 비교")
    
    comparison_data = []
    for prompt_type in CustomPromptFactory.get_available_prompt_types():
        description = CustomPromptFactory.get_prompt_type_description(prompt_type)
        comparison_data.append({
            "프롬프트 타입": description,
            "정확도": get_accuracy_rating(prompt_type),
            "속도": get_speed_rating(prompt_type),
            "특화도": get_specialization_rating(prompt_type),
            "권장 사용처": get_recommended_usage(prompt_type)
        })
    
    import pandas as pd
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def get_recommended_usage(prompt_type: PromptType) -> str:
    """프롬프트 타입별 권장 사용처"""
    usages = {
        PromptType.DEFAULT: "일반적인 RAG 시스템",
        PromptType.NUCLEAR_HYDRO_TECH: "원자력/수력 기술 문서, 안전 분석 보고서",
        PromptType.KOREAN_FORMAL: "공식 문서, 정책 문서"
    }
    return usages.get(prompt_type, "기타")


def show_prompt_customization_tips():
    """프롬프트 커스터마이징 팁 표시"""
    
    st.markdown("### 💡 프롬프트 선택 가이드")
    
    st.markdown("""
    #### 🎯 언제 어떤 프롬프트를 사용해야 할까요?
    
    **🌐 기본 프롬프트 (DEFAULT)**
    - 영어 문서나 범용적인 내용 평가
    - 빠른 성능이 필요한 경우
    - 검증된 안정성이 중요한 경우
    
    **⚛️ 원자력/수력 기술 문서 프롬프트 (NUCLEAR_HYDRO_TECH)**
    - 원자력 발전소 운영 문서
    - 수력 발전 시스템 기술 문서
    - 안전 분석 보고서 (SAR/FSAR)
    - 규제 요구사항 및 절차서
    - 한영 혼용 전문 용어가 포함된 기술 문서
    - 수식과 물리량이 포함된 정밀 문서
    """)
    
    st.info("""
    **📝 팁:** 
    - 처음에는 기본 프롬프트로 테스트해보세요
    - 결과가 만족스럽지 않다면 도메인 특화 프롬프트를 시도하세요
    - 여러 프롬프트로 평가하여 결과를 비교해보세요
    """)