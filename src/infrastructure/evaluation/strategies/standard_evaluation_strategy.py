"""
Standard Evaluation Strategy

기본 RAGAS 메트릭을 사용한 표준 평가 전략입니다.
"""

from typing import Any, List
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from ragas.run_config import RunConfig

from .base_strategy import EvaluationStrategy


class StandardEvaluationStrategy(EvaluationStrategy):
    """기본 RAGAS 메트릭을 사용한 표준 평가 전략"""
    
    def __init__(self, llm, embeddings):
        super().__init__(llm, embeddings)
        self.run_config = RunConfig(
            timeout=300,
            max_retries=3,
            max_workers=4,
            max_wait=60,
            log_tenacity=True
        )
    
    def get_metrics(self) -> List[Any]:
        """기본 RAGAS 메트릭 반환"""
        return [
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
        ]
    
    def run_evaluation(self, dataset: Dataset) -> Any:
        """기본 RAGAS 평가 실행"""
        print("🚀 표준 RAGAS 평가 실행 중...")
        print(f"📊 데이터셋 크기: {len(dataset)}개 QA 쌍")
        print(f"🤖 LLM 모델: {self.llm.model}")
        
        # 임베딩 모델 정보 출력
        embedding_info = f"🌐 임베딩 모델: {type(self.embeddings).__name__}"
        if hasattr(self.embeddings, 'model_name'):
            embedding_info += f" ({self.embeddings.model_name})"
        elif hasattr(self.embeddings, 'device'):
            embedding_info += f" (디바이스: {self.embeddings.device})"
        print(embedding_info)
        
        return evaluate(
            dataset=dataset,
            metrics=self.get_metrics(),
            llm=self.llm,
            embeddings=self.embeddings,
            run_config=self.run_config,
            raise_exceptions=False,
        )
    
    def get_strategy_name(self) -> str:
        """전략 이름 반환"""
        return "표준 RAGAS 평가 (영어)"