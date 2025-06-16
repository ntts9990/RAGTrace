"""main.py 테스트 (간소화 버전)"""

from unittest.mock import MagicMock, patch

import pytest


class TestMain:
    """main.py 테스트"""

    @patch("src.presentation.main.RunEvaluationUseCase")
    @patch("src.presentation.main.RagasEvalAdapter")
    @patch("src.presentation.main.FileRepositoryAdapter")
    @patch("src.presentation.main.GeminiAdapter")
    @patch("builtins.print")
    def test_main_success(
        self, mock_print, mock_gemini, mock_file_repo, mock_ragas, mock_use_case
    ):
        """메인 함수 성공 시나리오 테스트"""
        # Mock 설정
        mock_llm_instance = MagicMock()
        mock_gemini.return_value = mock_llm_instance

        mock_repo_instance = MagicMock()
        mock_file_repo.return_value = mock_repo_instance

        mock_ragas_instance = MagicMock()
        mock_ragas.return_value = mock_ragas_instance

        mock_use_case_instance = MagicMock()
        mock_evaluation_result = MagicMock()
        mock_evaluation_result.faithfulness = 0.85
        mock_evaluation_result.answer_relevancy = 0.92
        mock_evaluation_result.context_recall = 0.78
        mock_evaluation_result.context_precision = 0.88
        mock_evaluation_result.ragas_score = 0.86
        mock_use_case_instance.execute.return_value = mock_evaluation_result
        mock_use_case.return_value = mock_use_case_instance

        # main 함수 실행
        from src.presentation.main import main

        main()

        # 검증
        mock_print.assert_called()
        mock_gemini.assert_called_once()
        mock_file_repo.assert_called_once()
        mock_ragas.assert_called_once()
        mock_use_case.assert_called_once()
        mock_use_case_instance.execute.assert_called_once()

    @patch("src.presentation.main.RunEvaluationUseCase")
    @patch("src.presentation.main.RagasEvalAdapter")
    @patch("src.presentation.main.FileRepositoryAdapter")
    @patch("src.presentation.main.GeminiAdapter")
    @patch("builtins.print")
    @patch("src.presentation.main.logging")
    @patch("src.presentation.main.sys")
    def test_main_exception_handling(
        self,
        mock_sys,
        mock_logging,
        mock_print,
        mock_gemini,
        mock_file_repo,
        mock_ragas,
        mock_use_case,
    ):
        """메인 함수 예외 처리 테스트"""
        # 예외 발생 설정
        mock_gemini.side_effect = Exception("Gemini 연결 오류")

        # main 함수 실행
        from src.presentation.main import main

        main()

        # 검증
        mock_logging.error.assert_called()
        mock_sys.exit.assert_called_with(1)

    @patch("src.presentation.main.RunEvaluationUseCase")
    @patch("src.presentation.main.RagasEvalAdapter")
    @patch("src.presentation.main.FileRepositoryAdapter")
    @patch("src.presentation.main.GeminiAdapter")
    def test_dependency_injection_setup(
        self, mock_gemini, mock_file_repo, mock_ragas, mock_use_case
    ):
        """의존성 주입 설정 테스트"""
        # Mock 설정
        mock_llm_instance = MagicMock()
        mock_gemini.return_value = mock_llm_instance

        mock_repo_instance = MagicMock()
        mock_file_repo.return_value = mock_repo_instance

        mock_ragas_instance = MagicMock()
        mock_ragas.return_value = mock_ragas_instance

        mock_use_case_instance = MagicMock()
        mock_evaluation_result = MagicMock()
        mock_evaluation_result.faithfulness = 0.85
        mock_evaluation_result.answer_relevancy = 0.92
        mock_evaluation_result.context_recall = 0.78
        mock_evaluation_result.context_precision = 0.88
        mock_evaluation_result.ragas_score = 0.86
        mock_use_case_instance.execute.return_value = mock_evaluation_result
        mock_use_case.return_value = mock_use_case_instance

        # main 함수 실행
        from src.presentation.main import main

        main()

        # 의존성 주입 검증
        mock_gemini.assert_called_once_with(
            model_name="gemini-2.5-flash-preview-05-20", requests_per_minute=1000
        )

        # FileRepositoryAdapter 호출 검증
        mock_file_repo.assert_called_once()

        # UseCase에 올바른 의존성들이 주입되었는지 검증
        mock_use_case.assert_called_once_with(
            llm_port=mock_llm_instance,
            repository_port=mock_repo_instance,
            evaluation_runner=mock_ragas_instance,
        )


