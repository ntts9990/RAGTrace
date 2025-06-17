#!/usr/bin/env python3
"""API 연결 테스트"""

import os
from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.llm.gemini_adapter import GeminiAdapter

def test_api():
    """API 연결 테스트"""
    print("=== API 연결 테스트 ===")
    
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"API 키: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # Gemini 어댑터 생성
        adapter = GeminiAdapter(
            api_key=api_key,
            model_name="gemini-1.5-flash-latest",
            requests_per_minute=60
        )
        
        # 간단한 답변 생성 테스트
        print("\n답변 생성 테스트:")
        answer = adapter.generate_answer(
            question="안녕하세요",
            contexts=["인사말에 대한 예의 바른 응답을 해야 합니다."]
        )
        print(f"생성된 답변: {answer}")
        
        # LLM 객체 테스트
        print("\nLLM 객체 테스트:")
        llm = adapter.get_llm()
        print(f"LLM 타입: {type(llm)}")
        
        return True
        
    except Exception as e:
        print(f"API 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_api()