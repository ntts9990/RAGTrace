"""
Base Provider Factory

모든 제공자 팩토리의 기본 클래스입니다.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseProviderFactory(ABC):
    """제공자 팩토리의 기본 클래스"""
    
    def __init__(self, configuration_container):
        self._config_container = configuration_container
        self._providers = {}
    
    @abstractmethod
    def create_provider(self, provider_type: str) -> Any:
        """제공자 생성 (추상 메서드)"""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> list:
        """지원되는 타입 목록 반환 (추상 메서드)"""
        pass
    
    @abstractmethod
    def is_supported(self, provider_type: str) -> bool:
        """타입 지원 여부 확인 (추상 메서드)"""
        pass