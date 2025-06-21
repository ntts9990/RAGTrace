#!/usr/bin/env python3
"""기본 연결 테스트"""

import os
import time
import requests
from dotenv import load_dotenv
load_dotenv()

def test_direct_api():
    """직접 HTTP 요청 테스트"""
    print("=== 직접 API 호출 테스트 ===")
    
    api_key = os.getenv('GEMINI_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": "Hello"}]
        }]
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"응답 시간: {end_time - start_time:.2f}초")
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 직접 API 호출 성공")
            data = response.json()
            if 'candidates' in data:
                print(f"응답: {data['candidates'][0]['content']['parts'][0]['text']}")
        else:
            print(f"❌ API 오류: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 타임아웃 (30초)")
    except Exception as e:
        print(f"❌ 오류: {e}")

def test_langchain_simple():
    """LangChain 간단 테스트"""
    print("\n=== LangChain 간단 테스트 ===")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        api_key = os.getenv('GEMINI_API_KEY')
        
        # 기본 설정으로 테스트
        llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.5-flash-preview-05-20",
            google_api_key=api_key,
            temperature=0.1,
            timeout=30,
            request_timeout=30
        )
        
        print("LLM 객체 생성 완료")
        
        start_time = time.time()
        response = llm.invoke("Say hello")
        end_time = time.time()
        
        print(f"✅ LangChain 성공 - {end_time - start_time:.2f}초")
        print(f"응답: {response.content}")
        
    except Exception as e:
        print(f"❌ LangChain 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_api()
    test_langchain_simple()