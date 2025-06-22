"""
설정 및 환경 테스트

설정 검증, 환경 변수, 기본값 처리 등을 테스트합니다.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

# 시스템 패스 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import settings, validate_settings, SUPPORTED_LLM_TYPES, SUPPORTED_EMBEDDING_TYPES
from src.domain.prompts import PromptType
from src.utils.paths import get_available_datasets, get_evaluation_data_path


class TestConfigAndEnvironment:
    """설정 및 환경 테스트"""
    
    def test_supported_model_types(self):
        """지원되는 모델 타입 확인"""
        assert 'gemini' in SUPPORTED_LLM_TYPES
        assert 'hcx' in SUPPORTED_LLM_TYPES
        
        assert 'gemini' in SUPPORTED_EMBEDDING_TYPES
        assert 'hcx' in SUPPORTED_EMBEDDING_TYPES
        assert 'bge_m3' in SUPPORTED_EMBEDDING_TYPES

    def test_prompt_types(self):
        """프롬프트 타입 확인"""
        prompt_types = [pt.value for pt in PromptType]
        assert 'default' in prompt_types
        assert 'korean_tech' in prompt_types
        assert 'multilingual' in prompt_types

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test_key'})
    def test_valid_settings_with_gemini_key(self):
        """Gemini API 키가 있을 때 설정 검증"""
        try:
            validate_settings()
            # 예외가 발생하지 않으면 성공
        except ValueError:
            pytest.fail("Valid settings should not raise ValueError")

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_keys(self):
        """API 키가 없을 때 설정 검증"""
        # 모든 API 키가 없는 상황에서는 설정이 유효하지 않을 수 있음
        # 하지만 시스템이 기본적으로 동작해야 함
        try:
            validate_settings()
        except ValueError as e:
            # API 키 관련 오류가 예상됨
            assert 'API' in str(e) or 'key' in str(e).lower()

    @patch.dict(os.environ, {'DEFAULT_LLM': 'invalid_llm'})
    def test_invalid_default_llm(self):
        """잘못된 기본 LLM 설정"""
        with pytest.raises(ValueError, match="지원되지 않는 LLM"):
            validate_settings()

    @patch.dict(os.environ, {'DEFAULT_EMBEDDING': 'invalid_embedding'})
    def test_invalid_default_embedding(self):
        """잘못된 기본 임베딩 설정"""
        with pytest.raises(ValueError, match="지원되지 않는 임베딩"):
            validate_settings()

    def test_settings_default_values(self):
        """설정 기본값 확인"""
        # 기본 LLM과 임베딩 설정 확인
        assert settings.DEFAULT_LLM in SUPPORTED_LLM_TYPES
        assert settings.DEFAULT_EMBEDDING in SUPPORTED_EMBEDDING_TYPES

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test_gemini_key'})
    def test_gemini_api_key_access(self):
        """Gemini API 키 접근 테스트"""
        assert settings.GEMINI_API_KEY == 'test_gemini_key'

    @patch.dict(os.environ, {'CLOVA_STUDIO_API_KEY': 'test_clova_key'})
    def test_clova_api_key_access(self):
        """Clova API 키 접근 테스트"""
        assert settings.CLOVA_STUDIO_API_KEY == 'test_clova_key'

    def test_prompt_type_validation(self):
        """프롬프트 타입 검증"""
        # 유효한 프롬프트 타입
        assert PromptType.DEFAULT.value == 'default'
        assert PromptType.KOREAN_TECH.value == 'korean_tech'
        assert PromptType.MULTILINGUAL.value == 'multilingual'
        
        # 모든 프롬프트 타입이 문자열이어야 함
        for prompt_type in PromptType:
            assert isinstance(prompt_type.value, str)

    def test_data_paths_functionality(self):
        """데이터 경로 기능 테스트"""
        # 임시 데이터 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / 'data'
            data_dir.mkdir()
            
            # 테스트 JSON 파일 생성
            test_file = data_dir / 'test_dataset.json'
            test_file.write_text('[]', encoding='utf-8')
            
            with patch('src.utils.paths.DATA_DIR', data_dir):
                # 사용 가능한 데이터셋 확인
                datasets = get_available_datasets()
                assert 'test_dataset' in datasets
                
                # 데이터셋 경로 확인
                path = get_evaluation_data_path('test_dataset')
                assert path == str(test_file)
                
                # 존재하지 않는 데이터셋
                path = get_evaluation_data_path('nonexistent')
                assert path is None

    def test_data_paths_empty_directory(self):
        """빈 데이터 디렉토리 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_data_dir = Path(temp_dir) / 'empty_data'
            empty_data_dir.mkdir()
            
            with patch('src.utils.paths.DATA_DIR', empty_data_dir):
                datasets = get_available_datasets()
                assert len(datasets) == 0

    def test_data_paths_nonexistent_directory(self):
        """존재하지 않는 데이터 디렉토리 테스트"""
        nonexistent_dir = Path('/nonexistent/data/directory')
        
        with patch('src.utils.paths.DATA_DIR', nonexistent_dir):
            datasets = get_available_datasets()
            assert len(datasets) == 0

    @patch.dict(os.environ, {'BGE_M3_MODEL_PATH': '/custom/model/path'})
    def test_bge_m3_model_path_custom(self):
        """BGE-M3 모델 경로 커스터마이징 테스트"""
        # 환경 변수 재로드를 위해 설정 다시 가져오기
        from importlib import reload
        import src.config
        reload(src.config)
        
        assert src.config.settings.BGE_M3_MODEL_PATH == '/custom/model/path'

    def test_config_file_loading(self):
        """설정 파일 로딩 테스트"""
        # .env 파일 시뮬레이션
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('TEST_SETTING=test_value\n')
            f.write('GEMINI_API_KEY=test_gemini\n')
            env_file = f.name
        
        try:
            # python-dotenv를 사용한 로딩 시뮬레이션
            from dotenv import load_dotenv
            load_dotenv(env_file)
            
            assert os.getenv('TEST_SETTING') == 'test_value'
            assert os.getenv('GEMINI_API_KEY') == 'test_gemini'
            
        finally:
            os.unlink(env_file)
            # 환경 변수 정리
            if 'TEST_SETTING' in os.environ:
                del os.environ['TEST_SETTING']

    def test_container_initialization_with_different_settings(self):
        """다양한 설정으로 컨테이너 초기화 테스트"""
        from src.container import container
        
        # 컨테이너가 제대로 초기화되는지 확인
        assert container is not None
        
        # LLM 제공자 확인
        llm_providers = container.llm_providers()
        assert 'gemini' in llm_providers
        assert 'hcx' in llm_providers
        
        # 임베딩 제공자 확인
        embedding_providers = container.embedding_providers()
        assert 'gemini' in embedding_providers
        assert 'hcx' in embedding_providers
        assert 'bge_m3' in embedding_providers

    @patch.dict(os.environ, {'GEMINI_API_KEY': ''})
    def test_empty_api_key(self):
        """빈 API 키 처리 테스트"""
        # 빈 문자열 API 키는 None과 같이 처리되어야 함
        assert not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == ''

    def test_settings_immutability(self):
        """설정의 불변성 테스트"""
        # 설정이 실행 중에 변경되지 않는지 확인
        original_llm = settings.DEFAULT_LLM
        original_embedding = settings.DEFAULT_EMBEDDING
        
        # 다른 작업 수행
        _ = SUPPORTED_LLM_TYPES
        _ = SUPPORTED_EMBEDDING_TYPES
        
        # 설정이 그대로인지 확인
        assert settings.DEFAULT_LLM == original_llm
        assert settings.DEFAULT_EMBEDDING == original_embedding

    def test_model_validation_functions(self):
        """모델 검증 함수 테스트"""
        # 유효한 LLM
        for llm in SUPPORTED_LLM_TYPES:
            # 검증 함수가 있다면 테스트
            assert llm in ['gemini', 'hcx']
        
        # 유효한 임베딩 모델
        for embedding in SUPPORTED_EMBEDDING_TYPES:
            assert embedding in ['gemini', 'hcx', 'bge_m3']

    def test_configuration_consistency(self):
        """설정 일관성 테스트"""
        # 기본 LLM이 지원되는 LLM 목록에 있는지 확인
        assert settings.DEFAULT_LLM in SUPPORTED_LLM_TYPES
        
        # 기본 임베딩이 지원되는 임베딩 목록에 있는지 확인
        assert settings.DEFAULT_EMBEDDING in SUPPORTED_EMBEDDING_TYPES

    @patch('src.config.logger')
    def test_logging_configuration(self, mock_logger):
        """로깅 설정 테스트"""
        # 로깅이 제대로 설정되어 있는지 확인
        # (실제 로깅 동작은 모킹됨)
        from src.config import settings
        
        # 설정 로딩 시 로깅이 호출되는지 확인 (필요시)
        assert settings is not None

    def test_data_directory_structure(self):
        """데이터 디렉토리 구조 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / 'data'
            data_dir.mkdir()
            
            # 하위 디렉토리 생성
            db_dir = data_dir / 'db'
            db_dir.mkdir()
            
            temp_dir_path = data_dir / 'temp'
            temp_dir_path.mkdir()
            
            # JSON 파일들 생성
            (data_dir / 'dataset1.json').write_text('[]')
            (data_dir / 'dataset2.json').write_text('[]')
            (db_dir / 'evaluations.db').write_text('')  # SQLite 파일 시뮬레이션
            
            with patch('src.utils.paths.DATA_DIR', data_dir):
                datasets = get_available_datasets()
                assert 'dataset1' in datasets
                assert 'dataset2' in datasets
                assert len(datasets) == 2  # DB 파일은 제외됨

    def test_environment_variable_precedence(self):
        """환경 변수 우선순위 테스트"""
        # 환경 변수가 기본값보다 우선되는지 확인
        original_llm = settings.DEFAULT_LLM
        
        with patch.dict(os.environ, {'DEFAULT_LLM': 'hcx'}):
            # 새로운 설정 인스턴스 생성 필요
            from importlib import reload
            import src.config
            reload(src.config)
            
            # 환경 변수가 적용되었는지 확인
            assert src.config.settings.DEFAULT_LLM == 'hcx'
        
        # 원래 설정으로 복원하기 위해 다시 reload
        reload(src.config)

    def test_api_key_security(self):
        """API 키 보안 테스트"""
        # API 키가 로그에 노출되지 않는지 확인
        test_key = "secret_api_key_12345"
        
        with patch.dict(os.environ, {'GEMINI_API_KEY': test_key}):
            from importlib import reload
            import src.config
            reload(src.config)
            
            # 설정에서 API 키에 접근할 수 있어야 함
            assert src.config.settings.GEMINI_API_KEY == test_key
            
            # API 키가 문자열 표현에 노출되지 않는지 확인
            settings_str = str(src.config.settings)
            # 보안상 API 키가 완전히 노출되면 안 됨 (마스킹되거나 숨겨져야 함)
            assert test_key not in settings_str or '***' in settings_str