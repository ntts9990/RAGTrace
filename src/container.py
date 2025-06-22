"""애플리케이션의 의존성 주입(DI) 컨테이너

DEPRECATED: 이 모듈은 backward compatibility를 위해 유지됩니다.
새로운 코드에서는 src.container 패키지를 사용하세요.

이 모듈은 애플리케이션의 모든 서비스(유스케이스, 어댑터 등)의
인스턴스를 생성하고 필요한 의존성을 주입하는 역할을 중앙에서 관리합니다.
"""

# 새로운 컨테이너 구조를 사용 (backward compatibility)
from src.container.main_container import container, get_evaluation_use_case_with_llm


# Legacy container class for backward compatibility
class Container:
    """Legacy Container - backward compatibility를 위한 클래스"""
    
    def __init__(self):
        self._main_container = container
    
    def llm_providers(self):
        return self._main_container.llm_providers()
    
    def embedding_providers(self):
        return self._main_container.embedding_providers()
    
    def repository_factory(self):
        return self._main_container.repository_factory()
    
    def data_validator(self):
        return self._main_container.data_validator()
    
    def result_conversion_service(self):
        return self._main_container.result_conversion_service()
    
    def ragas_eval_adapter(self, **kwargs):
        return self._main_container.ragas_eval_adapter(**kwargs)
    
    def run_evaluation_use_case(self, **kwargs):
        return self._main_container.run_evaluation_use_case(**kwargs)


# Legacy container instance (backward compatibility)
# Note: 이제 실제로는 새로운 MainContainer를 사용합니다
# container = Container()

# 기존 함수도 그대로 export (backward compatibility)
__all__ = ['container', 'get_evaluation_use_case_with_llm']
