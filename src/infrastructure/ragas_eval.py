import time
from typing import Dict, Any, Optional
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import Field
import config


class RateLimitedEmbeddings(GoogleGenerativeAIEmbeddings):
    """Rate limiting이 적용된 임베딩 래퍼"""
    
    requests_per_minute: Optional[int] = Field(default=10, exclude=True)
    min_request_interval: Optional[float] = Field(default=6.0, exclude=True)
    last_request_time: Optional[float] = Field(default=0.0, exclude=True)
    
    def __init__(self, *args, requests_per_minute: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests_per_minute = requests_per_minute
        self.min_request_interval = 60.0 / requests_per_minute
        self.last_request_time = 0
    
    def _rate_limit(self):
        """요청 간 최소 시간 간격을 보장"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def embed_documents(self, texts):
        """문서 임베딩 시 rate limiting 적용"""
        self._rate_limit()
        return super().embed_documents(texts)
    
    def embed_query(self, text):
        """쿼리 임베딩 시 rate limiting 적용"""
        self._rate_limit()
        return super().embed_query(text)


class RagasEvalAdapter:
    """Ragas 라이브러리를 사용한 평가 실행을 담당하는 어댑터"""

    def __init__(self):
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
        ]

    def evaluate(self, dataset: Dataset, llm: Any) -> Dict[str, float]:
        """
        주어진 데이터셋과 LLM을 사용하여 Ragas 평가를 수행하고 결과를 반환합니다.

        :param dataset: 평가할 데이터셋 (Hugging Face Dataset 객체)
        :param llm: 평가에 사용할 LLM 객체 (LangChain 연동)
        :return: 평가 지표별 점수를 담은 딕셔너리
        """
        try:
            # Rate limiting이 적용된 임베딩 모델 설정
            embeddings = RateLimitedEmbeddings(
                model="models/gemini-embedding-exp-03-07",  # 더 안정적인 임베딩 모델 사용
                google_api_key=config.GEMINI_API_KEY,
                requests_per_minute=10,  # Tier 1: 10 RPM for embeddings
            )

            print("RAGAS 평가를 시작합니다. API 속도 제한으로 인해 시간이 걸릴 수 있습니다...")
            
            # Ragas 평가 실행
            # raise_exceptions=False로 설정하여 일부 실패 시에도 계속 진행
            result = evaluate(
                dataset=dataset,
                metrics=self.metrics,
                llm=llm,
                embeddings=embeddings,
                raise_exceptions=False,
            )

            # EvaluationResult 객체를 순수한 dict로 변환하여 반환
            result_dict = {}
            
            # result 객체 타입 확인
            print(f"평가 결과 타입: {type(result)}")
            
            # _scores_dict에서 결과 추출
            if hasattr(result, '_scores_dict') and result._scores_dict:
                scores_dict = result._scores_dict
                print(f"_scores_dict 발견: {scores_dict}")
                
                # 각 메트릭별로 평균값 계산
                for metric in self.metrics:
                    metric_name = metric.name
                    if metric_name in scores_dict:
                        scores = scores_dict[metric_name]
                        if isinstance(scores, list) and scores:
                            # numpy float64를 일반 float로 변환
                            avg_score = sum(float(s) for s in scores) / len(scores)
                            result_dict[metric_name] = avg_score
                        else:
                            result_dict[metric_name] = float(scores) if scores else 0.0
                    else:
                        print(f"경고: {metric_name} 결과를 찾을 수 없습니다.")
                        result_dict[metric_name] = 0.0
            
            # _repr_dict에서 대체값 확인
            elif hasattr(result, '_repr_dict') and result._repr_dict:
                repr_dict = result._repr_dict
                print(f"_repr_dict 발견: {repr_dict}")
                
                for metric in self.metrics:
                    metric_name = metric.name
                    if metric_name in repr_dict:
                        result_dict[metric_name] = float(repr_dict[metric_name])
                    else:
                        print(f"경고: {metric_name} 결과를 찾을 수 없습니다.")
                        result_dict[metric_name] = 0.0
            
            # 다른 방법으로 추출 시도
            else:
                for metric in self.metrics:
                    metric_name = metric.name
                    if hasattr(result, metric_name):
                        value = getattr(result, metric_name)
                        result_dict[metric_name] = float(value) if value is not None else 0.0
                    else:
                        print(f"경고: {metric_name} 결과를 찾을 수 없습니다.")
                        result_dict[metric_name] = 0.0
            
            # ragas_score 계산
            if result_dict:
                values = [v for v in result_dict.values() if v > 0]
                result_dict['ragas_score'] = sum(values) / len(values) if values else 0.0
            else:
                result_dict['ragas_score'] = 0.0
            
            print(f"최종 결과: {result_dict}")
            return result_dict
            
        except Exception as e:
            print(f"RAGAS 평가 중 오류 발생: {str(e)}")
            print(f"오류 타입: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            # 디버깅을 위해 빈 결과 대신 오류 정보를 포함한 결과 반환
            return {
                metric.name: 0.0 for metric in self.metrics
            }
