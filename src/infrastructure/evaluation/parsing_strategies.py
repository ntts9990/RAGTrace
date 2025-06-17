"""
RAGAS 평가 결과 파싱을 위한 전략 패턴 구현

다양한 RAGAS 버전과 결과 형태에 대응하기 위한 파싱 전략들을 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd
from datasets import Dataset


class ResultParsingStrategy(ABC):
    """결과 파싱 전략 추상 인터페이스"""
    
    @abstractmethod
    def can_parse(self, result: Any) -> bool:
        """이 전략이 주어진 결과를 파싱할 수 있는지 확인"""
        pass
    
    @abstractmethod
    def parse(self, result: Any, dataset: Dataset, metrics: List[Any]) -> Dict:
        """결과를 파싱하여 딕셔너리로 반환"""
        pass


class DataFrameParsingStrategy(ResultParsingStrategy):
    """DataFrame 변환을 통한 안정적인 파싱 전략"""
    
    def can_parse(self, result: Any) -> bool:
        """to_pandas 메서드가 있는지 확인"""
        return hasattr(result, 'to_pandas') and callable(result.to_pandas)
    
    def parse(self, result: Any, dataset: Dataset, metrics: List[Any]) -> Dict:
        """DataFrame을 통한 파싱"""
        try:
            df = result.to_pandas()
            result_dict = {}
            individual_scores = []
            
            # DataFrame에서 메트릭 값 추출
            for metric in metrics:
                metric_name = metric.name
                if metric_name in df.columns:
                    metric_values = df[metric_name].fillna(0.0)  # NaN을 0.0으로 대체
                    result_dict[metric_name] = float(metric_values.mean())
                    print(f"✅ {metric_name} 평균: {result_dict[metric_name]:.4f}")
                else:
                    result_dict[metric_name] = 0.0
                    print(f"⚠️  {metric_name} 결과를 찾을 수 없습니다.")
            
            # 개별 점수 추출
            for idx in range(len(dataset)):
                qa_scores = {}
                for metric in metrics:
                    metric_name = metric.name
                    if metric_name in df.columns and idx < len(df):
                        score_value = df.iloc[idx][metric_name]
                        qa_scores[metric_name] = float(score_value) if pd.notna(score_value) else 0.0
                    else:
                        qa_scores[metric_name] = 0.0
                individual_scores.append(qa_scores)
            
            result_dict["individual_scores"] = individual_scores
            return result_dict
            
        except Exception as e:
            raise ValueError(f"DataFrame 파싱 실패: {e}")


class ScoresDictParsingStrategy(ResultParsingStrategy):
    """_scores_dict 속성을 통한 레거시 파싱 전략"""
    
    def can_parse(self, result: Any) -> bool:
        """_scores_dict 속성이 있고 비어있지 않은지 확인"""
        return (hasattr(result, "_scores_dict") and 
                result._scores_dict and 
                isinstance(result._scores_dict, dict))
    
    def parse(self, result: Any, dataset: Dataset, metrics: List[Any]) -> Dict:
        """_scores_dict를 통한 파싱"""
        result_dict = {}
        individual_scores = []
        scores_dict = result._scores_dict
        
        # 개별 QA 점수 추출
        num_samples = len(dataset)
        for i in range(num_samples):
            qa_scores = {}
            for metric in metrics:
                metric_name = metric.name
                if metric_name in scores_dict:
                    scores = scores_dict[metric_name]
                    if isinstance(scores, list) and i < len(scores):
                        score_value = scores[i]
                        qa_scores[metric_name] = float(score_value) if score_value == score_value else 0.0
                    else:
                        qa_scores[metric_name] = float(scores) if scores == scores else 0.0
                else:
                    qa_scores[metric_name] = 0.0
            individual_scores.append(qa_scores)

        # 각 메트릭별로 평균값 계산
        for metric in metrics:
            metric_name = metric.name
            if metric_name in scores_dict:
                scores = scores_dict[metric_name]
                if isinstance(scores, list) and scores:
                    valid_scores = [float(s) for s in scores if s == s]  # NaN 제외
                    result_dict[metric_name] = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
                else:
                    result_dict[metric_name] = float(scores) if scores == scores else 0.0
            else:
                result_dict[metric_name] = 0.0

        result_dict["individual_scores"] = individual_scores
        return result_dict


class AttributeParsingStrategy(ResultParsingStrategy):
    """객체 속성을 통한 단순 파싱 전략"""
    
    def can_parse(self, result: Any) -> bool:
        """결과 객체가 존재하는지만 확인 (최후의 수단)"""
        return result is not None
    
    def parse(self, result: Any, dataset: Dataset, metrics: List[Any]) -> Dict:
        """객체 속성을 통한 단순 파싱"""
        result_dict = {}
        
        # 메트릭별로 속성 확인
        for metric in metrics:
            metric_name = metric.name
            if hasattr(result, metric_name):
                value = getattr(result, metric_name)
                result_dict[metric_name] = float(value) if value is not None else 0.0
            else:
                result_dict[metric_name] = 0.0
        
        # 개별 점수는 전체 평균으로 대체
        individual_scores = []
        for i in range(len(dataset)):
            qa_scores = {metric.name: result_dict.get(metric.name, 0.0) for metric in metrics}
            individual_scores.append(qa_scores)

        result_dict["individual_scores"] = individual_scores
        return result_dict


class ResultParser:
    """결과 파싱을 담당하는 컨텍스트 클래스"""
    
    def __init__(self):
        self.strategies = [
            DataFrameParsingStrategy(),
            ScoresDictParsingStrategy(),
            AttributeParsingStrategy(),  # 최후의 수단
        ]
    
    def parse_result(self, result: Any, dataset: Dataset, metrics: List[Any]) -> Dict:
        """적절한 전략을 선택하여 결과를 파싱"""
        for strategy in self.strategies:
            if strategy.can_parse(result):
                print(f"📋 파싱 전략 선택: {strategy.__class__.__name__}")
                try:
                    return strategy.parse(result, dataset, metrics)
                except Exception as e:
                    print(f"⚠️  {strategy.__class__.__name__} 실패: {e}")
                    continue
        
        # 모든 전략이 실패한 경우
        raise ValueError("모든 파싱 전략이 실패했습니다.")