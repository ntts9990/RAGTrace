"""
Evaluation Context

평가 전략과 관련 객체를 담는 데이터 컨테이너입니다.
"""

from typing import Optional

from src.domain.prompts import PromptType
from .base_strategy import EvaluationStrategy
from .standard_evaluation_strategy import StandardEvaluationStrategy
from .custom_prompt_evaluation_strategy import CustomPromptEvaluationStrategy
from .fallback_evaluation_strategy import FallbackEvaluationStrategy
from .hcx_evaluation_strategy import HcxEvaluationStrategy


class EvaluationContext:
    """평가 전략과 관련 객체를 담는 데이터 컨테이너"""
    
    def __init__(self, llm, embeddings, prompt_type: Optional[PromptType] = None):
        self.llm = llm
        self.embeddings = embeddings
        self.prompt_type = prompt_type or PromptType.DEFAULT
        
        # 전략 선택
        self.primary_strategy: EvaluationStrategy = self._create_primary_strategy()
        self.fallback_strategy: EvaluationStrategy = FallbackEvaluationStrategy(llm, embeddings)
    
    def _create_primary_strategy(self) -> EvaluationStrategy:
        """주요 전략 생성"""
        # HCX 모델인 경우 전용 전략 사용
        if hasattr(self.llm, 'model') and 'HCX' in str(self.llm.model):
            print("🔧 HCX 모델 감지 - HCX 전용 평가 전략 사용")
            return HcxEvaluationStrategy(self.llm, self.embeddings)
        
        # 기본 전략 선택
        if self.prompt_type == PromptType.DEFAULT:
            return StandardEvaluationStrategy(self.llm, self.embeddings)
        else:
            return CustomPromptEvaluationStrategy(self.llm, self.embeddings, self.prompt_type)
    
    def get_metrics(self):
        """현재 전략의 메트릭 반환"""
        return self.primary_strategy.get_metrics()