#!/usr/bin/env python3
"""
RAGAS 안정성 검증 테스트 - 다른 데이터셋 사용
두 번째 데이터셋으로 RAGAS 메트릭의 일관성을 검증합니다.
"""

import os
import json
import time
import logging
import requests
from dotenv import load_dotenv
import uuid
from datetime import datetime
import re

# 로그 설정
log_filename = f'ragas_validation_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 두 번째 테스트 데이터 (API 설계 관련 - 더 복잡한 평가 시나리오)
TEST_DATA = {
    "question": "API 설계에서 RESTful 원칙이란 무엇인가요?",
    "contexts": [
        "RESTful API는 HTTP 메서드를 의미에 맞게 사용하는 것이 중요합니다.",
        "자원(Resource)은 URI로 표현되며, 명사 형태로 작성해야 합니다.",
        "상태 코드를 적절히 사용하여 요청 처리 결과를 명확히 전달해야 합니다."
    ],
    "answer": "RESTful 원칙은 웹 애플리케이션 개발에서 사용되는 아키텍처 스타일입니다. SOAP와 달리 가볍고 빠른 특징을 가지고 있으며, JSON과 XML 형식을 모두 지원합니다. 또한 마이크로서비스 아키텍처와 잘 어울리는 특징이 있어 많은 회사에서 채택하고 있습니다.",
    "ground_truth": "RESTful 원칙은 HTTP 메서드의 의미적 사용, 자원의 URI 표현, 적절한 상태 코드 사용을 통해 일관되고 예측 가능한 API를 설계하는 것입니다."
}

# RAGAS 메트릭별 프롬프트 (이전과 동일)
PROMPTS = {
    "faithfulness": {
        "system": "You are an expert evaluator for RAG systems. Extract statements from the given answer exactly as they appear, without interpretation or modification.",
        "user": """Given an answer, extract each sentence or claim exactly as stated in the original answer.

IMPORTANT: Do NOT interpret, rephrase, or modify the sentences. Extract them EXACTLY as they appear in the answer.

Answer: {answer}

Return a JSON object with a single key 'statements' containing an array of strings, where each string is a sentence or claim from the answer.

Example for "The sky is blue. Water is wet.":
{{"statements": ["The sky is blue.", "Water is wet."]}}"""
    },
    "answer_relevancy": {
        "system": "You are an expert evaluator. Assess if the answer is relevant to the question.",
        "user": """Question: {question}
Answer: {answer}

Evaluate if the answer addresses the question. Return a JSON object with 'reason' explaining your assessment.

Example:
{{"reason": "The answer directly addresses the question by explaining..."}}"""
    },
    "context_recall": {
        "system": "You are an expert evaluator. Assess if the contexts contain information needed for the ground truth.",
        "user": """Question: {question}
Ground Truth: {ground_truth}
Contexts: {contexts}

Evaluate if the contexts contain all information needed to derive the ground truth. Return a JSON with 'reason'.

Example:
{{"reason": "The contexts contain all necessary information..."}}"""
    },
    "context_precision": {
        "system": "You are an expert evaluator. Assess the precision and relevance of the contexts.",
        "user": """Question: {question}
Contexts: {contexts}

Evaluate if the contexts are precise and relevant without unnecessary information. Return a JSON with 'reason'.

Example:
{{"reason": "The contexts are highly relevant with minimal irrelevant information..."}}"""
    }
}


def parse_json_response(content: str) -> dict:
    """JSON 응답 파싱 (여러 형식 지원)"""
    content = content.strip()
    
    # 1. 마크다운 코드 블록 제거
    if "```json" in content or "```" in content:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    
    # 2. JSON 객체 추출
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(content[start:end+1])
        except json.JSONDecodeError:
            pass
    
    # 3. 전체 문자열 파싱
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 4. 실패 시 기본 형식
        return {"error": "Failed to parse JSON", "raw": content}


