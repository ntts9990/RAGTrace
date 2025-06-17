#!/usr/bin/env python3
"""간단한 API 테스트"""

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

def test_simple_api():
    """간단한 API 연결 테스트"""
    print("=== 간단한 API 테스트 ===")
    
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"API 키: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # 표준 Gemini LLM 생성 (rate limiting 없이)
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=api_key,
            temperature=0.1
        )
        
        # 간단한 질문
        response = llm.invoke("안녕하세요. 간단히 인사해주세요.")
        print(f"응답: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"API 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_api()