from abc import ABC, abstractmethod
from typing import Any, List


class LlmPort(ABC):
    """LLM 연동을 위한 추상 인터페이스 (Port)"""

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

    @abstractmethod
    def get_llm(self) -> Any:
        """
        Ragas 평가에 사용할 LLM 객체를 반환합니다.
        
        Note: 이 메서드는 하위 호환성을 위해 유지되지만, 
        향후 generate_answer 메서드 사용을 권장합니다.
        """
        pass
