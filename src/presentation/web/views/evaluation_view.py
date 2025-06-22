"""
Evaluation View

새 평가 실행 뷰입니다.
"""

import json
import streamlit as st
from typing import List

from .base_view import BaseView
from ..models.evaluation_model import EvaluationConfig, EvaluationModel
from ..services import EvaluationService, DatabaseService
from src.domain.prompts import PromptType
from src.utils.paths import get_available_datasets, get_evaluation_data_path
from src.presentation.web.components.llm_selector import show_llm_selector
from src.presentation.web.components.embedding_selector import show_embedding_selector
from src.presentation.web.components.prompt_selector import show_prompt_selector
from ..components import llm_selector, embedding_selector, prompt_selector


class EvaluationView(BaseView):
    """새 평가 실행 뷰"""
    
    def __init__(self, session_manager):
        super().__init__(session_manager)
        self.evaluation_service = EvaluationService()
        self.db_service = DatabaseService()

    def render(self) -> None:
        """새 평가 실행 페이지 렌더링"""
        st.title("🚀 Run New Evaluation")
        st.markdown("---")
        
        # 데이터셋 선택
        available_datasets = self.db_service.get_available_datasets()
        self.state.selected_dataset = st.selectbox(
            "1. Select Dataset", available_datasets,
            index=available_datasets.index(self.state.selected_dataset) if self.state.selected_dataset in available_datasets else 0
        )
        
        # 모델 및 프롬프트 선택
        llm_type = llm_selector()
        embedding_type = embedding_selector()
        prompt_type = prompt_selector()

        if st.button("Start Evaluation", type="primary"):
            if self.state.selected_dataset:
                with st.spinner("Evaluation in progress... Please wait."):
                    result = self.evaluation_service.run_evaluation(
                        dataset_name=self.state.selected_dataset,
                        llm=llm_type,
                        embedding=embedding_type,
                        prompt_type=prompt_type.value
                    )
                    # 평가 결과와 완료 상태를 AppState에 저장
                    self.state.evaluation.is_completed = True
                    self.state.evaluation.result = result
                    
                    # 평가 이력에도 추가 (DB 저장 후)
                    self.db_service.save_evaluation_result(result)
                    
                    st.success("Evaluation completed!")
                    st.rerun() # UI를 즉시 새로고침하여 결과 표시
            else:
                st.error("Please select a dataset first.")

        # 평가 완료 후 결과 표시
        if self.state.evaluation.is_completed and self.state.evaluation.result:
            st.subheader("Latest Evaluation Result")
            st.json(self.state.evaluation.result)
            
            if st.button("View Detailed Analysis"):
                # 상세 분석 페이지로 네비게이션
                self.session_manager.state.selected_page = "📈 Historical Analysis"
                st.rerun()
    
    def _collect_configuration(self) -> EvaluationConfig:
        """평가 설정 수집"""
        # LLM 선택
        selected_llm = show_llm_selector()
        st.markdown("---")
        
        # 임베딩 선택
        selected_embedding = show_embedding_selector()
        st.markdown("---")
        
        # 프롬프트 선택
        selected_prompt_type = show_prompt_selector()
        st.markdown("---")
        
        # 데이터셋 선택
        selected_dataset = self._render_dataset_selector()
        
        if not selected_dataset:
            return None
        
        return EvaluationModel.create_config(
            llm_type=selected_llm,
            embedding_type=selected_embedding,
            prompt_type=selected_prompt_type,
            dataset_name=selected_dataset
        )
    
    def _render_dataset_selector(self) -> str:
        """데이터셋 선택 UI"""
        st.markdown("### 📊 데이터셋 선택")
        
        existing_datasets = get_available_datasets()
        if not existing_datasets:
            self.show_error("❌ 사용 가능한 평가 데이터셋이 없습니다.")
            self.show_info("data/ 디렉토리에 JSON 형식의 평가 데이터를 추가하세요.")
            return None
        
        # 세션 상태에서 선택된 데이터셋 관리
        if not self.session.get_selected_dataset() or self.session.get_selected_dataset() not in existing_datasets:
            self.session.set_selected_dataset(existing_datasets[0])
        
        current_index = existing_datasets.index(self.session.get_selected_dataset())
        
        selected_dataset = st.selectbox(
            "평가할 데이터셋을 선택하세요:",
            existing_datasets,
            index=current_index,
            key="dataset_selector_box",
            help="평가에 사용할 QA 데이터셋을 선택합니다."
        )
        
        self.session.set_selected_dataset(selected_dataset)
        
        # 데이터셋 정보 표시
        self._show_dataset_info(selected_dataset)
        
        return selected_dataset
    
    def _show_dataset_info(self, dataset_name: str) -> None:
        """데이터셋 정보 표시"""
        dataset_path = get_evaluation_data_path(dataset_name)
        if dataset_path:
            try:
                with open(dataset_path, encoding="utf-8") as f:
                    qa_data = json.load(f)
                    self.show_info(f"📋 선택된 데이터셋: **{dataset_name}** ({len(qa_data)}개 QA 쌍)")
            except Exception as e:
                self.show_warning(f"데이터셋 정보 로드 실패: {e}")
    
    def _render_configuration_summary(self, config: EvaluationConfig) -> None:
        """평가 설정 요약"""
        st.markdown("---")
        st.markdown("### 📋 평가 설정 요약")
        
        col1, col2, col3, col4 = self.create_columns(4)
        with col1:
            st.write(f"**🤖 LLM 모델:** {config.llm_type}")
        with col2:
            st.write(f"**🔍 임베딩 모델:** {config.embedding_type}")
        with col3:
            st.write(f"**🎯 프롬프트 타입:** {config.prompt_type.value}")
        with col4:
            st.write(f"**📊 데이터셋:** {config.dataset_name}")
        
        st.markdown("---")
    
    def _render_execution_buttons(self, config: EvaluationConfig) -> None:
        """실행 버튼들"""
        col1, col2, col3 = self.create_columns([1, 2, 1])
        
        with col1:
            self.show_navigation_button("← 뒤로가기", "🎯 Overview")
        
        with col2:
            if st.button("🚀 평가 시작", type="primary", use_container_width=True):
                self._execute_evaluation(config)
        
        with col3:
            st.write("")  # 빈 공간
    
    def _execute_evaluation(self, config: EvaluationConfig) -> None:
        """평가 실행"""
        # 설정 유효성 검증
        if not EvaluationService.validate_configuration(config):
            error_msg = EvaluationService.get_configuration_error_message(config)
            self.show_error(error_msg)
            return
        
        with self.show_spinner("🔄 평가를 실행 중입니다..."):
            try:
                self._show_evaluation_info(config)
                
                # 진행 상황 표시
                progress_placeholder = st.empty()
                
                with progress_placeholder.container():
                    self.show_info("⚡ 평가 실행 중... (최대 30초 소요)")
                    self.show_warning("💡 **참고**: 현재 네트워크 문제로 인해 실제 평가가 진행되지 않을 수 있습니다. 30초 후 샘플 결과를 표시합니다.")
                    progress_bar = st.progress(0)
                    progress_text = st.empty()
                    
                    progress_text.text("평가 시작...")
                    progress_bar.progress(25)
                    
                    # 실제 평가 실행
                    result = EvaluationService.execute_evaluation(config)
                    
                    progress_bar.progress(100)
                    progress_text.text("평가 완료!")
                
                # 진행 상황 표시 제거
                progress_placeholder.empty()
                
                # 성공 처리
                self._handle_evaluation_success(result)
                
            except Exception as e:
                self.show_error(f"❌ 평가 중 오류 발생: {str(e)}")
                st.exception(e)
    
    def _show_evaluation_info(self, config: EvaluationConfig) -> None:
        """평가 정보 표시"""
        st.markdown("### 🔧 평가 설정")
        col1, col2 = self.create_columns(2)
        
        with col1:
            self.show_info(f"🤖 **LLM 모델**: {config.llm_type}")
            self.show_info(f"📊 **데이터셋**: {config.dataset_name}")
        
        with col2:
            self.show_info(f"🔍 **임베딩 모델**: {config.embedding_type}")
            self.show_info(f"🎯 **프롬프트 타입**: {config.prompt_type.value}")
        
        # 프롬프트 타입 설명
        if config.prompt_type == PromptType.DEFAULT:
            self.show_success("📝 **기본 RAGAS 프롬프트 (영어)** - 범용적이고 안정적인 평가")
        elif config.prompt_type == PromptType.NUCLEAR_HYDRO_TECH:
            self.show_success("⚛️ **원자력/수력 기술 문서 특화 프롬프트** - 기술 정확성과 안전 규정에 최적화")
        elif config.prompt_type == PromptType.KOREAN_FORMAL:
            self.show_success("📋 **한국어 공식 문서 특화 프롬프트** - 정책 문서와 법규 해석에 최적화")
        
        st.markdown("---")
    
    def _handle_evaluation_success(self, result) -> None:
        """평가 성공 처리"""
        self.show_success("✅ 평가가 완료되었습니다!")
        self.show_balloons()
        
        # 결과 요약 표시
        st.markdown("### 📊 평가 결과")
        
        # 더미 결과 확인
        if EvaluationModel.is_dummy_result(result):
            self.show_error("🚨 **샘플 결과**: 네트워크 문제로 인해 실제 평가가 실행되지 않았습니다.")
            st.markdown("""
            **해결 방법:**
            1. 인터넷 연결 상태 확인
            2. Google AI API 할당량 확인
            3. 방화벽/프록시 설정 확인
            4. 잠시 후 다시 시도
            """)
        
        # 결과 메트릭 표시
        col1, col2, col3, col4 = self.create_columns(4)
        with col1:
            st.metric("🏆 RAGAS Score", f"{result.ragas_score:.3f}")
        with col2:
            st.metric("✅ Faithfulness", f"{result.faithfulness:.3f}")
        with col3:
            st.metric("🎯 Answer Relevancy", f"{result.answer_relevancy:.3f}")
        with col4:
            st.metric("🔄 Context Recall", f"{result.context_recall:.3f}")
        
        # 세션 상태 업데이트
        self.session.set_evaluation_completed(True)
        self.session.set_latest_evaluation_result(result.raw_data)
        
        # 네비게이션 버튼
        self._render_post_evaluation_navigation()
    
    def _render_post_evaluation_navigation(self) -> None:
        """평가 후 네비게이션"""
        st.markdown("---")
        self.show_info("💡 평가가 완료되었습니다! 결과를 확인해보세요.")
        
        col1, col2 = self.create_columns([1, 1])
        
        with col1:
            if st.button("📊 Overview 페이지로 이동", type="primary", use_container_width=True, key="goto_overview"):
                self.session.navigate_to("🎯 Overview")
                st.rerun()
        
        with col2:
            if st.button("📈 Historical 페이지로 이동", type="secondary", use_container_width=True, key="goto_historical"):
                self.session.navigate_to("📈 Historical")
                st.rerun()
        
        st.markdown("**또는** 사이드바에서 다른 페이지를 선택하세요.")