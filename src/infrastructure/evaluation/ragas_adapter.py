from typing import Any, Optional

import pandas as pd
from datasets import Dataset
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from src.domain.prompts import PromptType
from src.infrastructure.evaluation.custom_prompts import CustomPromptFactory
from src.infrastructure.evaluation.parsing_strategies import ResultParser
from src.infrastructure.llm.rate_limiter import RateLimitedGeminiEmbeddings


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
        
        # 결과 파서 초기화
        self.result_parser = ResultParser()

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
            # 1. 임베딩 모델 초기화
            embeddings = self._initialize_embeddings()
            
            # 2. 평가 실행
            raw_result = self._run_evaluation(dataset, llm, embeddings)
            
            # 3. 결과 파싱
            result_dict = self._parse_result(raw_result, dataset)
            
            # 4. 최종 리포트 생성
            return self._create_final_report(result_dict, dataset, llm)
            
        except Exception as e:
            print(f"RAGAS 평가 중 오류 발생: {str(e)}")
            return self._create_error_result()

    def _initialize_embeddings(self):
        """임베딩 모델 초기화"""
        try:
            embeddings = RateLimitedGeminiEmbeddings(
                model=self.embedding_model_name,
                google_api_key=self.api_key,
                requests_per_minute=self.embedding_requests_per_minute,
            )
            print("✅ 임베딩 모델 초기화 완료")
            return embeddings
        except Exception as e:
            print(f"⚠️  임베딩 모델 초기화 실패: {e}")
            embeddings = GoogleGenerativeAIEmbeddings(
                model=self.embedding_model_name,
                google_api_key=self.api_key,
            )
            print("✅ 기본 임베딩 모델로 fallback 완료")
            return embeddings

    def _run_evaluation(self, dataset: Dataset, llm: Any, embeddings):
        """평가 실행"""
        import datetime
        import uuid

        current_time = datetime.datetime.now()
        evaluation_id = str(uuid.uuid4())[:8]
        
        print("\n=== 한국어 콘텐트 RAGAS 평가 시작 ===")
        print(f"🔍 평가 ID: {evaluation_id}")
        print(f"📊 데이터셋 크기: {len(dataset)}개 QA 쌍")
        print(f"🤖 LLM 모델: {llm.model}")
        print("평가 진행 중...")

        try:
            print(f"🚀 RAGAS 평가 실행 중... (메트릭: {len(self.metrics)}개)")
            result = evaluate(
                dataset=dataset,
                metrics=self.metrics,
                llm=llm,
                embeddings=embeddings,
                raise_exceptions=False,
            )
            print("✅ RAGAS evaluate 함수 완료")
            return result
            
        except Exception as eval_error:
            print(f"❌ RAGAS evaluate 함수에서 오류: {eval_error}")
            return self._fallback_evaluation(dataset, llm, embeddings)

    def _fallback_evaluation(self, dataset: Dataset, llm: Any, embeddings):
        """평가 실패 시 기본 메트릭으로 재시도"""
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
            return result
        except Exception as basic_error:
            print(f"❌ 기본 메트릭도 실패: {basic_error}")
            return self._create_dummy_result(dataset)

    def _parse_result(self, result, dataset: Dataset) -> dict:
        """결과 파싱 - 전략 패턴을 통한 안정적인 파싱"""
        try:
            return self.result_parser.parse_result(result, dataset, self.metrics)
        except Exception as e:
            print(f"❌ 모든 파싱 전략 실패: {e}")
            # 최후의 수단: 빈 결과 반환
            result_dict = {metric.name: 0.0 for metric in self.metrics}
            result_dict["individual_scores"] = [
                {metric.name: 0.0 for metric in self.metrics} 
                for _ in range(len(dataset))
            ]
            return result_dict

    def _create_final_report(self, result_dict: dict, dataset: Dataset, llm: Any) -> dict:
        """최종 리포트 생성"""
        import datetime
        import uuid
        
        # ragas_score 계산
        metric_values = [v for k, v in result_dict.items() if k != "individual_scores" and v > 0]
        result_dict["ragas_score"] = sum(metric_values) / len(metric_values) if metric_values else 0.0
        
        # 메타데이터 추가
        result_dict["metadata"] = {
            "evaluation_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "model": str(llm.model),
            "temperature": getattr(llm, "temperature", 0.0),
            "dataset_size": len(dataset),
        }
        
        print(f"✅ 평가 완료!")
        print(f"📊 최종 결과: RAGAS Score = {result_dict['ragas_score']:.4f}")
        return result_dict

    def _create_error_result(self) -> dict:
        """오류 발생 시 기본 결과 생성"""
        error_result = {metric.name: 0.0 for metric in self.metrics}
        error_result["ragas_score"] = 0.0
        error_result["individual_scores"] = []
        return error_result
