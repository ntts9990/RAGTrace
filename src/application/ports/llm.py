from abc import ABC, abstractmethod
from typing import Any, List


class AnswerGeneratorPort(ABC):
    """답변 생성을 위한 인터페이스"""

    @abstractmethod
    def generate_answer(self, question: str, contexts: List[str]) -> str:
        """
        질문과 컨텍스트를 바탕으로 답변을 생성합니다.
        
        Args:
            question: 질문 텍스트
            contexts: 검색된 컨텍스트 목록
            
        Returns:
            str: 생성된 답변
        """
        pass


class RagasLlmProviderPort(ABC):
    """Ragas 평가를 위한 LLM 제공 인터페이스"""

    @abstractmethod
    def get_llm(self) -> Any:
        """
        Ragas 평가에 사용할 LLM 객체를 반환합니다.
        
        Returns:
            Any: Ragas 평가에 사용할 LLM 객체
        """
        pass


# 하위 호환성을 위한 통합 인터페이스
class LlmPort(AnswerGeneratorPort, RagasLlmProviderPort):
    """
    LLM 연동을 위한 통합 인터페이스
    
    AnswerGeneratorPort와 RagasLlmProviderPort를 모두 구현합니다.
    기존 코드와의 호환성을 유지하면서도 ISP 원칙을 준수합니다.
    """
    pass
