from abc import ABC, abstractmethod
from typing import Any


class LlmPort(ABC):
    """LLM 연동을 위한 추상 인터페이스 (Port)"""

    @abstractmethod
    def get_llm(self) -> Any:
        """
        Ragas 평가에 사용할 LLM 객체를 반환합니다.
        반환 타입은 사용하는 LLM 라이브러리(예: LangChain)에 따라 달라질 수 있으므로 Any로 지정합니다.
        """
        pass
