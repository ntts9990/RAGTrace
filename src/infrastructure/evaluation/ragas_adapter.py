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
        """
        try:
            # 단순화된 평가 실행: primary_strategy를 직접 호출
            strategy = self.evaluation_context.primary_strategy
            strategy.print_strategy_info()
            
            raw_result = strategy.run_evaluation(dataset)
            
            # 결과 파싱만 수행하고 그대로 반환
            return self._parse_result(raw_result, dataset)
            
        except Exception as e:
            print(f"❌ 평가 중 오류 발생: {str(e)}")
            # 오류 발생 시 빈 결과 반환
            return self._create_error_result()


    def _parse_result(self, result, dataset: Dataset) -> dict:
        """결과 파싱 - 전략 패턴을 통한 안정적인 파싱"""
        try:
            metrics = self.evaluation_context.get_metrics()
            return self.result_parser.parse_result(result, dataset, metrics)
        except Exception as e:
            print(f"❌ 모든 파싱 전략 실패: {e}")
            # 최후의 수단: 빈 결과 반환
            metrics = self.evaluation_context.get_metrics()
            result_dict = {metric.name: 0.0 for metric in metrics}
            result_dict["individual_scores"] = [
                {metric.name: 0.0 for metric in metrics} 
                for _ in range(len(dataset))
            ]
            return result_dict

    def _create_error_result(self) -> dict:
        """오류 발생 시 기본 결과 생성"""
        metrics = self.evaluation_context.get_metrics()
        error_result = {metric.name: 0.0 for metric in metrics}
        error_result["ragas_score"] = 0.0
        error_result["individual_scores"] = []
        return error_result
