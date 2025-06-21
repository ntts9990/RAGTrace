"""
임베딩 모델 선택 컴포넌트

사용자가 평가에 사용할 임베딩 모델을 선택할 수 있는 UI를 제공합니다.
"""

import streamlit as st
from src.config import settings


def show_embedding_selector() -> str:
    """
    임베딩 모델 선택 UI를 표시합니다.
    
    Returns:
        str: 선택된 임베딩 타입 ('gemini' 또는 'hcx')
    """
    st.markdown("### 🔍 임베딩 모델 선택")
    
    # 임베딩 옵션 정의
    embedding_options = {
        "🌐 Google Gemini Embedding": "gemini",
        "🎯 Naver HCX Embedding": "hcx"
    }
    
    # HCX API 키 확인
    hcx_available = bool(settings.CLOVA_STUDIO_API_KEY)
    
    if not hcx_available:
        st.warning("⚠️ HCX 임베딩을 사용하려면 .env 파일에 CLOVA_STUDIO_API_KEY를 설정해야 합니다.")
        # HCX 옵션 비활성화
        available_options = {"🌐 Google Gemini Embedding": "gemini"}
    else:
        available_options = embedding_options
    
    # session_state에 기본값 설정
    if "selected_embedding" not in st.session_state:
        st.session_state.selected_embedding = "gemini"  # 기본값을 gemini로 설정
    
    # 현재 선택된 임베딩이 사용 가능한 옵션에 없으면 기본값으로 변경
    if st.session_state.selected_embedding not in available_options.values():
        st.session_state.selected_embedding = "gemini"
    
    # 현재 선택된 임베딩에 해당하는 설명 찾기
    current_description = None
    for desc, embedding_type in available_options.items():
        if embedding_type == st.session_state.selected_embedding:
            current_description = desc
            break
    
    if current_description is None:
        current_description = list(available_options.keys())[0]
    
    # 선택 박스
    selected_description = st.selectbox(
        "사용할 임베딩 모델을 선택하세요:",
        options=list(available_options.keys()),
        index=list(available_options.keys()).index(current_description),
        key="embedding_selector_box",
        help="벡터 검색과 문맥 이해에 사용할 임베딩 모델을 선택합니다. LLM과 독립적으로 선택 가능합니다."
    )
    
    selected_embedding = available_options[selected_description]
    st.session_state.selected_embedding = selected_embedding
    
    # 선택된 임베딩 정보 표시
    if selected_embedding == "gemini":
        st.info("🌐 **Google Gemini Embedding**: 다국어 지원, 빠른 벡터화")
    elif selected_embedding == "hcx":
        st.info("🎯 **Naver HCX Embedding**: 한국어 특화, 높은 의미 이해도")
    
    return selected_embedding


def show_embedding_comparison():
    """임베딩 모델들의 비교 정보를 표시합니다."""
    st.markdown("### 📊 임베딩 모델 비교")
    
    comparison_data = {
        "모델": ["Google Gemini Embedding", "Naver HCX Embedding"],
        "언어 지원": ["다국어 (한국어 포함)", "한국어 특화"],
        "속도": ["매우 빠름", "빠름"],
        "정확도": ["높음", "매우 높음 (한국어)"],
        "벡터 차원": ["768차원", "1024차원"],
        "특징": ["범용성, 효율성", "한국어 의미 이해도"],
    }
    
    st.table(comparison_data)
    
    st.markdown("""
    **선택 가이드:**
    - **한국어 문서 임베딩**: HCX Embedding 권장
    - **다국어 혼재 문서**: Gemini Embedding 권장
    - **빠른 처리가 필요한 경우**: Gemini Embedding 권장
    - **높은 정확도가 필요한 경우**: HCX Embedding 권장 (한국어)
    """)


def show_llm_embedding_combination_guide():
    """LLM과 임베딩 모델 조합 가이드를 표시합니다."""
    st.markdown("### 💡 LLM-임베딩 조합 가이드")
    
    st.markdown("""
    #### 🎯 권장 조합
    
    **🥇 최고 성능 (한국어)**
    - LLM: Naver HCX-005 + 임베딩: Naver HCX
    - 한국어 전용 문서에서 최고 성능
    
    **🥈 균형잡힌 성능**
    - LLM: Google Gemini + 임베딩: Google Gemini
    - 다국어 문서에서 안정적 성능
    
    **🥉 하이브리드 조합**
    - LLM: Naver HCX-005 + 임베딩: Google Gemini
    - 한국어 답변 생성 + 빠른 임베딩 처리
    
    **🔄 실험적 조합**
    - LLM: Google Gemini + 임베딩: Naver HCX
    - 범용 LLM + 한국어 특화 임베딩
    """)