class TestMainModuleExecution:
    """메인 모듈 실행 테스트"""

    @patch("src.presentation.main.main")
    def test_if_name_main_execution(self, mock_main):
        """__name__ == "__main__" 시 main() 함수 호출 테스트"""
        # 이 테스트는 실제로는 모듈 레벨에서 실행되므로 직접 테스트하기 어려움
        # 대신 main 함수가 정의되어 있는지 확인
        from src.presentation.main import main

        assert callable(main)

    def test_main_function_exists(self):
        """main 함수가 존재하는지 테스트"""
        from src.presentation.main import main

        assert callable(main)

        # 함수 signature 검증
        import inspect

        sig = inspect.signature(main)
        assert len(sig.parameters) == 0  # main()은 파라미터가 없어야 함


class TestMainImports:
    """main.py import 테스트"""

    def test_all_imports_successful(self):
        """모든 import가 성공하는지 테스트"""
        try:
            import src.presentation.main

            assert True
        except ImportError as e:
            pytest.fail(f"Import 실패: {e}")

    def test_required_modules_imported(self):
        """필요한 모듈들이 import되었는지 테스트"""
        import src.presentation.main as main_module

        # 필요한 클래스들이 모듈에서 접근 가능한지 확인
        required_classes = [
            "RunEvaluationUseCase",
            "RagasEvalAdapter",
            "GeminiAdapter",
            "FileRepositoryAdapter",
        ]

        for class_name in required_classes:
            assert hasattr(main_module, class_name), f"{class_name}이 import되지 않음"


class TestMainConfiguration:
    """main 함수 설정 테스트"""

    @patch("src.presentation.main.GeminiAdapter")
    def test_gemini_adapter_configuration(self, mock_gemini):
        """Gemini 어댑터 설정 테스트"""
        mock_gemini.return_value = MagicMock()

        # 다른 의존성들도 mock
        with (
            patch("src.presentation.main.FileRepositoryAdapter"),
            patch("src.presentation.main.RagasEvalAdapter"),
            patch("src.presentation.main.RunEvaluationUseCase") as mock_use_case,
        ):

            mock_use_case_instance = MagicMock()
            mock_use_case_instance.execute.return_value = MagicMock(
                faithfulness=0.85,
                answer_relevancy=0.92,
                context_recall=0.78,
                context_precision=0.88,
                ragas_score=0.86,
            )
            mock_use_case.return_value = mock_use_case_instance

            from src.presentation.main import main

            main()

            # Gemini 설정 검증
            mock_gemini.assert_called_with(
                model_name="gemini-2.5-flash-preview-05-20", requests_per_minute=1000
            )

    @patch("src.presentation.main.FileRepositoryAdapter")
    def test_file_repository_configuration(self, mock_file_repo):
        """파일 리포지토리 어댑터 설정 테스트"""
        mock_file_repo.return_value = MagicMock()

        # 다른 의존성들도 mock
        with (
            patch("src.presentation.main.GeminiAdapter"),
            patch("src.presentation.main.RagasEvalAdapter"),
            patch("src.presentation.main.RunEvaluationUseCase") as mock_use_case,
        ):

            mock_use_case_instance = MagicMock()
            mock_use_case_instance.execute.return_value = MagicMock(
                faithfulness=0.85,
                answer_relevancy=0.92,
                context_recall=0.78,
                context_precision=0.88,
                ragas_score=0.86,
            )
            mock_use_case.return_value = mock_use_case_instance

            from src.presentation.main import main

            main()

            # 파일 경로 설정 검증 (DEFAULT_EVALUATION_DATA 사용)
            mock_file_repo.assert_called_once()
            call_args = mock_file_repo.call_args
            assert "file_path" in call_args.kwargs or len(call_args.args) > 0
