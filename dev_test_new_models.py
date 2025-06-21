#!/usr/bin/env python3
"""새로운 모델로 API 테스트"""

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

def test_new_models():
    """새로운 모델로 API 테스트"""
    print("=== 새로운 모델 테스트 ===")
    
    api_key = os.getenv('GEMINI_API_KEY')
    gemini_model = os.getenv('GEMINI_MODEL_NAME', 'models/gemini-2.5-flash-preview-05-20')
    embedding_model = os.getenv('GEMINI_EMBEDDING_MODEL_NAME', 'models/gemini-embedding-exp-03-07')
    
    print(f"API 키: {api_key[:10]}...{api_key[-4:]}")
    print(f"LLM 모델: {gemini_model}")
    print(f"임베딩 모델: {embedding_model}")
    
    # 1. LLM 테스트
    print("\n1. LLM 테스트:")
    try:
        llm = ChatGoogleGenerativeAI(
            model=gemini_model,
            google_api_key=api_key,
            temperature=0.1
        )
        
        response = llm.invoke("안녕하세요. 간단히 인사해주세요.")
        print(f"✅ LLM 응답: {response.content}")
        
    except Exception as e:
        print(f"❌ LLM 테스트 실패: {e}")
    
    # 2. 임베딩 테스트
    print("\n2. 임베딩 테스트:")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=api_key,
        )
        
        result = embeddings.embed_query("테스트 문장입니다.")
        print(f"✅ 임베딩 성공 (차원: {len(result)})")
        
    except Exception as e:
        print(f"❌ 임베딩 테스트 실패: {e}")

if __name__ == "__main__":
    test_new_models()