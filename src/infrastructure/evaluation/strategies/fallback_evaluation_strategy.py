"""
Fallback Evaluation Strategy

평가 실패 시 사용되는 폴백 전략입니다.
"""

from typing import Any, List
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from ragas.run_config import RunConfig

from .base_strategy import EvaluationStrategy


class FallbackEvaluationStrategy(EvaluationStrategy):
    """평가 실패 시 사용되는 폴백 전략"""
    
    def __init__(self, llm, embeddings):
        super().__init__(llm, embeddings)
        # 더 보수적인 설정
        self.run_config = RunConfig(
            timeout=180,        # 3분으로 단축
            max_retries=2,      # 재시도 2회
            max_workers=2,      # 워커 2개로 제한
            max_wait=30,
            log_tenacity=True
        )
    
    def get_metrics(self) -> List[Any]:
        """기본 메트릭 반환 (보수적)"""
        return [
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
        ]
    
    def run_evaluation(self, dataset: Dataset) -> Any:
        """폴백 평가 실행"""
        print("🔄 폴백 평가 전략 실행 중...")
        print("⚠️  더 보수적인 설정으로 재시도합니다")
        print(f"📊 데이터셋 크기: {len(dataset)}개 QA 쌍")
        print(f"🤖 LLM 모델: {self.llm.model}")
        print(f"⚙️  폴백 설정: 타임아웃={self.run_config.timeout}초, 워커={self.run_config.max_workers}개")
        
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
        return "폴백 평가 (보수적 설정)"