def test_gemini_metric(metric_name: str) -> dict:
    """Gemini로 특정 메트릭 테스트"""
    logger.info(f"\n[Gemini] {metric_name} 테스트 시작")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"model": "gemini", "metric": metric_name, "success": False, "error": "No API key"}
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    # 프롬프트 준비
    prompt_config = PROMPTS[metric_name]
    if metric_name == "faithfulness":
        user_prompt = prompt_config["user"].format(answer=TEST_DATA["answer"])
    elif metric_name == "answer_relevancy":
        user_prompt = prompt_config["user"].format(
            question=TEST_DATA["question"],
            answer=TEST_DATA["answer"]
        )
    elif metric_name == "context_recall":
        user_prompt = prompt_config["user"].format(
            question=TEST_DATA["question"],
            ground_truth=TEST_DATA["ground_truth"],
            contexts="\n".join(TEST_DATA["contexts"])
        )
    elif metric_name == "context_precision":
        user_prompt = prompt_config["user"].format(
            question=TEST_DATA["question"],
            contexts="\n".join(TEST_DATA["contexts"])
        )
    
    # 전체 프롬프트 구성
    full_prompt = f"{prompt_config['system']}\n\n{user_prompt}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": full_prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 4096
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if "candidates" in data and data["candidates"]:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(f"[Gemini] 원본 응답:\n{content}")
            
            parsed = parse_json_response(content)
            logger.info(f"[Gemini] 파싱된 JSON:\n{json.dumps(parsed, ensure_ascii=False, indent=2)}")
            
            return {
                "model": "gemini",
                "metric": metric_name,
                "success": True,
                "raw_response": content,
                "parsed_response": parsed
            }
        else:
            return {
                "model": "gemini",
                "metric": metric_name,
                "success": False,
                "error": "No candidates in response"
            }
            
    except Exception as e:
        logger.error(f"[Gemini] {metric_name} 오류: {str(e)}")
        return {
            "model": "gemini",
            "metric": metric_name,
            "success": False,
            "error": str(e)
        }


