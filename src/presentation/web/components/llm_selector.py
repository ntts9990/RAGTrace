"""
LLM 선택 컴포넌트

사용자가 평가에 사용할 LLM 모델을 선택할 수 있는 UI를 제공합니다.
"""

import streamlit as st
from src.config import settings


def show_llm_selector() -> str:
    """
    LLM 선택 UI를 표시합니다.
    
    Returns:
        str: 선택된 LLM 타입 ('gemini' 또는 'hcx')
    """
    st.markdown("### 🤖 LLM 모델 선택")
    
    # LLM 옵션 정의
    llm_options = {
        "🔥 Google Gemini 2.5 Flash": "gemini",
        "🎯 Naver HCX-005": "hcx"
    }
    
    # HCX API 키 확인
    hcx_available = bool(settings.CLOVA_STUDIO_API_KEY)
    
    if not hcx_available:
        st.warning("⚠️ HCX 모델을 사용하려면 .env 파일에 CLOVA_STUDIO_API_KEY를 설정해야 합니다.")
        # HCX 옵션 비활성화
        available_options = {"🔥 Google Gemini 2.5 Flash": "gemini"}
    else:
        available_options = llm_options
    
    # session_state에 기본값 설정
    if "selected_llm" not in st.session_state:
        st.session_state.selected_llm = settings.DEFAULT_LLM
    
    # 현재 선택된 LLM이 사용 가능한 옵션에 없으면 기본값으로 변경
    if st.session_state.selected_llm not in available_options.values():
        st.session_state.selected_llm = "gemini"
    
    # 현재 선택된 LLM에 해당하는 설명 찾기
    current_description = None
    for desc, llm_type in available_options.items():
        if llm_type == st.session_state.selected_llm:
            current_description = desc
            break
    
    if current_description is None:
        current_description = list(available_options.keys())[0]
    
    # 선택 박스
    selected_description = st.selectbox(
        "사용할 LLM 모델을 선택하세요:",
        options=list(available_options.keys()),
        index=list(available_options.keys()).index(current_description),
        key="llm_selector_box",
        help="평가에 사용할 LLM 모델을 선택합니다. 각 모델마다 다른 성능 특성을 가집니다."
    )
    
    selected_llm = available_options[selected_description]
    st.session_state.selected_llm = selected_llm
    
    # 선택된 LLM 정보 표시
    if selected_llm == "gemini":
        st.info("🔥 **Google Gemini 2.5 Flash**: 빠르고 효율적인 다목적 LLM")
    elif selected_llm == "hcx":
        st.info("🎯 **Naver HCX-005**: 한국어에 최적화된 고성능 LLM")
    
    return selected_llm


def show_llm_comparison():
    """LLM 모델들의 비교 정보를 표시합니다."""
    st.markdown("### 📊 LLM 모델 비교")
    
    comparison_data = {
        "모델": ["Google Gemini 2.5 Flash", "Naver HCX-005"],
        "언어 지원": ["다국어 (한국어 포함)", "한국어 특화"],
        "속도": ["매우 빠름", "빠름"],
        "정확도": ["높음", "매우 높음 (한국어)"],
        "특징": ["범용성, 효율성", "한국어 이해도, 문맥 파악"],
    }
    
    st.table(comparison_data)
    
    st.markdown("""
    **선택 가이드:**
    - **한국어 콘텐츠 평가**: HCX-005 권장
    - **다국어 혼재 콘텐츠**: Gemini 2.5 Flash 권장
    - **빠른 평가가 필요한 경우**: Gemini 2.5 Flash 권장
    """)