"""End-to-End 평가 프로세스 통합 테스트

실제 사용자 시나리오를 기반으로 한 전체 평가 워크플로우 테스트
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.application.use_cases.run_evaluation import RunEvaluationUseCase
from src.domain.entities.evaluation_data import EvaluationData
from src.domain.entities.evaluation_result import EvaluationResult
from src.infrastructure.evaluation.ragas_adapter import RagasEvalAdapter
from src.infrastructure.llm.gemini_adapter import GeminiAdapter
from src.infrastructure.repository.file_adapter import FileRepositoryAdapter
from src.infrastructure.repository.sqlite_adapter import SQLiteAdapter


@pytest.fixture
def temp_evaluation_file():
    """테스트용 임시 평가 데이터 파일"""
    test_data = [
        {
            "question": "Python에서 리스트와 튜플의 차이점은 무엇인가요?",
            "contexts": [
                "리스트는 가변(mutable) 데이터 타입으로 생성 후 요소를 변경할 수 있습니다.",
                "튜플은 불변(immutable) 데이터 타입으로 생성 후 요소를 변경할 수 없습니다.",
                "리스트는 대괄호 []로 표현하고, 튜플은 소괄호 ()로 표현합니다.",
            ],
            "answer": "리스트는 가변 데이터 타입으로 요소를 변경할 수 있지만, 튜플은 불변 데이터 타입으로 요소를 변경할 수 없습니다.",
            "ground_truth": "리스트(list)는 가변(mutable) 객체로 생성 후 요소의 추가, 삭제, 수정이 가능합니다. 반면 튜플(tuple)은 불변(immutable) 객체로 생성 후 요소를 변경할 수 없습니다.",
        },
        {
            "question": "클래스와 객체의 차이점을 설명해주세요.",
            "contexts": [
                "클래스는 객체를 생성하기 위한 템플릿 또는 설계도입니다.",
                "객체는 클래스를 기반으로 생성된 실제 인스턴스입니다.",
                "클래스는 속성과 메서드를 정의하고, 객체는 이를 구현합니다.",
            ],
            "answer": "클래스는 객체를 만들기 위한 템플릿이고, 객체는 클래스로부터 생성된 실제 인스턴스입니다.",
            "ground_truth": "클래스(class)는 객체를 생성하기 위한 템플릿으로 속성과 메서드를 정의합니다. 객체(object)는 클래스를 기반으로 생성된 실제 인스턴스로 클래스에서 정의한 속성과 메서드를 가집니다.",
        },
    ]

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
        return Path(f.name)


@pytest.fixture
def temp_database():
    """테스트용 임시 데이터베이스"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return Path(f.name)


@pytest.fixture
def mock_gemini_responses():
    """Gemini API 응답 모킹"""
    return {
        "responses": [
            "이 답변은 정확하고 관련성이 높습니다.",
            "제공된 컨텍스트에 충실한 답변입니다.",
        ],
        "embeddings": [
            [0.1, 0.2, 0.3] * 100,  # 300차원 가상 임베딩
            [0.4, 0.5, 0.6] * 100,
        ],
    }