def test_hcx_metric(metric_name: str) -> dict:
    """HCX로 특정 메트릭 테스트"""
    logger.info(f"\n[HCX] {metric_name} 테스트 시작")
    
    api_key = os.getenv("CLOVA_STUDIO_API_KEY")
    if not api_key:
        return {"model": "hcx", "metric": metric_name, "success": False, "error": "No API key"}
    
    api_url = "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-NCP-CLOVASTUDIO-API-KEY": api_key,
        "X-NCP-APIGW-API-KEY": api_key,
        "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    
    # 프롬프트 준비
    prompt_config = PROMPTS[metric_name]
    if metric_name == "faithfulness":
        user_prompt = prompt_config["user"].format(answer=TEST_DATA["answer"])
    elif metric_name == "answer_relevancy":
        user_prompt = prompt_config["user"].format(
            question=TEST_DATA["question"],
            answer=TEST_DATA["answer"]
        )
    elif metric_name == "context_recall":
        user_prompt = prompt_config["user"].format(
            question=TEST_DATA["question"],
            ground_truth=TEST_DATA["ground_truth"],
            contexts="\n".join(TEST_DATA["contexts"])
        )
    elif metric_name == "context_precision":
        user_prompt = prompt_config["user"].format(
            question=TEST_DATA["question"],
            contexts="\n".join(TEST_DATA["contexts"])
        )
    
    body = {
        "messages": [
            {
                "role": "system",
                "content": prompt_config["system"]
            },
            {
                "role": "user",
                "content": user_prompt
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
    
    try:
        response = requests.post(api_url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if "result" in data and "message" in data["result"]:
            content = data["result"]["message"]["content"]
        elif "message" in data:
            content = data["message"]["content"]
        else:
            content = ""
        
        logger.info(f"[HCX] 원본 응답:\n{content}")
        
        parsed = parse_json_response(content)
        logger.info(f"[HCX] 파싱된 JSON:\n{json.dumps(parsed, ensure_ascii=False, indent=2)}")
        
        return {
            "model": "hcx",
            "metric": metric_name,
            "success": True,
            "raw_response": content,
            "parsed_response": parsed
        }
        
    except Exception as e:
        logger.error(f"[HCX] {metric_name} 오류: {str(e)}")
        return {
            "model": "hcx",
            "metric": metric_name,
            "success": False,
            "error": str(e)
        }


def main():
    """메인 테스트 함수"""
    logger.info("=" * 80)
    logger.info("RAGAS 안정성 검증 테스트 - 두 번째 데이터셋")
    logger.info("=" * 80)
    
    logger.info(f"\n테스트 데이터:")
    logger.info(f"질문: {TEST_DATA['question']}")
    logger.info(f"답변: {TEST_DATA['answer'][:100]}...")
    logger.info(f"정답: {TEST_DATA['ground_truth'][:100]}...")
    
    # 메트릭 리스트
    metrics = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
    
    # 결과 저장
    all_results = []
    
    # 각 메트릭에 대해 테스트
    for metric in metrics:
        logger.info(f"\n{'='*60}")
        logger.info(f"{metric.upper()} 메트릭 테스트")
        logger.info(f"{'='*60}")
        
        # Gemini 테스트
        gemini_result = test_gemini_metric(metric)
        all_results.append(gemini_result)
        time.sleep(2)  # API 제한 방지
        
        # HCX 테스트
        hcx_result = test_hcx_metric(metric)
        all_results.append(hcx_result)
        time.sleep(3)  # HCX는 더 긴 대기
    
    # 결과 요약
    logger.info("\n" + "=" * 80)
    logger.info("안정성 검증 테스트 결과 요약")
    logger.info("=" * 80)
    
    # 모델별 성공률 계산
    for model in ["gemini", "hcx"]:
        model_results = [r for r in all_results if r["model"] == model]
        success_count = sum(1 for r in model_results if r["success"])
        total_count = len(model_results)
        
        logger.info(f"\n{model.upper()} 결과:")
        logger.info(f"- 성공률: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)")
        
        for metric in metrics:
            metric_result = next((r for r in model_results if r["metric"] == metric), None)
            if metric_result and metric_result["success"]:
                parsed = metric_result.get("parsed_response", {})
                if metric == "faithfulness" and "statements" in parsed:
                    logger.info(f"- {metric}: ✅ (statements: {len(parsed['statements'])}개)")
                elif "reason" in parsed:
                    logger.info(f"- {metric}: ✅ (reason 길이: {len(parsed['reason'])}자)")
                else:
                    logger.info(f"- {metric}: ✅")
            else:
                logger.info(f"- {metric}: ❌")
    
    # Faithfulness 비교 분석
    logger.info("\n" + "=" * 80)
    logger.info("Faithfulness 분석 - 답변과 컨텍스트 불일치 시나리오")
    logger.info("=" * 80)
    
    logger.info(f"\n원본 답변:")
    logger.info(f"{TEST_DATA['answer']}")
    
    logger.info(f"\n제공된 컨텍스트:")
    for i, context in enumerate(TEST_DATA['contexts'], 1):
        logger.info(f"  {i}. {context}")
    
    for model in ["gemini", "hcx"]:
        faith_result = next((r for r in all_results if r["model"] == model and r["metric"] == "faithfulness"), None)
        if faith_result and faith_result["success"]:
            parsed = faith_result.get("parsed_response", {})
            if "statements" in parsed:
                logger.info(f"\n{model.upper()} 추출된 statements:")
                for i, stmt in enumerate(parsed["statements"], 1):
                    logger.info(f"  {i}. {stmt}")
    
    # 전체 테스트 성공 여부 확인
    total_success = sum(1 for r in all_results if r["success"])
    total_tests = len(all_results)
    overall_success_rate = total_success / total_tests * 100
    
    logger.info(f"\n전체 테스트 성공률: {total_success}/{total_tests} ({overall_success_rate:.0f}%)")
    
    if overall_success_rate == 100:
        logger.info("🎉 모든 테스트 통과! RAGAS 시스템이 안정적으로 작동합니다.")
        test_passed = True
    else:
        logger.info("⚠️  일부 테스트 실패. 추가 검토가 필요합니다.")
        test_passed = False
    
    # 결과 파일 저장
    output_file = f"ragas_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_summary = {
        "test_timestamp": datetime.now().isoformat(),
        "test_data": TEST_DATA,
        "overall_success_rate": overall_success_rate,
        "test_passed": test_passed,
        "detailed_results": all_results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n결과가 {output_file}에 저장되었습니다.")
    logger.info(f"로그 파일: {log_filename}")
    
    return test_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)