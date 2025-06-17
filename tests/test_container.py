"""
컨테이너 모듈 테스트
의존성 주입 컨테이너의 인스턴스 생성 및 의존성 관리 테스트
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# 프로젝트 루트 경로 추가
def add_project_root_to_path():
    current_path = Path(__file__).resolve()
    while current_path != current_path.parent:
        if (current_path / "pyproject.toml").exists():
            sys.path.insert(0, str(current_path))
            return current_path
        current_path = current_path.parent
    raise FileNotFoundError("프로젝트 루트를 찾을 수 없습니다.")

add_project_root_to_path()


class TestContainer:
    """컨테이너 클래스 테스트"""

    @patch('src.container.settings')
    @patch('src.container.GeminiAdapter')
    @patch('src.container.RagasEvalAdapterFactory')
    @patch('src.container.FileRepositoryFactory')
    @patch('src.container.RunEvaluationUseCase')
    def test_container_initialization(self, mock_use_case, mock_repo_factory, 
                                    mock_eval_factory, mock_gemini, mock_settings):
        """컨테이너 초기화 테스트"""
        # Mock settings
        mock_settings.GEMINI_API_KEY = "test_api_key"
        mock_settings.GEMINI_MODEL_NAME = "gemini-2.5-flash"
        mock_settings.GEMINI_REQUESTS_PER_MINUTE = 8
        mock_settings.GEMINI_EMBEDDING_MODEL_NAME = "models/text-embedding-004"
        mock_settings.EMBEDDING_REQUESTS_PER_MINUTE = 8
        
        from src.container import Container
        
        container = Container()
        
        # GeminiAdapter가 올바른 매개변수로 호출되었는지 확인
        mock_gemini.assert_called_once_with(
            api_key="test_api_key",
            model_name="gemini-2.5-flash",
            requests_per_minute=8
        )
        
        # 팩토리들이 올바르게 호출되었는지 확인
        mock_eval_factory.assert_called_once()
        mock_repo_factory.assert_called_once()
        
        # 유스케이스가 팩토리들과 함께 생성되었는지 확인
        mock_use_case.assert_called_once()

    @patch('src.container.settings')
    @patch('src.container.GeminiAdapter')
    @patch('src.container.RagasEvalAdapterFactory')
    @patch('src.container.FileRepositoryFactory')
    @patch('src.container.RunEvaluationUseCase')
    def test_container_run_evaluation_use_case(self, mock_use_case, mock_repo_factory,
                                             mock_eval_factory, mock_gemini, mock_settings):
        """평가 유스케이스 접근 테스트"""
        mock_settings.GEMINI_API_KEY = "test_api_key"
        mock_settings.GEMINI_MODEL_NAME = "gemini-2.5-flash"
        mock_settings.GEMINI_REQUESTS_PER_MINUTE = 8
        mock_settings.GEMINI_EMBEDDING_MODEL_NAME = "models/text-embedding-004"
        mock_settings.EMBEDDING_REQUESTS_PER_MINUTE = 8
        
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        from src.container import Container
        
        container = Container()
        use_case = container.run_evaluation_use_case
        
        # 유스케이스가 반환되는지 확인
        assert use_case is mock_use_case_instance

    @patch('src.container.settings')
    @patch('src.container.GeminiAdapter')
    def test_container_with_missing_config(self, mock_gemini, mock_settings):
        """설정이 누락된 경우 테스트"""
        # API 키 누락
        mock_settings.GEMINI_API_KEY = None
        mock_settings.GEMINI_MODEL_NAME = "gemini-2.5-flash" 
        mock_settings.GEMINI_REQUESTS_PER_MINUTE = 8
        mock_settings.GEMINI_EMBEDDING_MODEL_NAME = "models/text-embedding-004"
        mock_settings.EMBEDDING_REQUESTS_PER_MINUTE = 8
        
        mock_gemini.side_effect = ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        
        from src.container import Container
        
        with pytest.raises(ValueError, match="GEMINI_API_KEY가 설정되지 않았습니다."):
            Container()

    def test_dependency_injection_pattern(self):
        """의존성 주입 패턴 테스트"""
        
        class MockService:
            def __init__(self, dependency):
                self.dependency = dependency
        
        class MockDependency:
            def __init__(self, name):
                self.name = name
        
        # 의존성 주입 테스트
        dependency = MockDependency("test_dependency")
        service = MockService(dependency)
        
        assert service.dependency is dependency
        assert service.dependency.name == "test_dependency"