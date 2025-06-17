"""평가 어댑터 팩토리"""

from typing import Optional

from src.application.ports.evaluation import EvaluationRunnerPort
from src.domain.prompts import PromptType
from src.infrastructure.evaluation import RagasEvalAdapter


class RagasEvalAdapterFactory:
    """RagasEvalAdapter 인스턴스를 생성하는 팩토리"""
    
    def __init__(
        self,
        embedding_model_name: str,
        api_key: str,
        embedding_requests_per_minute: int,
    ):
        self.embedding_model_name = embedding_model_name
        self.api_key = api_key
        self.embedding_requests_per_minute = embedding_requests_per_minute
    
    def create_evaluator(
        self, 
        prompt_type: Optional[PromptType] = None
    ) -> EvaluationRunnerPort:
        """
        주어진 프롬프트 타입으로 RagasEvalAdapter를 생성합니다.
        
        Args:
            prompt_type: 프롬프트 타입 (선택사항)
            
        Returns:
            EvaluationRunnerPort: Ragas 평가 어댑터
        """
        return RagasEvalAdapter(
            embedding_model_name=self.embedding_model_name,
            api_key=self.api_key,
            embedding_requests_per_minute=self.embedding_requests_per_minute,
            prompt_type=prompt_type,
        )