class TestEndToEndEvaluationWorkflow:
    """전체 평가 워크플로우 통합 테스트"""

    @patch("src.infrastructure.llm.gemini_adapter.ChatGoogleGenerativeAI")
    @patch("src.infrastructure.evaluation.ragas_adapter.evaluate")
    def test_complete_evaluation_workflow_success(
        self,
        mock_ragas_evaluate,
        mock_chat_genai,
        temp_evaluation_file,
        temp_database,
        mock_gemini_responses,
    ):
        """성공적인 전체 평가 워크플로우 테스트"""

        # 1. Mock 설정
        mock_llm_instance = mock_chat_genai.return_value
        mock_llm_instance.invoke.return_value = "Mock response"

        # RAGAS 평가 결과 모킹
        mock_result = MagicMock()
        mock_result.to_pandas.return_value.to_dict.return_value = {
            "faithfulness": [0.85, 0.78],
            "answer_relevancy": [0.92, 0.88],
            "context_recall": [0.78, 0.82],
            "context_precision": [0.88, 0.85],
        }
        mock_ragas_evaluate.return_value = mock_result

        # 2. 실제 컴포넌트 생성 (Mock 사용)
        llm_adapter = GeminiAdapter(
            api_key="fake-key", model_name="gemini-2.5-flash", requests_per_minute=100
        )

        file_adapter = FileRepositoryAdapter(file_path=str(temp_evaluation_file))
        ragas_adapter = RagasEvalAdapter(
            embedding_model_name="test-embedding-model",
            api_key="fake-key",
            embedding_requests_per_minute=100,
        )

        # 3. Use Case 실행
        use_case = RunEvaluationUseCase(
            llm_port=llm_adapter,
            repository_port=file_adapter,
            evaluation_runner=ragas_adapter,
        )

        # 4. 평가 실행
        result = use_case.execute()

        # 5. 결과 검증
        assert isinstance(result, EvaluationResult)
        assert result.faithfulness is not None
        assert result.answer_relevancy is not None

        # 메트릭 값이 유효한 범위에 있는지 확인
        assert 0.0 <= result.faithfulness <= 1.0
        assert 0.0 <= result.answer_relevancy <= 1.0
        assert 0.0 <= result.context_recall <= 1.0
        assert 0.0 <= result.context_precision <= 1.0

        # 6. 데이터베이스 저장 테스트
        db_adapter = SQLiteAdapter(temp_database)
        result_dict = result.to_dict()
        evaluation_id = db_adapter.save_evaluation(result_dict)

        # 저장된 데이터 검증
        saved_result = db_adapter.get_evaluation(evaluation_id)
        assert saved_result is not None
        assert saved_result["id"] == evaluation_id

        # 7. 정리
        temp_evaluation_file.unlink()
        temp_database.unlink()

    def test_evaluation_with_invalid_data_file(self):
        """잘못된 데이터 파일로 평가 시도"""
        file_adapter = FileRepositoryAdapter(file_path="non_existent_file.json")
        data_list = file_adapter.load_data()
        # FileRepositoryAdapter는 예외를 발생시키지 않고 빈 리스트를 반환
        assert data_list == []

    @patch("src.infrastructure.llm.gemini_adapter.ChatGoogleGenerativeAI")
    def test_evaluation_with_api_error(self, mock_chat_genai, temp_evaluation_file):
        """API 오류 발생 시 처리 테스트"""

        # API 오류 모킹
        mock_chat_genai.side_effect = Exception("API 연결 오류")

        llm_adapter = GeminiAdapter(
            api_key="fake-api-key",
            model_name="gemini-2.5-flash",
            requests_per_minute=100,
        )

        file_adapter = FileRepositoryAdapter(file_path=str(temp_evaluation_file))
        ragas_adapter = RagasEvalAdapter(
            embedding_model_name="fake-embedding-model",
            api_key="fake-api-key",
            embedding_requests_per_minute=100,
        )

        use_case = RunEvaluationUseCase(
            llm_port=llm_adapter,
            repository_port=file_adapter,
            evaluation_runner=ragas_adapter,
        )

        # API 오류 시 적절한 예외 발생 확인
        with pytest.raises(Exception):
            use_case.execute()

        temp_evaluation_file.unlink()


class TestDataFlowIntegration:
    """데이터 흐름 통합 테스트"""

    def test_data_loading_and_validation(self, temp_evaluation_file):
        """데이터 로딩 및 유효성 검증 통합 테스트"""

        # 1. 파일에서 데이터 로딩
        file_adapter = FileRepositoryAdapter(file_path=str(temp_evaluation_file))
        evaluation_data_list = file_adapter.load_data()

        # 2. 로딩된 데이터 검증
        assert len(evaluation_data_list) == 2

        for data in evaluation_data_list:
            assert isinstance(data, EvaluationData)
            assert data.question.strip() != ""
            assert len(data.contexts) > 0
            assert data.answer.strip() != ""
            assert data.ground_truth.strip() != ""

        # 3. 정리
        temp_evaluation_file.unlink()

    def test_evaluation_result_serialization(self, temp_database):
        """평가 결과 직렬화/역직렬화 테스트"""

        # 1. 평가 결과 생성
        result = EvaluationResult(
            faithfulness=0.85,
            answer_relevancy=0.92,
            context_recall=0.78,
            context_precision=0.88,
            ragas_score=0.86,
        )

        # 2. 딕셔너리로 변환
        result_dict = result.to_dict()
        assert "faithfulness" in result_dict
        assert result_dict["faithfulness"] == 0.85

        # 3. 데이터베이스 저장/조회
        db_adapter = SQLiteAdapter(temp_database)
        evaluation_id = db_adapter.save_evaluation(result_dict)

        retrieved_data = db_adapter.get_evaluation(evaluation_id)
        assert retrieved_data["faithfulness"] == 0.85
        assert retrieved_data["answer_relevancy"] == 0.92

        # 4. 정리
        temp_database.unlink()


