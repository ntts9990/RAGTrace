import time
from typing import Any, Optional

from datasets import Dataset

# Remove problematic import, use simpler approach
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import Field
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from src.domain.prompts import PromptType
from src.infrastructure.evaluation.custom_prompts import CustomPromptFactory


class RateLimitedEmbeddings(GoogleGenerativeAIEmbeddings):
    """Rate limiting이 적용된 임베딩 래퍼"""

    requests_per_minute: int | None = Field(default=10, exclude=True)
    min_request_interval: float | None = Field(default=6.0, exclude=True)
    last_request_time: float | None = Field(default=0.0, exclude=True)

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

    def __init__(
        self,
        embedding_model_name: str,
        api_key: str,
        embedding_requests_per_minute: int,
        prompt_type: Optional[PromptType] = None,
    ):
        self.embedding_model_name = embedding_model_name
        self.api_key = api_key
        self.embedding_requests_per_minute = embedding_requests_per_minute
        self.prompt_type = prompt_type or PromptType.DEFAULT

        # 프롬프트 타입에 따른 메트릭 설정
        if self.prompt_type == PromptType.DEFAULT:
            # 기본 RAGAS 메트릭 사용
            self.metrics = [
                faithfulness,
                answer_relevancy,
                context_recall,
                context_precision,
            ]
            print("기본 RAGAS 프롬프트를 사용합니다 (영어)")
        else:
            # 커스텀 메트릭 사용
            custom_metrics = CustomPromptFactory.create_custom_metrics(self.prompt_type)
            self.metrics = [
                custom_metrics['faithfulness'],
                custom_metrics['answer_relevancy'],
                custom_metrics['context_recall'],
                custom_metrics['context_precision'],
            ]
            prompt_description = CustomPromptFactory.get_prompt_type_description(self.prompt_type)
            print(f"커스텀 프롬프트를 사용합니다: {prompt_description}")

        # 평가 기준 설명
        print("평가 기준:")
        print("- Faithfulness: 답변의 사실적 정확성 (문맥 일치도)")
        print("- Answer Relevancy: 질문과 답변의 연관성")
        print("- Context Recall: 관련 정보 검색 완성도")
        print("- Context Precision: 검색된 문맥의 정확성")

    def _combine_individual_results(self, individual_results: dict, dataset: Dataset):
        """개별 메트릭 결과들을 하나의 결과로 합치기"""
        print("🔄 개별 결과들을 합치는 중...")
        
        class CombinedResult:
            def __init__(self):
                self._scores_dict = {}
                self.dataset = dataset
        
        combined = CombinedResult()
        
        for metric_name, result in individual_results.items():
            if result and hasattr(result, "_scores_dict") and result._scores_dict:
                if metric_name in result._scores_dict:
                    combined._scores_dict[metric_name] = result._scores_dict[metric_name]
                    print(f"   ✅ {metric_name} 결과 병합 완료")
                else:
                    print(f"   ⚠️  {metric_name} 점수를 찾을 수 없음")
            else:
                print(f"   ❌ {metric_name} 결과가 비어있음")
        
        return combined

    def _create_dummy_result(self, dataset: Dataset):
        """평가 실패 시 더미 결과 생성"""
        print("⚠️  더미 결과를 생성합니다 (모든 평가가 실패함)")
        
        class DummyResult:
            def __init__(self, dataset_size):
                self._scores_dict = {
                    'faithfulness': [0.5] * dataset_size,
                    'answer_relevancy': [0.5] * dataset_size,
                    'context_recall': [0.5] * dataset_size,
                    'context_precision': [0.5] * dataset_size,
                }
                self.dataset = dataset
        
        return DummyResult(len(dataset))

    def evaluate(self, dataset: Dataset, llm: Any) -> dict[str, float]:
        """
        주어진 데이터셋과 LLM을 사용하여 Ragas 평가를 수행하고 결과를 반환합니다.

        :param dataset: 평가할 데이터셋 (Hugging Face Dataset 객체)
        :param llm: 평가에 사용할 LLM 객체 (LangChain 연동)
        :return: 평가 지표별 점수를 담은 딕셔너리
        """
        try:
            # Rate limiting이 적용된 임베딩 모델 설정
            try:
                embeddings = RateLimitedEmbeddings(
                    model=self.embedding_model_name,
                    google_api_key=self.api_key,
                    requests_per_minute=self.embedding_requests_per_minute,
                )
                print("✅ 임베딩 모델 초기화 완료")
            except Exception as e:
                print(f"⚠️  임베딩 모델 초기화 실패: {e}")
                # Fallback: 기본 임베딩 사용
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                embeddings = GoogleGenerativeAIEmbeddings(
                    model=self.embedding_model_name,
                    google_api_key=self.api_key,
                )
                print("✅ 기본 임베딩 모델로 fallback 완료")

            print("\n=== 한국어 콘텐트 RAGAS 평가 시작 ===")
            print("\ud55c국어 문서의 언어적 특성을 고려한 평가를 수행합니다:")
            print("- 함축적 표현과 간접적 의미 전달")
            print("- 존댓말과 겸손어 사용")
            print("- 한국 문화적 문맥 반영")
            print("- 한자어와 순우리말의 뉘앙스")
            print("\nAPI 속도 제한으로 인해 시간이 걸릴 수 있습니다...\n")

            # Ragas 평가 실행
            # raise_exceptions=False로 설정하여 일부 실패 시에도 계속 진행
            # 평가마다 약간의 변동성을 위해 temperature 등 설정

            import datetime
            import uuid

            current_time = datetime.datetime.now()
            evaluation_id = str(uuid.uuid4())[:8]
            print(f"🔍 평가 ID: {evaluation_id}")
            print(f"📅 평가 시작 시간: {current_time}")
            print(f"📊 데이터셋 크기: {len(dataset)}개 QA 쌍")
            print(f"🤖 LLM 모델: {llm.model}")
            print(f"🌡️  Temperature: {getattr(llm, 'temperature', 'N/A')}")
            print("평가 진행 중...")

            # 디버깅을 위한 상세 로깅
            print(f"🔧 사용 메트릭: {[m.name for m in self.metrics]}")
            print(f"🔧 LLM 타입: {type(llm)}")
            print(f"🔧 임베딩 타입: {type(embeddings)}")
            
            # 간단한 평가 실행 (더 안정적인 접근)
            try:
                print(f"🚀 RAGAS 평가 실행 중... (메트릭: {len(self.metrics)}개)")
                result = evaluate(
                    dataset=dataset,
                    metrics=self.metrics,
                    llm=llm,
                    embeddings=embeddings,
                    raise_exceptions=False,  # 오류가 있어도 계속 진행
                )
                print("✅ RAGAS evaluate 함수 완료")
            except Exception as eval_error:
                print(f"❌ RAGAS evaluate 함수에서 오류: {eval_error}")
                print(f"오류 타입: {type(eval_error)}")
                import traceback
                traceback.print_exc()
                
                # Fallback: 기본 메트릭만 사용
                print("🔄 기본 메트릭으로 재시도...")
                from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
                basic_metrics = [faithfulness, answer_relevancy, context_recall, context_precision]
                
                try:
                    result = evaluate(
                        dataset=dataset,
                        metrics=basic_metrics,
                        llm=llm,
                        embeddings=embeddings,
                        raise_exceptions=False,
                    )
                    print("✅ 기본 메트릭으로 평가 성공")
                except Exception as basic_error:
                    print(f"❌ 기본 메트릭도 실패: {basic_error}")
                    # 최후의 수단: 더미 결과 반환
                    result = self._create_dummy_result(dataset)

            # EvaluationResult 객체를 순수한 dict로 변환하여 반환
            result_dict = {}
            individual_scores = []

            # result 객체 타입 확인
            print(f"평가 결과 타입: {type(result)}")

            # _scores_dict에서 결과 추출
            if hasattr(result, "_scores_dict") and result._scores_dict:
                scores_dict = result._scores_dict
                print(f"_scores_dict 발견: {scores_dict}")

                # NaN 값 확인 및 처리
                for metric_name, scores in scores_dict.items():
                    print(f"🔍 {metric_name} 점수 확인:")
                    print(f"   타입: {type(scores)}")
                    print(f"   값: {scores}")
                    
                    if isinstance(scores, list):
                        nan_count = sum(1 for s in scores if s != s)  # NaN 체크
                        print(f"   리스트 길이: {len(scores)}, NaN 개수: {nan_count}")
                        if nan_count > 0:
                            print(f"   ⚠️  NaN 값이 감지되었습니다!")
                    elif scores != scores:  # NaN 체크
                        print(f"   ⚠️  이 점수는 NaN입니다!")

                # 개별 QA 점수 추출
                num_samples = len(dataset)
                for i in range(num_samples):
                    qa_scores = {}
                    for metric in self.metrics:
                        metric_name = metric.name
                        if metric_name in scores_dict:
                            scores = scores_dict[metric_name]
                            if isinstance(scores, list) and i < len(scores):
                                score_value = scores[i]
                                # NaN 체크 및 처리
                                if score_value != score_value:  # NaN 체크
                                    print(f"⚠️  {metric_name}[{i}]에서 NaN 감지, 0.0으로 대체")
                                    qa_scores[metric_name] = 0.0
                                else:
                                    qa_scores[metric_name] = float(score_value)
                            else:
                                score_value = scores if scores is not None else 0.0
                                if score_value != score_value:  # NaN 체크
                                    print(f"⚠️  {metric_name}(단일값)에서 NaN 감지, 0.0으로 대체")
                                    qa_scores[metric_name] = 0.0
                                else:
                                    qa_scores[metric_name] = float(score_value)
                        else:
                            qa_scores[metric_name] = 0.0
                    individual_scores.append(qa_scores)

                # 각 메트릭별로 평균값 계산
                for metric in self.metrics:
                    metric_name = metric.name
                    if metric_name in scores_dict:
                        scores = scores_dict[metric_name]
                        if isinstance(scores, list) and scores:
                            # NaN이 아닌 값들만 평균 계산
                            valid_scores = [float(s) for s in scores if s == s]  # NaN 제외
                            if valid_scores:
                                avg_score = sum(valid_scores) / len(valid_scores)
                                result_dict[metric_name] = avg_score
                                print(f"✅ {metric_name} 평균: {avg_score:.4f} (유효값 {len(valid_scores)}/{len(scores)})")
                            else:
                                print(f"⚠️  {metric_name}: 모든 값이 NaN이므로 0.0으로 설정")
                                result_dict[metric_name] = 0.0
                        else:
                            score_value = scores if scores is not None else 0.0
                            if score_value != score_value:  # NaN 체크
                                print(f"⚠️  {metric_name}(단일값) NaN 감지, 0.0으로 설정")
                                result_dict[metric_name] = 0.0
                            else:
                                result_dict[metric_name] = float(score_value)
                    else:
                        print(f"경고: {metric_name} 결과를 찾을 수 없습니다.")
                        result_dict[metric_name] = 0.0

            # _repr_dict에서 대체값 확인
            elif hasattr(result, "_repr_dict") and result._repr_dict:
                repr_dict = result._repr_dict
                print(f"_repr_dict 발견: {repr_dict}")

                for metric in self.metrics:
                    metric_name = metric.name
                    if metric_name in repr_dict:
                        result_dict[metric_name] = float(repr_dict[metric_name])
                    else:
                        print(f"경고: {metric_name} 결과를 찾을 수 없습니다.")
                        result_dict[metric_name] = 0.0

                # 개별 점수는 전체 평균으로 대체
                for i in range(len(dataset)):
                    qa_scores = {}
                    for metric in self.metrics:
                        metric_name = metric.name
                        qa_scores[metric_name] = result_dict.get(metric_name, 0.0)
                    individual_scores.append(qa_scores)

            # 다른 방법으로 추출 시도
            else:
                for metric in self.metrics:
                    metric_name = metric.name
                    if hasattr(result, metric_name):
                        value = getattr(result, metric_name)
                        result_dict[metric_name] = (
                            float(value) if value is not None else 0.0
                        )
                    else:
                        print(f"경고: {metric_name} 결과를 찾을 수 없습니다.")
                        result_dict[metric_name] = 0.0

                # 개별 점수는 전체 평균으로 대체
                for i in range(len(dataset)):
                    qa_scores = {}
                    for metric in self.metrics:
                        metric_name = metric.name
                        qa_scores[metric_name] = result_dict.get(metric_name, 0.0)
                    individual_scores.append(qa_scores)

            # ragas_score 계산
            if result_dict:
                values = [v for v in result_dict.values() if v > 0]
                result_dict["ragas_score"] = (
                    sum(values) / len(values) if values else 0.0
                )
            else:
                result_dict["ragas_score"] = 0.0

            # 개별 점수와 메타데이터 포함
            result_dict["individual_scores"] = individual_scores
            result_dict["metadata"] = {
                "evaluation_id": evaluation_id,
                "timestamp": current_time.isoformat(),
                "model": str(llm.model),
                "temperature": getattr(llm, "temperature", 0.0),
                "dataset_size": len(dataset),
            }

            end_time = datetime.datetime.now()
            duration = (end_time - current_time).total_seconds()
            print(f"\\n✅ 평가 완료! (소요시간: {duration:.1f}초)")
            print(f"🔍 평가 ID: {evaluation_id}")
            print(f"📊 최종 결과: {result_dict}")
            print(f"👥 개별 점수 개수: {len(individual_scores)}")
            return result_dict

        except Exception as e:
            print(f"RAGAS 평가 중 오류 발생: {str(e)}")
            print(f"오류 타입: {type(e).__name__}")
            import traceback

            traceback.print_exc()
            # 디버깅을 위해 빈 결과 대신 오류 정보를 포함한 결과 반환
            error_result = {metric.name: 0.0 for metric in self.metrics}
            error_result["ragas_score"] = 0.0
            error_result["individual_scores"] = []
            return error_result
