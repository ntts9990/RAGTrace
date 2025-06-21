#!/usr/bin/env python3
"""최소한의 RAGAS 테스트"""

import os
from dotenv import load_dotenv
from datasets import Dataset

load_dotenv()

def test_minimal_ragas():
    """최소한의 RAGAS 평가 테스트"""
    try:
        # 매우 간단한 데이터
        data = {
            'question': ['What is 2+2?'],
            'answer': ['4'],
            'contexts': [['2+2=4']],
            'ground_truth': ['4']
        }
        dataset = Dataset.from_dict(data)
        
        # 기본 메트릭만 사용
        from ragas.metrics import faithfulness
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        from ragas import evaluate
        
        api_key = os.getenv('GEMINI_API_KEY')
        
        print("=== 최소 RAGAS 테스트 ===")
        print("1. LLM 초기화...")
        llm = ChatGoogleGenerativeAI(
            model='models/gemini-2.5-flash-preview-05-20',
            google_api_key=api_key,
            temperature=0.1,
            max_retries=1,
            request_timeout=30
        )
        
        print("2. 임베딩 초기화...")
        embeddings = GoogleGenerativeAIEmbeddings(
            model='models/gemini-embedding-exp-03-07',
            google_api_key=api_key
        )
        
        print("3. 단일 메트릭 평가...")
        import threading
        import time
        
        result = [None]
        exception = [None]
        
        def run_eval():
            try:
                result[0] = evaluate(
                    dataset=dataset,
                    metrics=[faithfulness],  # 단일 메트릭만
                    llm=llm,
                    embeddings=embeddings,
                    raise_exceptions=True
                )
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=run_eval)
        thread.daemon = True
        thread.start()
        thread.join(timeout=60)  # 1분 타임아웃
        
        if thread.is_alive():
            print("❌ 1분 타임아웃")
            return False
            
        if exception[0]:
            print(f"❌ 평가 오류: {exception[0]}")
            return False
            
        if result[0]:
            print("✅ 평가 성공!")
            print(f"결과: {result[0]}")
            return True
        else:
            print("❌ 결과 없음")
            return False
            
    except Exception as e:
        print(f"❌ 설정 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_minimal_ragas()
    if success:
        print("\n✅ RAGAS가 정상 작동합니다.")
    else:
        print("\n❌ RAGAS에 문제가 있습니다.")
        print("\n해결책:")
        print("1. 인터넷 연결 확인")
        print("2. GEMINI_API_KEY 확인")
        print("3. Google AI API 할당량 확인")
        print("4. 방화벽/프록시 설정 확인")