"""
Base Evaluation Strategy

평가 전략의 기본 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Any, List
from datasets import Dataset
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseLanguageModel


class EvaluationStrategy(ABC):
    """평가 전략 기본 인터페이스"""
    
    def __init__(self, llm: BaseLanguageModel, embeddings: Embeddings):
        self.llm = llm
        self.embeddings = embeddings
    
    @abstractmethod
    def get_metrics(self) -> List[Any]:
        """사용할 메트릭 목록 반환"""
        pass
    
    @abstractmethod
    def run_evaluation(self, dataset: Dataset) -> Any:
        """평가 실행"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """전략 이름 반환"""
        pass
    
    def print_strategy_info(self):
        """전략 정보 출력"""
        print(f"🔧 평가 전략: {self.get_strategy_name()}")
        print(f"📊 메트릭 수: {len(self.get_metrics())}개")