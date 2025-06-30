#!/usr/bin/env python3
"""
기본 API 연결 테스트
"""

import os
import json
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import uuid

# 환경 변수 로드
load_dotenv()

def test_gemini_basic():
    """Gemini 기본 연결 테스트"""
    print("\n=== GEMINI 기본 테스트 ===")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        return False
    
    print(f"✅ API 키 확인: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        genai.configure(api_key=api_key)
        
        # 설정 추가
        generation_config = genai.GenerationConfig(
            max_output_tokens=100,
            temperature=0.1,
        )
        
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash-preview-05-20',
            generation_config=generation_config
        )
        
        print("✅ 모델 생성 성공")
        
        # 간단한 테스트
        response = model.generate_content("Hello, respond with JSON: {\"status\": \"ok\"}")
        print(f"✅ 응답 받음: {response.text[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False


def test_hcx_basic():
    """HCX 기본 연결 테스트"""
    print("\n=== HCX 기본 테스트 ===")
    
    api_key = os.getenv("CLOVA_STUDIO_API_KEY")
    if not api_key:
        print("❌ CLOVA_STUDIO_API_KEY가 설정되지 않았습니다.")
        return False
    
    print(f"✅ API 키 확인: {api_key[:10]}...{api_key[-5:]}")
    
    try:
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
                {"role": "user", "content": "Hello, respond with JSON: {\"status\": \"ok\"}"}
            ],
            "maxTokens": 100,
            "temperature": 0.1,
        }
        
        response = requests.post(api_url, headers=headers, json=body, timeout=10)
        print(f"✅ 응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "message" in data["result"]:
                content = data["result"]["message"]["content"]
                print(f"✅ 응답 받음: {content[:100]}...")
                return True
        else:
            print(f"❌ 오류 응답: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False


if __name__ == "__main__":
    print("기본 API 연결 테스트")
    print("=" * 50)
    
    # Gemini 테스트
    gemini_ok = test_gemini_basic()
    
    # HCX 테스트
    hcx_ok = test_hcx_basic()
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과:")
    print(f"Gemini: {'✅ 정상' if gemini_ok else '❌ 실패'}")
    print(f"HCX: {'✅ 정상' if hcx_ok else '❌ 실패'}")