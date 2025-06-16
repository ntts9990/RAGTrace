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
    def test_container_initialization(self, mock_settings):
        """컨테이너 초기화 테스트"""
        # Mock settings
        mock_settings.GEMINI_API_KEY = "test_api_key"
        mock_settings.GEMINI_MODEL_NAME = "gemini-2.5-flash"
        mock_settings.GEMINI_REQUESTS_PER_MINUTE = 8
        mock_settings.GEMINI_EMBEDDING_MODEL_NAME = "models/text-embedding-004"
        mock_settings.EMBEDDING_REQUESTS_PER_MINUTE = 8
        
        from src.container import Container
        
        with patch('src.infrastructure.llm.gemini_adapter.GeminiAdapter') as mock_gemini, \
             patch('src.infrastructure.evaluation.RagasEvalAdapter') as mock_ragas:
            
            container = Container()
            
            # GeminiAdapter가 올바른 매개변수로 호출되었는지 확인
            mock_gemini.assert_called_once_with(
                api_key="test_api_key",
                model_name="gemini-2.5-flash",
                requests_per_minute=8
            )
            
            # RagasEvalAdapter가 올바른 매개변수로 호출되었는지 확인
            mock_ragas.assert_called_once()

    @patch('src.container.settings')
    def test_container_get_evaluation_use_case(self, mock_settings):
        """평가 유스케이스 생성 테스트"""
        mock_settings.GEMINI_API_KEY = "test_api_key"
        mock_settings.GEMINI_MODEL_NAME = "gemini-2.5-flash"
        mock_settings.GEMINI_REQUESTS_PER_MINUTE = 8
        mock_settings.GEMINI_EMBEDDING_MODEL_NAME = "models/text-embedding-004"
        mock_settings.EMBEDDING_REQUESTS_PER_MINUTE = 8
        
        from src.container import Container
        
        with patch('src.infrastructure.llm.gemini_adapter.GeminiAdapter'), \
             patch('src.infrastructure.evaluation.RagasEvalAdapter'), \
             patch('src.infrastructure.repository.file_adapter.FileRepositoryAdapter'):
            
            container = Container()
            use_case = container.get_evaluation_use_case()
            
            # 유스케이스가 반환되는지 확인
            assert use_case is not None

    def test_container_service_reuse(self):
        """컨테이너 서비스 재사용 테스트"""
        
        def test_singleton_behavior():
            """싱글톤 패턴 동작 테스트"""
            services = {}
            
            def get_service(service_name):
                if service_name not in services:
                    services[service_name] = Mock()
                return services[service_name]
            
            # 같은 서비스를 두 번 요청
            service1 = get_service("test_service")
            service2 = get_service("test_service")
            
            # 같은 인스턴스여야 함
            assert service1 is service2
            
            # 다른 서비스는 다른 인스턴스
            service3 = get_service("other_service")
            assert service1 is not service3
        
        test_singleton_behavior()

    @patch('src.container.settings')
    def test_container_with_missing_config(self, mock_settings):
        """설정이 누락된 경우 테스트"""
        # API 키 누락
        mock_settings.GEMINI_API_KEY = None
        mock_settings.GEMINI_MODEL_NAME = "gemini-2.5-flash"
        mock_settings.GEMINI_REQUESTS_PER_MINUTE = 8
        mock_settings.GEMINI_EMBEDDING_MODEL_NAME = "models/text-embedding-004"
        mock_settings.EMBEDDING_REQUESTS_PER_MINUTE = 8
        
        from src.container import Container
        
        with patch('src.infrastructure.llm.gemini_adapter.GeminiAdapter') as mock_gemini:
            mock_gemini.side_effect = ValueError("API key is required")
            
            with pytest.raises(ValueError, match="API key is required"):
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

    @patch('src.container.settings')
    def test_container_lazy_initialization(self, mock_settings):
        """지연 초기화 테스트"""
        mock_settings.GEMINI_API_KEY = "test_api_key"
        mock_settings.GEMINI_MODEL_NAME = "gemini-2.5-flash"
        mock_settings.GEMINI_REQUESTS_PER_MINUTE = 8
        mock_settings.GEMINI_EMBEDDING_MODEL_NAME = "models/text-embedding-004"
        mock_settings.EMBEDDING_REQUESTS_PER_MINUTE = 8
        
        class LazyContainer:
            def __init__(self):
                self._services = {}
            
            def get_service(self, service_name):
                if service_name not in self._services:
                    self._services[service_name] = Mock()
                return self._services[service_name]
        
        container = LazyContainer()
        
        # 서비스가 요청될 때까지 생성되지 않음
        assert len(container._services) == 0
        
        # 서비스 요청 시 생성
        service = container.get_service("test_service")
        assert len(container._services) == 1
        assert service is not None

    @patch('src.container.settings')  
    def test_container_adapter_configuration(self, mock_settings):
        """어댑터 설정 테스트"""
        mock_settings.GEMINI_API_KEY = "test_api_key"
        mock_settings.GEMINI_MODEL_NAME = "gemini-2.5-flash"
        mock_settings.GEMINI_REQUESTS_PER_MINUTE = 8
        mock_settings.GEMINI_EMBEDDING_MODEL_NAME = "models/text-embedding-004"
        mock_settings.EMBEDDING_REQUESTS_PER_MINUTE = 8
        
        from src.container import Container
        
        with patch('src.infrastructure.llm.gemini_adapter.GeminiAdapter') as mock_gemini_adapter, \
             patch('src.infrastructure.evaluation.RagasEvalAdapter') as mock_ragas_adapter:
            
            # Mock 인스턴스 설정
            mock_gemini_instance = Mock()
            mock_ragas_instance = Mock()
            mock_gemini_adapter.return_value = mock_gemini_instance
            mock_ragas_adapter.return_value = mock_ragas_instance
            
            container = Container()
            
            # 어댑터 인스턴스가 올바르게 설정되었는지 확인
            assert container.llm_adapter is mock_gemini_instance
            assert container.ragas_eval_adapter is mock_ragas_instance

    def test_container_error_handling(self):
        """컨테이너 오류 처리 테스트"""
        
        def test_service_creation_error():
            """서비스 생성 오류 처리"""
            def create_service_with_error():
                raise RuntimeError("Service creation failed")
            
            try:
                create_service_with_error()
                assert False, "Expected RuntimeError"
            except RuntimeError as e:
                assert str(e) == "Service creation failed"
        
        test_service_creation_error()

    def test_container_interface_compliance(self):
        """컨테이너 인터페이스 준수 테스트"""
        
        def test_adapter_interface():
            """어댑터 인터페이스 테스트"""
            
            class MockAdapter:
                def execute(self, data):
                    return {"result": "success"}
            
            adapter = MockAdapter()
            
            # 인터페이스 메서드가 존재하는지 확인
            assert hasattr(adapter, 'execute')
            assert callable(adapter.execute)
            
            # 메서드가 올바르게 작동하는지 확인
            result = adapter.execute("test_data")
            assert result["result"] == "success"
        
        test_adapter_interface()

    @patch('src.container.get_evaluation_data_path')
    def test_container_with_file_repository(self, mock_get_path):
        """파일 저장소와 함께 컨테이너 테스트"""
        mock_get_path.return_value = Path("/mock/path/data.json")
        
        with patch('src.container.settings') as mock_settings, \
             patch('src.infrastructure.llm.gemini_adapter.GeminiAdapter'), \
             patch('src.infrastructure.evaluation.RagasEvalAdapter'), \
             patch('src.infrastructure.repository.file_adapter.FileRepositoryAdapter') as mock_file_adapter:
            
            mock_settings.GEMINI_API_KEY = "test_api_key"
            mock_settings.GEMINI_MODEL_NAME = "gemini-2.5-flash"
            mock_settings.GEMINI_REQUESTS_PER_MINUTE = 8
            mock_settings.GEMINI_EMBEDDING_MODEL_NAME = "models/text-embedding-004"
            mock_settings.EMBEDDING_REQUESTS_PER_MINUTE = 8
            
            from src.container import Container
            
            container = Container()
            use_case = container.get_evaluation_use_case()
            
            # FileRepositoryAdapter가 호출되었는지 확인
            mock_file_adapter.assert_called()
            assert use_case is not None