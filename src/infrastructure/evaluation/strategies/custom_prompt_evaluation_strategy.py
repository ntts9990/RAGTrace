"""
Custom Prompt Evaluation Strategy

커스텀 프롬프트를 사용한 평가 전략입니다.
"""

from typing import Any, List
from datasets import Dataset
from ragas import evaluate
from ragas.run_config import RunConfig

from src.domain.prompts import PromptType
from src.infrastructure.evaluation.custom_prompts import CustomPromptFactory
from .base_strategy import EvaluationStrategy


class CustomPromptEvaluationStrategy(EvaluationStrategy):
    """커스텀 프롬프트를 사용한 평가 전략"""
    
    def __init__(self, llm, embeddings, prompt_type: PromptType):
        super().__init__(llm, embeddings)
        self.prompt_type = prompt_type
        # HCX 사용 시 순차 처리로 API 한도 방지
        max_workers = 1
        timeout = 600  # HCX 사용 시 타임아웃 증가
        
        # LLM이 HCX가 아닌 경우 더 많은 워커 사용 가능
        if hasattr(llm, 'model') and 'HCX' not in str(llm.model):
            max_workers = 4
            timeout = 300
        
        self.run_config = RunConfig(
            timeout=timeout,
            max_retries=5,  # 재시도 횟수 증가
            max_workers=max_workers,
            max_wait=120,   # 대기 시간 증가
            log_tenacity=True
        )
        
        # 커스텀 메트릭 생성
        self.custom_metrics = CustomPromptFactory.create_custom_metrics(self.prompt_type)
    
    def get_metrics(self) -> List[Any]:
        """커스텀 메트릭 반환 (Context Precision과 Answer Correctness는 기본 메트릭 사용)"""
        from ragas.metrics import context_precision, answer_correctness
        
        return [
            self.custom_metrics['faithfulness'],
            self.custom_metrics['answer_relevancy'],
            self.custom_metrics['context_recall'],
            context_precision,  # 기본 메트릭 사용으로 안정성 확보
            answer_correctness,  # 기본 메트릭 사용 (ground_truth 비교 필요)
        ]
    
    def run_evaluation(self, dataset: Dataset) -> Any:
        """커스텀 프롬프트 평가 실행"""
        prompt_description = CustomPromptFactory.get_prompt_type_description(self.prompt_type)
        print(f"🚀 커스텀 프롬프트 평가 실행 중: {prompt_description}")
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
        prompt_description = CustomPromptFactory.get_prompt_type_description(self.prompt_type)
        return f"커스텀 프롬프트 평가 ({prompt_description})"