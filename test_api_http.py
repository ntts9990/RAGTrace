#!/usr/bin/env python3
"""
HTTP 직접 호출로 API 테스트
"""

import os
import json
import requests
from dotenv import load_dotenv
import uuid
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

def test_gemini_http():
    """Gemini HTTP API 직접 호출 테스트"""
    logger.info("\n=== GEMINI HTTP 테스트 ===")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY가 설정되지 않았습니다.")
        return False
    
    # HTTP 직접 호출
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "Respond with simple JSON: {\"status\": \"ok\"}"
            }]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 100
        }
    }
    
    try:
        logger.info("Gemini API 호출 중...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        logger.info(f"응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                logger.info(f"✅ 응답 받음: {content[:100]}...")
                return True
        else:
            logger.error(f"오류 응답: {response.text[:200]}...")
            return False
            
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        return False


def test_hcx_http():
    """HCX HTTP API 테스트"""
    logger.info("\n=== HCX HTTP 테스트 ===")
    
    api_key = os.getenv("CLOVA_STUDIO_API_KEY")
    if not api_key:
        logger.error("CLOVA_STUDIO_API_KEY가 설정되지 않았습니다.")
        return False
    
    api_url = "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-NCP-CLOVASTUDIO-API-KEY": api_key,
        "X-NCP-APIGW-API-KEY": api_key,
        "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    
    body = {
        "messages": [
            {"role": "user", "content": "Respond with simple JSON: {\"status\": \"ok\"}"}
        ],
        "maxTokens": 100,
        "temperature": 0.1,
    }
    
    try:
        logger.info("HCX API 호출 중...")
        response = requests.post(api_url, headers=headers, json=body, timeout=30)
        logger.info(f"응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "message" in data["result"]:
                content = data["result"]["message"]["content"]
                logger.info(f"✅ 응답 받음: {content[:100]}...")
                return True
        else:
            logger.error(f"오류 응답: {response.text[:200]}...")
            return False
            
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        return False


def test_ragas_format():
    """RAGAS 형식 테스트"""
    logger.info("\n=== RAGAS 형식 테스트 ===")
    
    # Faithfulness 프롬프트
    faithfulness_prompt = """Given an answer, break it down into simple statements.

Answer: 클린 아키텍처의 핵심 원칙은 의존성 규칙입니다.

Return the result as a JSON with a single key 'statements' containing an array of strings.

Example:
{"statements": ["statement 1", "statement 2"]}"""

    # Gemini 테스트
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        logger.info("\n--- Gemini RAGAS 테스트 ---")
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": faithfulness_prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    logger.info(f"Gemini 응답:\n{content}")
                    
                    # JSON 파싱 시도
                    try:
                        # 마크다운 제거
                        if "```json" in content or "```" in content:
                            import re
                            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                            if match:
                                content = match.group(1)
                        
                        parsed = json.loads(content)
                        logger.info(f"✅ JSON 파싱 성공: {parsed}")
                    except Exception as e:
                        logger.error(f"❌ JSON 파싱 실패: {e}")
        except Exception as e:
            logger.error(f"Gemini 오류: {e}")
    
    # HCX 테스트
    hcx_key = os.getenv("CLOVA_STUDIO_API_KEY")
    if hcx_key:
        logger.info("\n--- HCX RAGAS 테스트 ---")
        api_url = "https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005"
        
        headers = {
            "Authorization": f"Bearer {hcx_key}",
            "X-NCP-CLOVASTUDIO-API-KEY": hcx_key,
            "X-NCP-APIGW-API-KEY": hcx_key,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": str(uuid.uuid4()),
            "Content-Type": "application/json",
        }
        
        body = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": faithfulness_prompt
                }
            ],
            "maxTokens": 1024,
            "temperature": 0.1,
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=body, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "message" in data["result"]:
                    content = data["result"]["message"]["content"]
                    logger.info(f"HCX 응답:\n{content}")
                    
                    # JSON 파싱 시도
                    try:
                        # 여러 파싱 방법 시도
                        parsed = None
                        
                        # 마크다운 블록 제거
                        if "```json" in content or "```" in content:
                            import re
                            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                            if match:
                                parsed = json.loads(match.group(1))
                        
                        # JSON 객체 직접 추출
                        if not parsed:
                            start = content.find('{')
                            end = content.rfind('}')
                            if start != -1 and end != -1:
                                parsed = json.loads(content[start:end+1])
                        
                        # 전체 문자열 파싱
                        if not parsed:
                            parsed = json.loads(content)
                        
                        logger.info(f"✅ JSON 파싱 성공: {parsed}")
                    except Exception as e:
                        logger.error(f"❌ JSON 파싱 실패: {e}")
        except Exception as e:
            logger.error(f"HCX 오류: {e}")


if __name__ == "__main__":
    logger.info("API HTTP 테스트 시작")
    logger.info("=" * 50)
    
    # 기본 연결 테스트
    gemini_ok = test_gemini_http()
    hcx_ok = test_hcx_http()
    
    # RAGAS 형식 테스트
    if gemini_ok or hcx_ok:
        test_ragas_format()
    
    # 결과 요약
    logger.info("\n" + "=" * 50)
    logger.info("테스트 결과:")
    logger.info(f"Gemini: {'✅ 정상' if gemini_ok else '❌ 실패'}")
    logger.info(f"HCX: {'✅ 정상' if hcx_ok else '❌ 실패'}")