class TestErrorHandlingIntegration:
    """오류 처리 통합 테스트"""

    def test_malformed_evaluation_data(self):
        """잘못된 형식의 평가 데이터 처리"""

        # 잘못된 JSON 파일 생성
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            invalid_file = Path(f.name)

        try:
            file_adapter = FileRepositoryAdapter(file_path=str(invalid_file))
            data_list = file_adapter.load_data()
            # FileRepositoryAdapter는 예외를 발생시키지 않고 빈 리스트를 반환
            assert data_list == []
        finally:
            invalid_file.unlink()

    def test_incomplete_evaluation_data(self):
        """불완전한 평가 데이터 처리"""

        # 필수 필드가 누락된 데이터
        incomplete_data = [
            {
                "question": "테스트 질문",
                # contexts 누락
                "answer": "테스트 답변",
                # ground_truth 누락
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(incomplete_data, f)
            incomplete_file = Path(f.name)

        try:
            file_adapter = FileRepositoryAdapter(file_path=str(incomplete_file))
            data_list = file_adapter.load_data()
            # FileRepositoryAdapter는 예외를 발생시키지 않고 빈 리스트를 반환
            assert data_list == []
        finally:
            incomplete_file.unlink()

    def test_database_connection_error(self):
        """데이터베이스 연결 오류 처리"""

        # 읽기 전용 경로에 DB 생성 시도
        readonly_path = Path("/dev/null/impossible.db")

        with pytest.raises((PermissionError, OSError)):
            db_adapter = SQLiteAdapter(readonly_path)
            db_adapter.save_evaluation({"test": "data"})


class TestPerformanceIntegration:
    """성능 관련 통합 테스트"""

    @patch("src.infrastructure.llm.gemini_adapter.ChatGoogleGenerativeAI")
    @patch("src.infrastructure.evaluation.ragas_adapter.evaluate")
    def test_rate_limiting_integration(
        self, mock_ragas_evaluate, mock_chat_genai, temp_evaluation_file
    ):
        """Rate limiting 통합 테스트"""

        # Mock 설정
        mock_llm_instance = mock_chat_genai.return_value
        mock_llm_instance.invoke.return_value = "Mock"

        mock_result = MagicMock()
        mock_result.to_pandas.return_value.to_dict.return_value = {
            "faithfulness": [0.85],
            "answer_relevancy": [0.92],
        }
        mock_ragas_evaluate.return_value = mock_result

        # 낮은 rate limit 설정
        llm_adapter = GeminiAdapter(
            api_key="fake-api-key",
            model_name="gemini-2.5-flash",
            requests_per_minute=1,  # 매우 낮은 제한
        )

        file_adapter = FileRepositoryAdapter(file_path=str(temp_evaluation_file))
        ragas_adapter = RagasEvalAdapter(
            embedding_model_name="fake-embedding-model",
            api_key="fake-api-key",
            embedding_requests_per_minute=100,
        )

        use_case = RunEvaluationUseCase(
            llm_port=llm_adapter,
            repository_port=file_adapter,
            evaluation_runner=ragas_adapter,
        )

        # Rate limiting이 적용된 상태에서도 평가 실행 가능해야 함
        result = use_case.execute()
        assert isinstance(result, EvaluationResult)

        temp_evaluation_file.unlink()

    def test_large_dataset_handling(self):
        """대용량 데이터셋 처리 테스트"""

        # 100개 평가 항목 생성
        large_dataset = []
        for i in range(100):
            large_dataset.append(
                {
                    "question": f"테스트 질문 {i}",
                    "contexts": [f"컨텍스트 {i}-1", f"컨텍스트 {i}-2"],
                    "answer": f"테스트 답변 {i}",
                    "ground_truth": f"정답 {i}",
                }
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(large_dataset, f)
            large_file = Path(f.name)

        try:
            # 대용량 데이터 로딩 테스트
            file_adapter = FileRepositoryAdapter(file_path=str(large_file))
            evaluation_data_list = file_adapter.load_data()

            assert len(evaluation_data_list) == 100

            # 각 데이터가 올바르게 파싱되었는지 확인
            for i, data in enumerate(evaluation_data_list):
                assert isinstance(data, EvaluationData)
                assert f"테스트 질문 {i}" in data.question
        finally:
            large_file.unlink()


class TestRealWorldScenarios:
    """실제 사용 시나리오 테스트"""

    @patch("src.infrastructure.llm.gemini_adapter.ChatGoogleGenerativeAI")
    @patch("src.infrastructure.evaluation.ragas_adapter.evaluate")
    def test_typical_user_workflow(
        self, mock_ragas_evaluate, mock_chat_genai, temp_evaluation_file, temp_database
    ):
        """일반적인 사용자 워크플로우 시뮬레이션"""

        # Mock 설정
        mock_llm_instance = mock_chat_genai.return_value
        mock_llm_instance.invoke.return_value = "Mock"

        mock_result = MagicMock()
        mock_result.to_pandas.return_value.to_dict.return_value = {
            "faithfulness": [0.85, 0.78],
            "answer_relevancy": [0.92, 0.88],
            "context_recall": [0.78, 0.82],
            "context_precision": [0.88, 0.85],
        }
        mock_ragas_evaluate.return_value = mock_result

        # 실제 사용자 시나리오:
        # 1. 평가 데이터 준비 및 검증
        file_adapter = FileRepositoryAdapter(file_path=str(temp_evaluation_file))
        data_list = file_adapter.load_data()
        assert len(data_list) > 0

        # 2. LLM 설정 및 평가 실행
        llm_adapter = GeminiAdapter(
            api_key="fake-api-key",
            model_name="gemini-2.5-flash",
            requests_per_minute=100,
        )
        ragas_adapter = RagasEvalAdapter(
            embedding_model_name="fake-embedding-model",
            api_key="fake-api-key",
            embedding_requests_per_minute=100,
        )

        use_case = RunEvaluationUseCase(
            llm_port=llm_adapter,
            repository_port=file_adapter,
            evaluation_runner=ragas_adapter,
        )

        result = use_case.execute()

        # 3. 결과 검증 및 저장
        assert isinstance(result, EvaluationResult)

        db_adapter = SQLiteAdapter(temp_database)
        evaluation_id = db_adapter.save_evaluation(result.to_dict())

        # 4. 결과 조회 및 분석
        saved_result = db_adapter.get_evaluation(evaluation_id)
        assert saved_result is not None

        # 5. 통계 확인
        stats = db_adapter.get_statistics()
        assert stats["total_evaluations"] >= 1

        # 6. 정리
        temp_evaluation_file.unlink()
        temp_database.unlink()

    def test_multiple_evaluation_comparison(self, temp_database):
        """여러 평가 결과 비교 시나리오"""

        db_adapter = SQLiteAdapter(temp_database)

        # 여러 평가 결과 생성 및 저장
        evaluation_results = [
            {
                "faithfulness": 0.85,
                "answer_relevancy": 0.92,
                "timestamp": "2025-01-01T10:00:00",
                "metadata": {"model": "gemini-2.5-flash", "version": "v1"},
            },
            {
                "faithfulness": 0.88,
                "answer_relevancy": 0.89,
                "timestamp": "2025-01-01T11:00:00",
                "metadata": {"model": "gemini-2.5-flash", "version": "v2"},
            },
            {
                "faithfulness": 0.82,
                "answer_relevancy": 0.95,
                "timestamp": "2025-01-01T12:00:00",
                "metadata": {"model": "gpt-4", "version": "v1"},
            },
        ]

        saved_ids = []
        for result in evaluation_results:
            eval_id = db_adapter.save_evaluation(result)
            saved_ids.append(eval_id)

        # 모든 평가 결과 조회
        all_evaluations = db_adapter.get_all_evaluations()
        assert len(all_evaluations) == 3

        # 최신 순으로 정렬되어 있는지 확인
        timestamps = [eval_data["timestamp"] for eval_data in all_evaluations]
        assert timestamps == sorted(timestamps, reverse=True)

        # 통계 계산 확인
        stats = db_adapter.get_statistics()
        assert stats["total_evaluations"] == 3

        # 평균 faithfulness 계산 검증 (0.85 + 0.88 + 0.82) / 3 ≈ 0.85
        expected_avg = (0.85 + 0.88 + 0.82) / 3
        assert abs(stats["average_scores"]["faithfulness"] - expected_avg) < 0.01

        temp_database.unlink()
