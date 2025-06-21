#!/usr/bin/env python3
"""HCX API 연결 테스트 스크립트"""

import os
import time
from dotenv import load_dotenv
load_dotenv()

def test_hcx_api_direct():
    """HCX API 직접 테스트"""
    print("=== HCX API 직접 테스트 ===")
    
    import requests
    
    api_key = os.getenv('CLOVA_STUDIO_API_KEY')
    model_name = "HCX-005"
    
    if not api_key:
        print("❌ CLOVA_STUDIO_API_KEY가 설정되지 않았습니다.")
        return
        
    print(f"API 키: {api_key[:10]}...{api_key[-4:]}")
    print(f"모델: {model_name}")
    
    api_url = f"https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{model_name}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user", 
            "content": "안녕하세요! 간단한 테스트 질문입니다. 2+2는 얼마인가요?"
        }
    ]
    
    body = {
        "messages": messages,
        "maxTokens": 100,
        "temperature": 0.5,
        "topP": 0.8,
    }
    
    try:
        print("HCX API 요청 중...")
        start_time = time.time()
        
        response = requests.post(api_url, headers=headers, json=body, timeout=60)
        
        end_time = time.time()
        print(f"응답 시간: {end_time - start_time:.2f}초")
        print(f"HTTP 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ HCX API 성공!")
            print(f"응답: {result.get('result', {}).get('message', {}).get('content', 'No content')}")
        else:
            print(f"❌ HCX API 실패 - 상태 코드: {response.status_code}")
            print(f"응답 내용: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ HCX API 요청 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

def test_hcx_adapter():
    """HCX 어댑터 테스트"""
    print("\n=== HCX 어댑터 테스트 ===")
    
    try:
        from src.infrastructure.llm.hcx_adapter import HcxAdapter
        
        api_key = os.getenv('CLOVA_STUDIO_API_KEY')
        if not api_key:
            print("❌ CLOVA_STUDIO_API_KEY가 설정되지 않았습니다.")
            return
            
        adapter = HcxAdapter(api_key=api_key, model_name="HCX-005")
        
        print("HCX 어댑터 초기화 완료")
        
        # 답변 생성 테스트
        question = "원자력 발전소의 주요 안전 시스템은 무엇인가요?"
        contexts = ["원자력 발전소는 여러 안전 시스템을 갖추고 있습니다. 주요 시스템으로는 비상냉각시스템, 격납건물, 제어봉 시스템 등이 있습니다."]
        
        print(f"질문: {question}")
        print("답변 생성 중...")
        
        start_time = time.time()
        answer = adapter.generate_answer(question, contexts)
        end_time = time.time()
        
        print(f"✅ 답변 생성 성공 - {end_time - start_time:.2f}초")
        print(f"답변: {answer}")
        
        # LangChain 호환성 테스트
        print("\nLangChain 호환성 테스트...")
        llm = adapter.get_llm()
        
        prompt = "간단한 테스트입니다. 1+1은 얼마인가요?"
        
        start_time = time.time()
        result = llm._call(prompt)
        end_time = time.time()
        
        print(f"✅ LangChain 호환 테스트 성공 - {end_time - start_time:.2f}초")
        print(f"결과: {result}")
        
    except Exception as e:
        print(f"❌ HCX 어댑터 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

def test_hcx_with_ragas():
    """HCX를 RAGAS와 함께 테스트"""
    print("\n=== HCX + RAGAS 테스트 ===")
    
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness
        from src.infrastructure.llm.hcx_adapter import HcxAdapter
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        
        api_key = os.getenv('CLOVA_STUDIO_API_KEY')
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            print("❌ CLOVA_STUDIO_API_KEY가 설정되지 않았습니다.")
            return
            
        if not gemini_api_key:
            print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
            return
        
        # HCX LLM 설정
        hcx_adapter = HcxAdapter(api_key=api_key, model_name="HCX-005")
        llm = hcx_adapter.get_llm()
        
        # Gemini 임베딩 설정 (HCX 임베딩 대신 일단 Gemini 사용)
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-exp-03-07",
            google_api_key=gemini_api_key
        )
        
        # 최소 데이터셋
        data = {
            'question': ['원자력 발전소의 주요 안전 시스템은 무엇인가요?'],
            'answer': ['원자력 발전소의 주요 안전 시스템으로는 비상냉각시스템, 격납건물, 제어봉 시스템이 있습니다.'],
            'contexts': [['원자력 발전소는 여러 안전 시스템을 갖추고 있습니다. 주요 시스템으로는 비상냉각시스템, 격납건물, 제어봉 시스템 등이 있습니다.']],
            'ground_truth': ['비상냉각시스템, 격납건물, 제어봉 시스템']
        }
        dataset = Dataset.from_dict(data)
        
        print("HCX LLM + Gemini 임베딩으로 RAGAS 평가 시작...")
        start_time = time.time()
        
        result = evaluate(
            dataset=dataset,
            metrics=[faithfulness],
            llm=llm,
            embeddings=embeddings,
            raise_exceptions=True
        )
        
        end_time = time.time()
        
        print(f"✅ RAGAS 평가 성공 - {end_time - start_time:.2f}초")
        print(f"결과: {result}")
        
    except Exception as e:
        print(f"❌ HCX + RAGAS 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hcx_api_direct()
    test_hcx_adapter()
    test_hcx_with_ragas()