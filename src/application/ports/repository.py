from abc import ABC, abstractmethod

from src.domain import EvaluationData


class EvaluationRepositoryPort(ABC):
    """평가 데이터셋을 로드하기 위한 추상 인터페이스 (Port)"""

    @abstractmethod
    def load_data(self) -> list[EvaluationData]:
        """
        평가에 사용할 데이터셋을 로드하여 EvaluationData 객체의 리스트로 반환합니다.
        """
        pass
