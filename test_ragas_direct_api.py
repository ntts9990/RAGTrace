#!/usr/bin/env python3
"""
RAGAS 메트릭을 위한 직접 API 호출 테스트
Gemini와 HCX 모델을 사용하여 RAGAS 평가를 테스트합니다.
"""

import os
import json
import time
import logging
from typing import List, Dict, Any
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import uuid
from datetime import datetime

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'ragas_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 테스트용 데이터셋 (evaluation_data.json에서 일부 추출)
TEST_DATA = [
    {
        "question": "클린 아키텍처의 핵심 원칙은 무엇인가요?",
        "contexts": [
            "클린 아키텍처는 로버트 C. 마틴이 제안한 소프트웨어 설계 철학입니다.",
            "가장 중요한 규칙은 '의존성 규칙'으로, 모든 소스 코드 의존성은 외부에서 내부로, 즉 저수준의 구체적인 정책에서 고수준의 추상적인 정책으로만 향해야 합니다.",
            "이를 통해 시스템은 프레임워크, 데이터베이스, UI와 독립적으로 유지될 수 있습니다."
        ],
        "answer": "클린 아키텍처의 핵심 원칙은 의존성 규칙입니다. 이는 모든 소스코드 의존성이 외부에서 내부로 향해야 한다는 것을 의미합니다.",
        "ground_truth": "클린 아키텍처의 핵심 원칙은 의존성 규칙으로, 모든 소스 코드 의존성은 외부에서 내부로, 저수준 정책에서 고수준 정책으로 향해야 합니다."
    },
    {
        "question": "RAGAS의 Faithfulness 지표는 무엇을 측정하나요?",
        "contexts": [
            "Faithfulness는 생성된 답변이 제공된 컨텍스트에 얼마나 충실한지를 평가합니다.",
            "이 지표는 LLM의 환각(Hallucination) 현상을 측정하는 데 사용됩니다.",
            "Answer Relevancy는 답변이 질문과 관련이 있는지를 측정하는 다른 지표입니다."
        ],
        "answer": "Faithfulness는 생성된 답변이 제공된 컨텍스트에 얼마나 충실한지, 즉 컨텍스트에 없는 내용을 지어내지 않았는지를 평가하는 지표입니다.",
        "ground_truth": "Faithfulness는 생성된 답변이 제공된 컨텍스트에 얼마나 충실한지를 평가하여 LLM의 환각 현상을 측정하는 지표이다."
    }
]

# RAGAS 메트릭 프롬프트 템플릿
PROMPTS = {
    "faithfulness": """Given a question, an answer, and sentences from the answer analyze the complexity of each sentence given under 'sentences' and break down each sentence into one or more fully understandable statements while also ensuring no pronouns are used without explicitly mentioning the nouns they refer to.
        
IMPORTANT: Your task is to break down the sentences into simpler, standalone statements. Each statement should be clear and self-contained.

question: {question}
answer: {answer}
sentences: {sentences}

Return the result as a JSON with a single key 'statements' containing an array of strings, where each string is a simplified statement.

Example:
{{"statements": ["statement 1", "statement 2", "statement 3"]}}""",

    "answer_relevancy": """You are an expert evaluator. Given a question and an answer, your job is to determine if the answer is relevant to the question.

Question: {question}
Answer: {answer}

Provide your evaluation as a JSON object with the key 'reason' explaining whether the answer is relevant to the question.

Example:
{{"reason": "The answer directly addresses the question by explaining..."}}""",

    "context_recall": """You are an expert evaluator. Given a question, its ground truth answer, and the provided contexts, determine if the contexts contain all the information needed to answer the question correctly.

Question: {question}
Ground Truth: {ground_truth}
Contexts: {contexts}

Provide your evaluation as a JSON object with the key 'reason' explaining the completeness of the contexts.

Example:
{{"reason": "The contexts contain all necessary information to answer the question..."}}""",

    "context_precision": """You are an expert evaluator. Given a question and the provided contexts, determine if the contexts are precise and relevant without containing unnecessary information.

Question: {question}
Contexts: {contexts}

Provide your evaluation as a JSON object with the key 'reason' explaining the precision of the contexts.

Example:
{{"reason": "The contexts are highly relevant to the question with minimal irrelevant information..."}}"""
}


