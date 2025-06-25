"""
Ragas Adapter using Strategy Pattern

Strategy 패턴을 적용한 리팩토링된 Ragas 어댑터입니다.
"""

from typing import Any, Optional
import datetime
import uuid

import pandas as pd
from datasets import Dataset
from langchain_core.embeddings import Embeddings

from src.domain.prompts import PromptType
from src.infrastructure.evaluation.parsing_strategies import ResultParser
from src.infrastructure.evaluation.strategies import EvaluationContext


class RagasEvalAdapter:
    """Strategy 패턴을 사용한 리팩토링된 Ragas 평가 어댑터"""

    def __init__(
        self,
        llm: Any,  # LLM 어댑터 (GeminiAdapter 또는 HcxAdapter)
        embeddings: Embeddings,
        prompt_type: Optional[PromptType] = None,
    ):
        # LLM 어댑터에서 실제 LangChain 호환 LLM 객체 가져오기
        if hasattr(llm, 'get_llm'):
            self.llm = llm.get_llm()
        else:
            self.llm = llm
        
        self.embeddings = embeddings
        self.prompt_type = prompt_type or PromptType.DEFAULT
        
        # Strategy Context 초기화
        self.evaluation_context = EvaluationContext(
            llm=self.llm,
            embeddings=self.embeddings,
            prompt_type=self.prompt_type
        )
        
        # 결과 파서 초기화
        self.result_parser = ResultParser()


    def evaluate(self, dataset: Dataset) -> dict[str, float]:
        """
        주어진 데이터셋과 LLM, Embedding을 사용하여 Ragas 평가를 수행합니다.
        (오류 처리는 상위 계층으로 위임)
        """
        strategy = self.evaluation_context.primary_strategy
        raw_result = strategy.run_evaluation(dataset)
        return self._parse_result(raw_result, dataset)

    def _parse_result(self, result, dataset: Dataset) -> dict:
        """결과 파싱 - 오류 처리는 상위 계층으로 위임"""
        metrics = self.evaluation_context.get_metrics()
        return self.result_parser.parse_result(result, dataset, metrics)

    def _create_error_result(self) -> dict:
        """오류 발생 시 기본 결과 생성"""
        metrics = self.evaluation_context.get_metrics()
        error_result = {metric.name: 0.0 for metric in metrics}
        error_result["ragas_score"] = 0.0
        error_result["individual_scores"] = []
        return error_result
