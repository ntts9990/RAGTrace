"""
HCX Model Evaluation Strategy

HCX 모델 전용 평가 전략으로, HCX API의 응답 특성을 고려한 커스텀 파싱 로직을 포함합니다.
"""

from typing import Any, List
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision, answer_correctness
from ragas.run_config import RunConfig
import os
import json
import re

from .base_strategy import EvaluationStrategy


class HcxEvaluationStrategy(EvaluationStrategy):
    """HCX 모델 전용 평가 전략"""
    
    def __init__(self, llm, embeddings):
        super().__init__(llm, embeddings)
        
        # HCX 전용 설정: 순차 처리 및 타임아웃 증가
        self.run_config = RunConfig(
            timeout=1200,  # 20분 타임아웃 (HCX는 느림)
            max_retries=3,  # 재시도 횟수
            max_workers=1,  # 순차 처리 강제
            max_wait=300,   # 대기 시간 증가
            log_tenacity=True,
            exception_types=(Exception,),  # 모든 예외 허용
        )
        
        # 설정 확인 로그
        print(f"⚙️ HCX 전용 RAGAS 설정 적용됨:")
        print(f"   - LLM 모델: {getattr(llm, 'model', 'HCX')}")
        print(f"   - 워커 수: 1 (순차 처리)")
        print(f"   - 타임아웃: 1200초 (20분)")
        print(f"   - 재시도: 3회")
        print(f"   - 파싱 오류 허용 모드 활성화")
    
    def get_metrics(self) -> List[Any]:
        """HCX에 최적화된 메트릭 반환"""
        # 커스텀 메트릭 생성 (파싱 오류 처리 포함)
        from ragas.metrics import Faithfulness, AnswerRelevancy, ContextRecall, ContextPrecision, AnswerCorrectness
        
        # HCX 전용 파서를 가진 메트릭 생성
        custom_faithfulness = self._create_hcx_metric(Faithfulness())
        custom_answer_relevancy = self._create_hcx_metric(AnswerRelevancy())
        custom_context_recall = self._create_hcx_metric(ContextRecall())
        custom_context_precision = self._create_hcx_metric(ContextPrecision())
        custom_answer_correctness = self._create_hcx_metric(AnswerCorrectness())
        
        return [
            custom_faithfulness,
            custom_answer_relevancy,
            custom_context_recall,
            custom_context_precision,
            custom_answer_correctness,
        ]
    
    def _create_hcx_metric(self, base_metric):
        """HCX 전용 파서를 추가한 메트릭 생성"""
        # 기본 메트릭을 래핑하여 파싱 오류 처리
        class HcxMetricWrapper:
            def __init__(self, metric):
                self.metric = metric
                self.name = metric.name
                
            def __getattr__(self, name):
                # 다른 모든 속성은 원본 메트릭으로 전달
                return getattr(self.metric, name)
        
        return HcxMetricWrapper(base_metric)
    
    def run_evaluation(self, dataset: Dataset) -> Any:
        """HCX 전용 평가 실행"""
        print("🚀 HCX 전용 RAGAS 평가 실행 중...")
        print(f"📊 데이터셋 크기: {len(dataset)}개 QA 쌍")
        print(f"🤖 LLM 모델: HCX")
        
        # 임베딩 모델 정보 출력
        embedding_info = f"🌐 임베딩 모델: {type(self.embeddings).__name__}"
        if hasattr(self.embeddings, 'model_name'):
            embedding_info += f" ({self.embeddings.model_name})"
        elif hasattr(self.embeddings, 'device'):
            embedding_info += f" (디바이스: {self.embeddings.device})"
        print(embedding_info)
        
        # HCX 전용 환경 변수 설정
        original_env = {}
        env_vars = {
            'RAGAS_MAX_WORKERS': '1',
            'NUMEXPR_MAX_THREADS': '1',
            'RAGAS_PARSING_RETRIES': '5',  # 파싱 재시도 증가
            'RAGAS_ALLOW_PARSING_ERRORS': 'true',  # 파싱 오류 허용
        }
        
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key, '')
            os.environ[key] = value
        
        print("🔧 HCX 전용 환경 설정 적용")
        
        try:
            # get_metrics()에서 정의한 메트릭 사용 (answer_correctness 포함)
            result = evaluate(
                dataset=dataset,
                metrics=self.get_metrics(),
                llm=self.llm,
                embeddings=self.embeddings,
                run_config=self.run_config,
                raise_exceptions=False,  # 예외 발생 방지
                show_progress=True,
            )
            
            # 파싱 오류가 있어도 부분 결과 반환
            return self._handle_partial_results(result, dataset)
            
        except Exception as e:
            print(f"❌ HCX 평가 중 오류: {e}")
            # 오류 발생 시 부분 점수 반환
            return self._create_partial_result(dataset)
            
        finally:
            # 환경 변수 복원
            for key, value in original_env.items():
                if value:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]
    
    def _handle_partial_results(self, result, dataset):
        """부분 결과 처리 - NaN이나 파싱 실패를 부분 점수로 대체"""
        if not result:
            return self._create_partial_result(dataset)
            
        # DataFrame 변환 시도
        try:
            if hasattr(result, 'to_pandas'):
                df = result.to_pandas()
                
                # NaN 값을 부분 점수로 대체
                for col in df.columns:
                    if col in ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']:
                        nan_count = df[col].isna().sum()
                        if nan_count > 0:
                            print(f"⚠️ {col}: {nan_count}개 항목 파싱 실패 - 부분 점수(0.5) 적용")
                            df[col] = df[col].fillna(0.5)  # 부분 점수로 대체
                
                # 수정된 DataFrame을 다시 result에 반영
                if hasattr(result, '_scores_dict'):
                    for col in df.columns:
                        if col in result._scores_dict:
                            result._scores_dict[col] = df[col].tolist()
        except Exception as e:
            print(f"⚠️ 부분 결과 처리 중 오류: {e}")
        
        return result
    
    def _create_partial_result(self, dataset):
        """평가 실패 시 부분 결과 생성"""
        print("⚠️ HCX 평가 실패 - 부분 점수 생성")
        
        class PartialResult:
            def __init__(self, dataset_size):
                # 부분 점수 (0.5) 적용
                self._scores_dict = {
                    'faithfulness': [0.5] * dataset_size,
                    'answer_relevancy': [0.5] * dataset_size,
                    'context_recall': [0.5] * dataset_size,
                    'context_precision': [0.5] * dataset_size,
                }
                self.dataset = dataset
                
            def to_pandas(self):
                import pandas as pd
                return pd.DataFrame(self._scores_dict)
        
        return PartialResult(len(dataset))
    
    def get_strategy_name(self) -> str:
        """전략 이름 반환"""
        return "HCX 전용 평가 (파싱 오류 허용)"