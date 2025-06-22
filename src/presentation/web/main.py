"""
Refactored RAGTrace Dashboard using MVC Pattern

MVC 패턴을 적용한 리팩토링된 RAGTrace 대시보드입니다.
"""

import streamlit as st

# 페이지 설정을 가장 먼저 실행
st.set_page_config(
    page_title="RAGTrace 대시보드",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 간단한 메인 함수
def main():
    """간단한 메인 애플리케이션"""
    st.title("🔍 RAGTrace 대시보드")
    st.write("RAG 시스템의 성능을 추적하고 분석합니다.")
    
    # 사이드바
    st.sidebar.title("🔍 RAGTrace")
    page = st.sidebar.selectbox(
        "페이지 선택",
        ["🔍 Overview", "🚀 Run Evaluation", "📈 Historical Analysis"]
    )
    
    # 페이지별 내용
    if page == "🔍 Overview":
        show_overview()
    elif page == "🚀 Run Evaluation":
        show_evaluation()
    elif page == "📈 Historical Analysis":
        show_historical()


def show_overview():
    """Overview 페이지"""
    st.header("📊 평가 결과 개요")
    st.info("아직 평가 이력이 없습니다. 'Run Evaluation' 페이지에서 새로운 평가를 시작하세요.")
    
    if st.button("🚀 새 평가 실행", type="primary"):
        st.switch_page("🚀 Run Evaluation")


def show_evaluation():
    """Evaluation 페이지"""
    st.header("🚀 새 평가 실행")
    st.write("평가 기능은 구현 중입니다.")
    
    # 간단한 테스트 버튼
    if st.button("컨테이너 테스트"):
        with st.spinner("컨테이너 로딩 중..."):
            try:
                from src.container import container
                st.success("✅ 컨테이너 로딩 성공!")
            except Exception as e:
                st.error(f"❌ 컨테이너 로딩 실패: {e}")


def show_historical():
    """Historical 페이지"""
    st.header("📈 과거 평가 분석")
    st.write("히스토리 기능은 구현 중입니다.")


if __name__ == "__main__":
    main()