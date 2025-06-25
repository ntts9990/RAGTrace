"""
Evaluation Model

평가 관련 데이터 모델입니다.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.domain.prompts import PromptType


@dataclass
class EvaluationConfig:
    """평가 설정 모델"""
    llm_type: str
    embedding_type: str
    prompt_type: PromptType
    dataset_name: str


@dataclass
class EvaluationResult:
    """평가 결과 모델"""
    ragas_score: float
    faithfulness: float
    answer_relevancy: float
    context_recall: float
    context_precision: float
    answer_correctness: float = 0.0
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None


class EvaluationModel:
    """평가 관련 비즈니스 로직"""
    
    @staticmethod
    def create_config(llm_type: str, embedding_type: str, prompt_type: PromptType, dataset_name: str) -> EvaluationConfig:
        """평가 설정 생성"""
        return EvaluationConfig(
            llm_type=llm_type,
            embedding_type=embedding_type,
            prompt_type=prompt_type,
            dataset_name=dataset_name
        )
    
    @staticmethod
    def parse_result_dict(result_dict: Dict[str, Any]) -> EvaluationResult:
        """결과 딕셔너리를 EvaluationResult로 변환"""
        return EvaluationResult(
            ragas_score=result_dict.get("ragas_score", 0.0),
            faithfulness=result_dict.get("faithfulness", 0.0),
            answer_relevancy=result_dict.get("answer_relevancy", 0.0),
            context_recall=result_dict.get("context_recall", 0.0),
            context_precision=result_dict.get("context_precision", 0.0),
            answer_correctness=result_dict.get("answer_correctness", 0.0),
            timestamp=datetime.fromisoformat(result_dict.get("timestamp", datetime.now().isoformat())),
            metadata=result_dict.get("metadata"),
            raw_data=result_dict
        )
    
    @staticmethod
    def get_metric_color(value: float) -> str:
        """메트릭 값에 따른 색상 반환"""
        if value >= 0.8:
            return "green"
        elif value >= 0.6:
            return "orange"
        else:
            return "red"
    
    @staticmethod
    def is_dummy_result(result: EvaluationResult) -> bool:
        """더미 결과인지 확인"""
        return all(getattr(result, metric) == 0 for metric in 
                  ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision', 'answer_correctness'])
    
    @staticmethod
    def get_metrics_list() -> List[str]:
        """메트릭 목록 반환"""
        return ["faithfulness", "answer_relevancy", "context_recall", "context_precision", "answer_correctness"]
    
    @staticmethod
    def get_metrics_labels() -> List[str]:
        """메트릭 라벨 목록 반환"""
        return ["Faithfulness", "Answer Relevancy", "Context Recall", "Context Precision", "Answer Correctness"]