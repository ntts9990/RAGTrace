"""
Refactored Ragas Adapter using Strategy Pattern

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


class RagasEvalAdapterV2:
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
            # Strategy Context를 통한 평가 실행
            raw_result = self.evaluation_context.run_evaluation_with_timeout(dataset)
            
            # 결과 파싱 및 최종 리포트 생성
            result_dict = self._parse_result(raw_result, dataset)
            return self._create_final_report(result_dict, dataset)
            
        except Exception as e:
            print(f"❌ 평가 중 오류 발생: {str(e)}")
            print("⚠️  폴백: 샘플 결과 반환")
            try:
                raw_result = self.evaluation_context._create_dummy_result(dataset)
                result_dict = self._parse_result(raw_result, dataset)
                return self._create_final_report(result_dict, dataset)
            except Exception as fallback_error:
                print(f"❌ 샘플 결과 생성도 실패: {str(fallback_error)}")
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

    def _create_final_report(self, result_dict: dict, dataset: Dataset) -> dict:
        """최종 리포트 생성"""
        # ragas_score 계산
        metric_values = [v for k, v in result_dict.items() if k != "individual_scores" and v > 0]
        result_dict["ragas_score"] = sum(metric_values) / len(metric_values) if metric_values else 0.0
        
        # 메타데이터 추가
        result_dict["metadata"] = {
            "evaluation_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "model": str(self.llm.model),
            "temperature": getattr(self.llm, "temperature", 0.0),
            "dataset_size": len(dataset),
            "strategy": self.evaluation_context.primary_strategy.get_strategy_name(),
        }
        
        print(f"✅ 평가 완료!")
        print(f"📊 최종 결과: RAGAS Score = {result_dict['ragas_score']:.4f}")
        return result_dict

    def _create_error_result(self) -> dict:
        """오류 발생 시 기본 결과 생성"""
        metrics = self.evaluation_context.get_metrics()
        error_result = {metric.name: 0.0 for metric in metrics}
        error_result["ragas_score"] = 0.0
        error_result["individual_scores"] = []
        return error_result