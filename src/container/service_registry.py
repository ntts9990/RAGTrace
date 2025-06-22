"""
Service Registry

서비스 등록 및 조회를 담당하는 레지스트리입니다.
"""

from typing import Dict, Type, Any

from src.application.services.data_validator import DataContentValidator
from src.application.services.result_conversion_service import ResultConversionService
from src.infrastructure.repository import FileRepositoryFactory


class ServiceRegistry:
    """서비스 등록 및 관리를 위한 레지스트리"""
    
    def __init__(self):
        self._instances = {}  # Singleton 인스턴스 캐시
        
    def get_repository_factory(self) -> FileRepositoryFactory:
        """파일 리포지토리 팩토리 반환"""
        if 'repository_factory' not in self._instances:
            self._instances['repository_factory'] = FileRepositoryFactory()
        return self._instances['repository_factory']
    
    def get_data_validator(self) -> DataContentValidator:
        """데이터 검증기 반환"""
        if 'data_validator' not in self._instances:
            self._instances['data_validator'] = DataContentValidator()
        return self._instances['data_validator']
    
    def get_result_conversion_service(self) -> ResultConversionService:
        """결과 변환 서비스 반환"""
        if 'result_conversion_service' not in self._instances:
            self._instances['result_conversion_service'] = ResultConversionService()
        return self._instances['result_conversion_service']