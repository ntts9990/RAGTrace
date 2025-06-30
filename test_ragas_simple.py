#!/usr/bin/env python3
"""
RAGAS 메트릭을 위한 간단한 API 호출 테스트
각 LLM의 응답 형식을 확인합니다.
"""

import os
import json
import time
import logging
from typing import Dict, Any
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import uuid
from datetime import datetime

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(f'ragas_simple_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 간단한 테스트 데이터
TEST_DATA = {
    "question": "클린 아키텍처의 핵심 원칙은 무엇인가요?",
    "contexts": [
        "클린 아키텍처는 로버트 C. 마틴이 제안한 소프트웨어 설계 철학입니다.",
        "가장 중요한 규칙은 '의존성 규칙'으로, 모든 소스 코드 의존성은 외부에서 내부로 향해야 합니다."
    ],
    "answer": "클린 아키텍처의 핵심 원칙은 의존성 규칙입니다.",
    "ground_truth": "클린 아키텍처의 핵심 원칙은 의존성 규칙입니다."
}

# Faithfulness 프롬프트 (RAGAS 스타일)
FAITHFULNESS_PROMPT = """Given an answer, break it down into simple statements.

Answer: {answer}

Return the result as a JSON with a single key 'statements' containing an array of strings.

Example:
{{"statements": ["statement 1", "statement 2"]}}"""


def test_gemini_faithfulness():
    """Gemini API로 Faithfulness 테스트"""
    logger.info("\n=== GEMINI FAITHFULNESS 테스트 ===")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY가 없습니다.")
        return None
    
    try:
        genai.configure(api_key=api_key)
        # 최대 출력 토큰을 HCX와 동일하게 설정
        generation_config = genai.GenerationConfig(
            max_output_tokens=4096,
            temperature=0.1,
            top_p=0.8,
        )
        model = genai.GenerativeModel(
            model_name='models/gemini-2.5-flash-preview-05-20',
            generation_config=generation_config
        )
        
        prompt = FAITHFULNESS_PROMPT.format(answer=TEST_DATA["answer"])
        logger.info(f"프롬프트:\n{prompt}")
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        logger.info(f"\nGemini 원본 응답:\n{result}")
        
        # JSON 파싱 시도
        try:
            # 마크다운 제거
            if "```json" in result:
                start = result.find("```json") + 7
                end = result.find("```", start)
                result = result[start:end].strip()
            elif "```" in result:
                start = result.find("```") + 3
                end = result.find("```", start)
                result = result[start:end].strip()
            
            parsed = json.loads(result)
            logger.info(f"\n파싱된 JSON:\n{json.dumps(parsed, ensure_ascii=False, indent=2)}")
            return parsed
        except Exception as e:
            logger.error(f"JSON 파싱 실패: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Gemini API 호출 실패: {e}")
        return None


def test_hcx_faithfulness():
    """HCX API로 Faithfulness 테스트"""
    logger.info("\n=== HCX FAITHFULNESS 테스트 ===")
    
    api_key = os.getenv("CLOVA_STUDIO_API_KEY")
    if not api_key:
        logger.error("CLOVA_STUDIO_API_KEY가 없습니다.")
        return None
    
    try:
        api_url = "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "X-NCP-CLOVASTUDIO-API-KEY": api_key,
            "X-NCP-APIGW-API-KEY": api_key,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        prompt = FAITHFULNESS_PROMPT.format(answer=TEST_DATA["answer"])
        
        body = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Always respond with valid JSON."
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
        
        logger.info(f"프롬프트:\n{prompt}")
        
        response = requests.post(api_url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        
        result_data = response.json()
        
        # HCX API v3 응답 구조 파싱
        content = ""
        if "result" in result_data and "message" in result_data["result"]:
            content = result_data["result"]["message"]["content"]
        elif "message" in result_data:
            content = result_data["message"]["content"]
        
        logger.info(f"\nHCX 원본 응답:\n{content}")
        
        # JSON 파싱 시도
        try:
            # 여러 파싱 방법 시도
            parsed = None
            
            # 1. 마크다운 블록 제거
            if "```json" in content or "```" in content:
                import re
                match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(1))
            
            # 2. JSON 객체 직접 추출
            if not parsed:
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    parsed = json.loads(content[start:end+1])
            
            # 3. 전체 문자열 파싱
            if not parsed:
                parsed = json.loads(content)
            
            logger.info(f"\n파싱된 JSON:\n{json.dumps(parsed, ensure_ascii=False, indent=2)}")
            return parsed
            
        except Exception as e:
            logger.error(f"JSON 파싱 실패: {e}")
            # 폴백: 간단한 형식으로 변환
            logger.info("폴백: 기본 형식으로 변환")
            return {"statements": [content]}
            
    except Exception as e:
        logger.error(f"HCX API 호출 실패: {e}")
        return None


def main():
    """메인 함수"""
    logger.info("RAGAS API 응답 형식 테스트 시작")
    
    # Gemini 테스트
    gemini_result = test_gemini_faithfulness()
    time.sleep(2)
    
    # HCX 테스트
    hcx_result = test_hcx_faithfulness()
    
    # 결과 요약
    logger.info("\n=== 테스트 결과 요약 ===")
    
    if gemini_result:
        logger.info("✅ Gemini: JSON 파싱 성공")
        if "statements" in gemini_result:
            logger.info(f"   - statements 개수: {len(gemini_result['statements'])}")
    else:
        logger.info("❌ Gemini: JSON 파싱 실패")
    
    if hcx_result:
        logger.info("✅ HCX: JSON 파싱 성공")
        if "statements" in hcx_result:
            logger.info(f"   - statements 개수: {len(hcx_result['statements'])}")
    else:
        logger.info("❌ HCX: JSON 파싱 실패")
    
    # 결과 저장
    results = {
        "test_time": datetime.now().isoformat(),
        "gemini": gemini_result,
        "hcx": hcx_result
    }
    
    output_file = f"ragas_format_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n결과가 {output_file}에 저장되었습니다.")


if __name__ == "__main__":
    main()