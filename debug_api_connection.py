#!/usr/bin/env python3
"""API 연결 상세 디버깅 스크립트"""

import os
import time
import asyncio
from dotenv import load_dotenv
load_dotenv()

def test_basic_api():
    """1. 기본 API 연결 테스트"""
    print("=== 1. 기본 API 연결 테스트 ===")
    
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL_NAME', 'models/gemini-2.5-flash-preview-05-20')
    embedding_model = os.getenv('GEMINI_EMBEDDING_MODEL_NAME', 'models/gemini-embedding-exp-03-07')
    
    print(f"API 키: {api_key[:10]}...{api_key[-4:]}")
    print(f"LLM 모델: {model_name}")
    print(f"임베딩 모델: {embedding_model}")
    
    # LLM 테스트
    print("\n--- LLM 테스트 ---")
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1
        )
        
        start_time = time.time()
        response = llm.invoke("Hello, how are you?")
        end_time = time.time()
        
        print(f"✅ LLM 성공 - 응답 시간: {end_time - start_time:.2f}초")
        print(f"응답: {response.content[:100]}...")
        
    except Exception as e:
        print(f"❌ LLM 실패: {e}")
    
    # 임베딩 테스트
    print("\n--- 임베딩 테스트 ---")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=api_key
        )
        
        start_time = time.time()
        result = embeddings.embed_query("test query")
        end_time = time.time()
        
        print(f"✅ 임베딩 성공 - 응답 시간: {end_time - start_time:.2f}초")
        print(f"임베딩 차원: {len(result)}")
        
    except Exception as e:
        print(f"❌ 임베딩 실패: {e}")

def test_concurrent_requests():
    """2. 동시 요청 테스트"""
    print("\n=== 2. 동시 요청 테스트 ===")
    
    import threading
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL_NAME', 'models/gemini-2.5-flash-preview-05-20')
    
    results = []
    errors = []
    
    def make_request(i):
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.1
            )
            
            start_time = time.time()
            response = llm.invoke(f"Request {i}: What is 2+2?")
            end_time = time.time()
            
            results.append({
                'id': i,
                'time': end_time - start_time,
                'content': response.content[:50]
            })
            print(f"✅ 요청 {i} 성공 - {end_time - start_time:.2f}초")
            
        except Exception as e:
            errors.append({'id': i, 'error': str(e)})
            print(f"❌ 요청 {i} 실패: {e}")
    
    # 3개 동시 요청
    threads = []
    start_time = time.time()
    
    for i in range(3):
        thread = threading.Thread(target=make_request, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    print(f"\n총 시간: {end_time - start_time:.2f}초")
    print(f"성공: {len(results)}, 실패: {len(errors)}")

def test_ragas_minimal():
    """3. 최소 RAGAS 테스트"""
    print("\n=== 3. 최소 RAGAS 테스트 ===")
    
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        
        api_key = os.getenv('GEMINI_API_KEY')
        model_name = os.getenv('GEMINI_MODEL_NAME', 'models/gemini-2.5-flash-preview-05-20')
        embedding_model = os.getenv('GEMINI_EMBEDDING_MODEL_NAME', 'models/gemini-embedding-exp-03-07')
        
        # 최소 데이터셋
        data = {
            'question': ['What is 2+2?'],
            'answer': ['2+2 equals 4'],
            'contexts': [['Basic arithmetic: 2+2=4']],
            'ground_truth': ['4']
        }
        dataset = Dataset.from_dict(data)
        
        # LLM과 임베딩 설정
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1
        )
        
        embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=api_key
        )
        
        print("LLM과 임베딩 모델 초기화 완료")
        
        # 단일 메트릭으로 평가
        print("RAGAS 평가 시작...")
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
        print(f"❌ RAGAS 평가 실패: {e}")
        import traceback
        traceback.print_exc()

def test_async_behavior():
    """4. Async 동작 테스트"""
    print("\n=== 4. Async 동작 테스트 ===")
    
    import asyncio
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL_NAME', 'models/gemini-2.5-flash-preview-05-20')
    
    async def async_request(i):
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.1
            )
            
            start_time = time.time()
            response = await llm.ainvoke(f"Async request {i}: What is the capital of France?")
            end_time = time.time()
            
            print(f"✅ Async 요청 {i} 성공 - {end_time - start_time:.2f}초")
            return {'id': i, 'time': end_time - start_time, 'success': True}
            
        except Exception as e:
            print(f"❌ Async 요청 {i} 실패: {e}")
            return {'id': i, 'error': str(e), 'success': False}
    
    async def run_async_tests():
        tasks = [async_request(i) for i in range(3)]
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        print(f"\nAsync 총 시간: {end_time - start_time:.2f}초")
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        print(f"성공: {success_count}, 실패: {len(results) - success_count}")
    
    try:
        asyncio.run(run_async_tests())
    except Exception as e:
        print(f"Async 테스트 실패: {e}")

def test_rate_limiting():
    """5. Rate Limiting 테스트"""
    print("\n=== 5. Rate Limiting 테스트 ===")
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL_NAME', 'models/gemini-2.5-flash-preview-05-20')
    
    # 빠른 연속 요청
    print("빠른 연속 요청 테스트...")
    
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.1
    )
    
    for i in range(5):
        try:
            start_time = time.time()
            response = llm.invoke(f"Quick request {i}: What is {i}+1?")
            end_time = time.time()
            print(f"✅ 요청 {i} - {end_time - start_time:.2f}초")
            
        except Exception as e:
            print(f"❌ 요청 {i} 실패: {e}")
        
        # 짧은 대기
        time.sleep(0.5)

if __name__ == "__main__":
    test_basic_api()
    test_concurrent_requests()
    test_ragas_minimal()
    test_async_behavior()
    test_rate_limiting()