class GeminiTester:
    """Gemini API 직접 호출 테스터"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # 최대 출력 토큰을 HCX와 동일하게 설정
        generation_config = genai.GenerationConfig(
            max_output_tokens=4096,
            temperature=0.1,
            top_p=0.8,
        )
        self.model = genai.GenerativeModel(
            model_name='models/gemini-2.5-flash-preview-05-20',
            generation_config=generation_config
        )
        logger.info("Gemini 테스터 초기화 완료")
    
    def test_metric(self, metric_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """특정 메트릭 테스트"""
        logger.info(f"[Gemini] {metric_name} 테스트 시작")
        
        prompt_template = PROMPTS[metric_name]
        
        # 프롬프트 준비
        if metric_name == "faithfulness":
            # Faithfulness는 답변을 문장으로 분리해야 함
            sentences = data["answer"].split(". ")
            sentences = [s.strip() + "." if not s.endswith(".") else s.strip() for s in sentences if s]
            prompt = prompt_template.format(
                question=data["question"],
                answer=data["answer"],
                sentences=json.dumps(sentences, ensure_ascii=False)
            )
        elif metric_name == "answer_relevancy":
            prompt = prompt_template.format(
                question=data["question"],
                answer=data["answer"]
            )
        elif metric_name == "context_recall":
            prompt = prompt_template.format(
                question=data["question"],
                ground_truth=data["ground_truth"],
                contexts="\n".join(data["contexts"])
            )
        elif metric_name == "context_precision":
            prompt = prompt_template.format(
                question=data["question"],
                contexts="\n".join(data["contexts"])
            )
        
        try:
            # API 호출
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            logger.info(f"[Gemini] {metric_name} 원본 응답: {result[:200]}...")
            
            # JSON 파싱 시도
            parsed_result = self._parse_json_response(result)
            logger.info(f"[Gemini] {metric_name} 파싱된 결과: {json.dumps(parsed_result, ensure_ascii=False, indent=2)}")
            
            return {
                "metric": metric_name,
                "model": "gemini",
                "success": True,
                "raw_response": result,
                "parsed_response": parsed_result
            }
            
        except Exception as e:
            logger.error(f"[Gemini] {metric_name} 테스트 실패: {str(e)}")
            return {
                "metric": metric_name,
                "model": "gemini",
                "success": False,
                "error": str(e)
            }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """JSON 응답 파싱"""
        import re
        
        # 마크다운 코드 블록 제거
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)
        
        # JSON 객체 추출
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        if start_idx != -1 and end_idx != -1:
            response = response[start_idx:end_idx+1]
        
        return json.loads(response)


class HCXTester:
    """HCX API 직접 호출 테스터"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model_name = "HCX-005"
        self.api_url = f"https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{self.model_name}"
        logger.info("HCX 테스터 초기화 완료")
    
    def test_metric(self, metric_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """특정 메트릭 테스트"""
        logger.info(f"[HCX] {metric_name} 테스트 시작")
        
        prompt_template = PROMPTS[metric_name]
        
        # 프롬프트 준비
        if metric_name == "faithfulness":
            sentences = data["answer"].split(". ")
            sentences = [s.strip() + "." if not s.endswith(".") else s.strip() for s in sentences if s]
            prompt = prompt_template.format(
                question=data["question"],
                answer=data["answer"],
                sentences=json.dumps(sentences, ensure_ascii=False)
            )
        elif metric_name == "answer_relevancy":
            prompt = prompt_template.format(
                question=data["question"],
                answer=data["answer"]
            )
        elif metric_name == "context_recall":
            prompt = prompt_template.format(
                question=data["question"],
                ground_truth=data["ground_truth"],
                contexts="\n".join(data["contexts"])
            )
        elif metric_name == "context_precision":
            prompt = prompt_template.format(
                question=data["question"],
                contexts="\n".join(data["contexts"])
            )
        
        try:
            # API 호출
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "X-NCP-CLOVASTUDIO-API-KEY": self.api_key,
                "X-NCP-APIGW-API-KEY": self.api_key,
                "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            
            body = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert evaluator for RAG systems. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "maxTokens": 4096,
                "temperature": 0.1,
                "topP": 0.8,
                "topK": 0,
                "repetitionPenalty": 1.1,
                "stop": [],
                "includeAiFilters": False,
            }
            
            response = requests.post(self.api_url, headers=headers, json=body, timeout=60)
            response.raise_for_status()
            
            result_data = response.json()
            
            # HCX API v3 응답 구조 파싱
            content = ""
            if "result" in result_data and "message" in result_data["result"]:
                content = result_data["result"]["message"]["content"]
            elif "message" in result_data:
                content = result_data["message"]["content"]
            
            logger.info(f"[HCX] {metric_name} 원본 응답: {content[:200]}...")
            
            # JSON 파싱 시도
            parsed_result = self._parse_json_response(content)
            logger.info(f"[HCX] {metric_name} 파싱된 결과: {json.dumps(parsed_result, ensure_ascii=False, indent=2)}")
            
            return {
                "metric": metric_name,
                "model": "hcx",
                "success": True,
                "raw_response": content,
                "parsed_response": parsed_result
            }
            
        except Exception as e:
            logger.error(f"[HCX] {metric_name} 테스트 실패: {str(e)}")
            return {
                "metric": metric_name,
                "model": "hcx",
                "success": False,
                "error": str(e)
            }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """JSON 응답 파싱 (HCX 어댑터의 로직 재사용)"""
        import re
        
        response = response.strip()
        
        # 1. JSON 마크다운 블록 추출
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                response = json_str
        
        # 2. JSON 객체 추출
        start_index = response.find('{')
        end_index = response.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = response[start_index : end_index + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # 3. 전체 문자열이 JSON인지 확인
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 4. 실패 시 간단한 형식으로 변환
        escaped_content = response.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return {"answer": escaped_content}


def main():
    """메인 테스트 함수"""
    logger.info("=" * 80)
    logger.info("RAGAS 직접 API 호출 테스트 시작")
    logger.info("=" * 80)
    
    # API 키 확인
    gemini_key = os.getenv("GEMINI_API_KEY")
    hcx_key = os.getenv("CLOVA_STUDIO_API_KEY")
    
    if not gemini_key:
        logger.error("GEMINI_API_KEY가 설정되지 않았습니다.")
        return
    
    if not hcx_key:
        logger.warning("CLOVA_STUDIO_API_KEY가 설정되지 않았습니다. HCX 테스트를 건너뜁니다.")
    
    # 테스터 초기화
    gemini_tester = GeminiTester(gemini_key)
    hcx_tester = HCXTester(hcx_key) if hcx_key else None
    
    # 메트릭 리스트
    metrics = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
    
    # 결과 저장
    all_results = []
    
    # 각 데이터에 대해 테스트
    for idx, data in enumerate(TEST_DATA):
        logger.info(f"\n{'='*60}")
        logger.info(f"테스트 데이터 #{idx + 1}: {data['question'][:50]}...")
        logger.info(f"{'='*60}")
        
        for metric in metrics:
            logger.info(f"\n--- {metric.upper()} 메트릭 테스트 ---")
            
            # Gemini 테스트
            gemini_result = gemini_tester.test_metric(metric, data)
            all_results.append(gemini_result)
            time.sleep(1)  # API 제한 방지
            
            # HCX 테스트
            if hcx_tester:
                hcx_result = hcx_tester.test_metric(metric, data)
                all_results.append(hcx_result)
                time.sleep(2)  # HCX는 더 긴 대기 시간
    
    # 결과 요약
    logger.info("\n" + "=" * 80)
    logger.info("테스트 결과 요약")
    logger.info("=" * 80)
    
    success_count = {"gemini": 0, "hcx": 0}
    total_count = {"gemini": 0, "hcx": 0}
    
    for result in all_results:
        model = result["model"]
        total_count[model] += 1
        if result["success"]:
            success_count[model] += 1
    
    for model in ["gemini", "hcx"]:
        if total_count[model] > 0:
            success_rate = (success_count[model] / total_count[model]) * 100
            logger.info(f"{model.upper()} 성공률: {success_rate:.1f}% ({success_count[model]}/{total_count[model]})")
    
    # 결과 파일 저장
    output_file = f"ragas_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    logger.info(f"\n결과가 {output_file}에 저장되었습니다.")
    
    # 파싱 실패 사례 분석
    logger.info("\n" + "=" * 80)
    logger.info("파싱 실패 사례 분석")
    logger.info("=" * 80)
    
    for result in all_results:
        if not result["success"]:
            logger.warning(f"[{result['model']}] {result['metric']}: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()