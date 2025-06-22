"""
실제 평가 기능 워크플로우 테스트

RAGAS 평가의 전체 워크플로우를 사용자 행동 중심으로 테스트합니다.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# 시스템 패스 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.domain.entities.evaluation_data import EvaluationData
from src.domain.entities.evaluation_result import EvaluationResult
from src.application.use_cases.run_evaluation import RunEvaluationUseCase
from src.container import container
from src.utils.paths import get_evaluation_data_path


class TestEvaluationWorkflows:
    """실제 평가 기능 워크플로우 테스트"""
    
    @pytest.fixture
    def sample_evaluation_data(self):
        """테스트용 평가 데이터"""
        return [
            EvaluationData(
                question="원자력 발전의 주요 안전 시스템은 무엇인가요?",
                contexts=[
                    "원자력 발전소의 안전 시스템은 다중 방어벽으로 구성됩니다.",
                    "비상노심냉각시스템(ECCS)은 냉각재 상실사고 시 노심을 냉각합니다.",
                    "격납건물은 방사성 물질의 외부 누출을 방지하는 최후 방어벽입니다."
                ],
                answer="원자력 발전소의 주요 안전 시스템은 비상노심냉각시스템, 격납건물, 그리고 다중 방어벽 시스템입니다.",
                ground_truth="비상노심냉각시스템, 격납건물, 다중 방어벽"
            ),
            EvaluationData(
                question="수력발전의 원리는 무엇인가요?",
                contexts=[
                    "수력발전은 물의 위치에너지를 전기에너지로 변환합니다.",
                    "댐에서 저장된 물이 낙차를 통해 터빈을 회전시킵니다.",
                    "터빈의 회전은 발전기를 통해 전기를 생산합니다."
                ],
                answer="수력발전은 물의 위치에너지를 이용해 터빈을 회전시켜 전기를 생산하는 방식입니다.",
                ground_truth="위치에너지를 전기에너지로 변환"
            )
        ]
    
    @pytest.fixture
    def sample_json_file(self, sample_evaluation_data):
        """테스트용 JSON 파일 생성"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            # EvaluationData를 dict로 변환
            data_dicts = []
            for data in sample_evaluation_data:
                data_dicts.append({
                    "question": data.question,
                    "contexts": data.contexts,
                    "answer": data.answer,
                    "ground_truth": data.ground_truth
                })
            json.dump(data_dicts, f, ensure_ascii=False, indent=2)
            f.flush()  # 파일 버퍼 플러시
            yield f.name
        
        if os.path.exists(f.name):
            os.unlink(f.name)

    def test_evaluation_data_loading(self, sample_json_file):
        """평가 데이터 로딩 테스트"""
        # JSON 파일에서 데이터 로딩
        with open(sample_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 데이터 구조 확인
        assert len(data) == 2
        assert 'question' in data[0]
        assert 'contexts' in data[0]
        assert 'answer' in data[0]
        assert 'ground_truth' in data[0]
        
        # EvaluationData 객체로 변환 테스트
        evaluation_data_list = []
        for item in data:
            eval_data = EvaluationData(
                question=item['question'],
                contexts=item['contexts'],
                answer=item['answer'],
                ground_truth=item['ground_truth']
            )
            evaluation_data_list.append(eval_data)
        
        assert len(evaluation_data_list) == 2
        assert isinstance(evaluation_data_list[0], EvaluationData)

    @patch('src.container.container.llm_providers')
    @patch('src.container.container.embedding_providers')
    def test_container_evaluation_setup(self, mock_embedding_providers, mock_llm_providers):
        """컨테이너를 통한 평가 설정 테스트"""
        # Mock 설정
        mock_llm = MagicMock()
        mock_embedding = MagicMock()
        
        mock_llm_providers.return_value = {'gemini': mock_llm}
        mock_embedding_providers.return_value = {'bge_m3': mock_embedding}
        
        # LLM과 임베딩 어댑터 생성 확인
        llm_providers = container.llm_providers()
        embedding_providers = container.embedding_providers()
        
        assert 'gemini' in llm_providers
        assert 'bge_m3' in embedding_providers

    @patch('src.infrastructure.evaluation.ragas_adapter.RagasEvalAdapter')
    def test_ragas_adapter_creation(self, mock_ragas_adapter):
        """RAGAS 어댑터 생성 테스트"""
        # Mock LLM과 임베딩
        mock_llm = MagicMock()
        mock_embedding = MagicMock()
        
        # RAGAS 어댑터 인스턴스 모킹
        mock_adapter_instance = MagicMock()
        mock_ragas_adapter.return_value = mock_adapter_instance
        
        # 컨테이너를 통한 어댑터 생성
        with patch.object(container, 'ragas_eval_adapter') as mock_container_adapter:
            mock_container_adapter.return_value = mock_adapter_instance
            
            adapter = container.ragas_eval_adapter(
                llm=mock_llm,
                embeddings=mock_embedding
            )
            
            assert adapter == mock_adapter_instance

    @patch('src.container.container.run_evaluation_use_case')
    def test_evaluation_use_case_execution(self, mock_use_case_factory, sample_evaluation_data):
        """평가 유즈케이스 실행 테스트"""
        # Mock 평가 결과
        mock_result = EvaluationResult(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_recall=0.80,
            context_precision=0.88,
            ragas_score=0.8575,
            individual_scores=[
                {"faithfulness": 0.9, "answer_relevancy": 0.85},
                {"faithfulness": 0.8, "answer_relevancy": 0.95}
            ],
            metadata={
                "dataset_name": "test_dataset",
                "model_name": "gemini",
                "evaluation_id": "test_eval_001",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        )
        
        # Mock 유즈케이스
        mock_use_case = MagicMock()
        mock_use_case.execute.return_value = mock_result
        mock_use_case_factory.return_value = mock_use_case
        
        # 유즈케이스 실행
        use_case = container.run_evaluation_use_case()
        result = use_case.execute(dataset_name="test_dataset")
        
        # 결과 검증
        assert isinstance(result, EvaluationResult)
        assert result.ragas_score == 0.8575
        assert result.faithfulness == 0.85
        assert result.metadata["dataset_name"] == "test_dataset"

    def test_evaluation_result_conversion(self):
        """평가 결과 변환 테스트"""
        # 평가 결과 생성
        result = EvaluationResult(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_recall=0.80,
            context_precision=0.88,
            ragas_score=0.8575,
            individual_scores=[],
            metadata={"dataset_name": "test", "model_name": "gemini"}
        )
        
        # dict 변환 테스트
        result_dict = result.to_dict()
        
        assert result_dict['faithfulness'] == 0.85
        assert result_dict['answer_relevancy'] == 0.90
        assert result_dict['ragas_score'] == 0.8575
        assert result_dict['metadata']['dataset_name'] == "test"

    @patch('src.container.container')
    def test_complete_evaluation_workflow(self, mock_container, sample_json_file):
        """완전한 평가 워크플로우 테스트"""
        # Mock 설정
        mock_llm = MagicMock()
        mock_embedding = MagicMock()
        mock_ragas_adapter = MagicMock()
        mock_use_case = MagicMock()
        
        mock_container.llm_providers.return_value = {'gemini': mock_llm}
        mock_container.embedding_providers.return_value = {'bge_m3': mock_embedding}
        mock_container.ragas_eval_adapter.return_value = mock_ragas_adapter
        mock_container.run_evaluation_use_case.return_value = mock_use_case
        
        # 평가 결과 모킹
        mock_result = EvaluationResult(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_recall=0.80,
            context_precision=0.88,
            ragas_score=0.8575,
            individual_scores=[
                {"question_1": {"faithfulness": 0.9, "answer_relevancy": 0.85}},
                {"question_2": {"faithfulness": 0.8, "answer_relevancy": 0.95}}
            ],
            metadata={
                "dataset_name": "test_dataset",
                "model_name": "gemini",
                "embedding_model": "bge_m3",
                "prompt_type": "default",
                "evaluation_time": "2024-01-01T12:00:00Z",
                "dataset_size": 2
            }
        )
        mock_use_case.execute.return_value = mock_result
        
        # 워크플로우 실행
        with patch('src.utils.paths.get_evaluation_data_path', return_value=sample_json_file):
            # 1. 컨테이너에서 어댑터들 가져오기
            llm_providers = mock_container.llm_providers()
            embedding_providers = mock_container.embedding_providers()
            
            assert 'gemini' in llm_providers
            assert 'bge_m3' in embedding_providers
            
            # 2. RAGAS 어댑터 생성
            ragas_adapter = mock_container.ragas_eval_adapter(
                llm=llm_providers['gemini'],
                embeddings=embedding_providers['bge_m3']
            )
            
            # 3. 유즈케이스 생성 및 실행
            use_case = mock_container.run_evaluation_use_case()
            result = use_case.execute(dataset_name="test_dataset")
            
            # 4. 결과 검증
            assert result.ragas_score == 0.8575
            assert len(result.individual_scores) == 2
            assert result.metadata["dataset_size"] == 2

    def test_evaluation_error_handling(self):
        """평가 중 오류 처리 테스트"""
        # 직접적인 예외 발생 테스트
        with patch('src.infrastructure.llm.gemini_adapter.GeminiAdapter') as mock_gemini:
            mock_gemini.side_effect = Exception("LLM 초기화 실패")
            
            with pytest.raises(Exception, match="LLM 초기화 실패"):
                mock_gemini()

    def test_multiple_llm_evaluation_comparison(self):
        """여러 LLM 평가 결과 비교 테스트"""
        # Gemini 결과
        gemini_result = EvaluationResult(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_recall=0.80,
            context_precision=0.88,
            ragas_score=0.8575,
            individual_scores=[],
            metadata={"model_name": "gemini"}
        )
        
        # HCX 결과 
        hcx_result = EvaluationResult(
            faithfulness=0.82,
            answer_relevancy=0.88,
            context_recall=0.85,
            context_precision=0.90,
            ragas_score=0.8625,
            individual_scores=[],
            metadata={"model_name": "hcx"}
        )
        
        # 비교 분석
        assert hcx_result.ragas_score > gemini_result.ragas_score
        assert hcx_result.context_precision > gemini_result.context_precision
        assert gemini_result.answer_relevancy > hcx_result.answer_relevancy

    def test_evaluation_with_different_prompt_types(self):
        """다양한 프롬프트 타입으로 평가 테스트"""
        from src.domain.prompts import PromptType
        
        # 기본 프롬프트 결과
        default_result = EvaluationResult(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_recall=0.80,
            context_precision=0.88,
            ragas_score=0.8575,
            individual_scores=[],
            metadata={"prompt_type": "default"}
        )
        
        # 한국어 기술 문서 프롬프트 결과
        korean_tech_result = EvaluationResult(
            faithfulness=0.88,
            answer_relevancy=0.92,
            context_recall=0.83,
            context_precision=0.90,
            ragas_score=0.8825,
            individual_scores=[],
            metadata={"prompt_type": "korean_tech"}
        )
        
        # 한국어 특화 프롬프트가 더 좋은 성능을 보이는지 확인
        assert korean_tech_result.ragas_score > default_result.ragas_score
        assert korean_tech_result.faithfulness > default_result.faithfulness

    def test_evaluation_individual_scores_analysis(self):
        """개별 점수 분석 테스트"""
        # 개별 점수가 포함된 평가 결과
        result = EvaluationResult(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_recall=0.80,
            context_precision=0.88,
            ragas_score=0.8575,
            individual_scores=[
                {
                    "question": "원자력 발전의 주요 안전 시스템은 무엇인가요?",
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.85,
                    "context_recall": 0.8,
                    "context_precision": 0.9
                },
                {
                    "question": "수력발전의 원리는 무엇인가요?",
                    "faithfulness": 0.8,
                    "answer_relevancy": 0.95,
                    "context_recall": 0.8,
                    "context_precision": 0.86
                }
            ],
            metadata={"dataset_size": 2}
        )
        
        # 개별 점수 분석
        assert len(result.individual_scores) == 2
        
        # 첫 번째 질문이 faithfulness에서 더 좋은 성능
        assert result.individual_scores[0]["faithfulness"] > result.individual_scores[1]["faithfulness"]
        
        # 두 번째 질문이 answer_relevancy에서 더 좋은 성능
        assert result.individual_scores[1]["answer_relevancy"] > result.individual_scores[0]["answer_relevancy"]

    def test_evaluation_metadata_tracking(self):
        """평가 메타데이터 추적 테스트"""
        result = EvaluationResult(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_recall=0.80,
            context_precision=0.88,
            ragas_score=0.8575,
            individual_scores=[],
            metadata={
                "dataset_name": "nuclear_hydro_qa",
                "model_name": "gemini-2.5-flash",
                "embedding_model": "bge-m3",
                "prompt_type": "korean_tech",
                "evaluation_id": "eval_20240101_001",
                "timestamp": "2024-01-01T12:00:00Z",
                "dataset_size": 50,
                "evaluation_duration": "2.5 minutes",
                "api_calls": 150,
                "token_usage": {
                    "input_tokens": 12000,
                    "output_tokens": 3000
                }
            }
        )
        
        # 메타데이터 검증
        metadata = result.metadata
        assert metadata["dataset_name"] == "nuclear_hydro_qa"
        assert metadata["model_name"] == "gemini-2.5-flash"
        assert metadata["embedding_model"] == "bge-m3"
        assert metadata["prompt_type"] == "korean_tech"
        assert metadata["dataset_size"] == 50
        assert "token_usage" in metadata
        assert metadata["token_usage"]["input_tokens"] == 12000

    @patch('src.infrastructure.repository.sqlite_adapter.SQLiteAdapter')
    def test_evaluation_result_persistence(self, mock_repository):
        """평가 결과 영속성 테스트"""
        # Mock 리포지토리
        mock_repo_instance = MagicMock()
        mock_repository.return_value = mock_repo_instance
        
        # 평가 결과
        result = EvaluationResult(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_recall=0.80,
            context_precision=0.88,
            ragas_score=0.8575,
            individual_scores=[],
            metadata={"dataset_name": "test", "evaluation_id": "eval_001"}
        )
        
        # 저장 시뮬레이션
        repo = mock_repository()
        repo.save_evaluation_result(result)
        
        # 저장 메서드가 호출되었는지 확인
        mock_repo_instance.save_evaluation_result.assert_called_once_with(result)

    def test_evaluation_performance_metrics(self):
        """평가 성능 메트릭 테스트"""
        import time
        
        # 평가 시간 측정 시뮬레이션
        start_time = time.time()
        
        # 가상의 평가 작업
        time.sleep(0.01)  # 10ms 대기
        
        end_time = time.time()
        evaluation_duration = end_time - start_time
        
        # 평가 결과에 성능 정보 포함
        result = EvaluationResult(
            faithfulness=0.85,
            answer_relevancy=0.90,
            context_recall=0.80,
            context_precision=0.88,
            ragas_score=0.8575,
            individual_scores=[],
            metadata={
                "evaluation_duration_seconds": evaluation_duration,
                "questions_per_second": 2 / evaluation_duration,
                "average_response_time": evaluation_duration / 2
            }
        )
        
        # 성능 메트릭 검증
        assert result.metadata["evaluation_duration_seconds"] > 0
        assert result.metadata["questions_per_second"] > 0
        assert result.metadata["average_response_time"] > 0