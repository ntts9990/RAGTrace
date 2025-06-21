#!/usr/bin/env python3
"""HCX API 직접 테스트"""

import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()

def test_hcx_direct_api():
    """HCX API 직접 호출 테스트"""
    print("=== HCX API 직접 호출 테스트 ===")
    
    api_key = os.getenv('CLOVA_STUDIO_API_KEY')
    model_name = os.getenv('HCX_MODEL_NAME', 'HCX-005')
    
    if not api_key:
        print("❌ CLOVA_STUDIO_API_KEY가 설정되지 않았습니다.")
        return
    
    print(f"API 키: {api_key[:10]}...{api_key[-4:]}")
    print(f"모델명: {model_name}")
    
    # API URL 구성
    api_url = f"https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/{model_name}"
    print(f"API URL: {api_url}")
    
    # 요청 헤더
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # 요청 본문
    body = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. Respond in Korean."
            },
            {
                "role": "user",
                "content": "안녕하세요. 간단한 테스트입니다."
            }
        ],
        "maxTokens": 100,
        "temperature": 0.5,
        "topP": 0.8,
    }
    
    print(f"요청 본문: {json.dumps(body, ensure_ascii=False, indent=2)}")
    print("\n--- API 호출 중... ---")
    
    try:
        response = requests.post(api_url, headers=headers, json=body, timeout=30)
        
        print(f"상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ HCX API 호출 성공!")
            result = response.json()
            print(f"응답 JSON: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 응답 구조 분석
            try:
                message_content = result["result"]["message"]["content"]
                print(f"\n🤖 HCX 응답: {message_content}")
            except KeyError as e:
                print(f"❌ 예상과 다른 응답 구조: {e}")
                print(f"전체 응답: {result}")
                
        else:
            print(f"❌ HCX API 오류 - 상태 코드: {response.status_code}")
            print(f"오류 내용: {response.text}")
            
            # 특정 오류 분석
            if response.status_code == 401:
                print("🔑 인증 오류 - API 키를 확인하세요")
            elif response.status_code == 404:
                print("🔍 모델을 찾을 수 없음 - 모델명을 확인하세요")
            elif response.status_code == 429:
                print("⏰ 요청 한도 초과 - 잠시 후 다시 시도하세요")
            
    except requests.exceptions.Timeout:
        print("❌ 타임아웃 (30초)")
    except requests.exceptions.ConnectionError:
        print("❌ 연결 오류 - 네트워크를 확인하세요")
    except Exception as e:
        print(f"❌ 예기치 않은 오류: {e}")

def test_hcx_adapter():
    """HCX 어댑터 클래스 테스트"""
    print("\n=== HCX 어댑터 클래스 테스트 ===")
    
    try:
        from src.infrastructure.llm.hcx_adapter import HcxAdapter
        
        api_key = os.getenv('CLOVA_STUDIO_API_KEY')
        model_name = os.getenv('HCX_MODEL_NAME', 'HCX-005')
        
        # HcxAdapter 인스턴스 생성
        adapter = HcxAdapter(api_key=api_key, model_name=model_name)
        print("✅ HcxAdapter 인스턴스 생성 성공")
        
        # 질문과 컨텍스트로 답변 생성 테스트
        question = "원자력 발전소의 주요 안전 시스템은 무엇인가요?"
        contexts = [
            "원자력 발전소는 여러 안전 시스템을 갖추고 있습니다.",
            "비상 냉각 시스템(ECCS)은 중요한 안전 장치입니다.",
            "격납 건물은 방사성 물질의 외부 유출을 방지합니다."
        ]
        
        print(f"질문: {question}")
        print(f"컨텍스트: {contexts}")
        print("\n--- 답변 생성 중... ---")
        
        answer = adapter.generate_answer(question, contexts)
        print(f"✅ 답변 생성 성공!")
        print(f"🤖 HCX 답변: {answer}")
        
        # LangChain 호환 객체 테스트
        print("\n--- LangChain 호환 테스트 ---")
        llm = adapter.get_llm()
        response = llm.invoke("간단한 인사를 해주세요.")
        print(f"✅ LangChain 호환 테스트 성공!")
        print(f"응답: {response}")
        
    except Exception as e:
        print(f"❌ HCX 어댑터 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

def test_hcx_embedding():
    """HCX 임베딩 테스트"""
    print("\n=== HCX 임베딩 테스트 ===")
    
    try:
        from src.infrastructure.embedding.hcx_adapter import HcxEmbeddingAdapter
        
        api_key = os.getenv('CLOVA_STUDIO_API_KEY')
        
        # HcxEmbeddingAdapter 인스턴스 생성
        embedding_adapter = HcxEmbeddingAdapter(api_key=api_key)
        print("✅ HcxEmbeddingAdapter 인스턴스 생성 성공")
        
        # 단일 텍스트 임베딩 테스트
        test_text = "원자력 발전소 안전 시스템"
        print(f"테스트 텍스트: {test_text}")
        
        embedding = embedding_adapter.embed_query(test_text)
        print(f"✅ 임베딩 생성 성공!")
        print(f"임베딩 차원: {len(embedding)}")
        print(f"임베딩 샘플 (처음 5개): {embedding[:5]}")
        
        # 여러 문서 임베딩 테스트
        test_documents = [
            "원자력 발전소 안전 시스템",
            "수력 발전소 운영 방식",
            "재생 에너지 기술 동향"
        ]
        
        embeddings = embedding_adapter.embed_documents(test_documents)
        print(f"✅ 문서 임베딩 생성 성공!")
        print(f"문서 수: {len(embeddings)}")
        print(f"각 임베딩 차원: {[len(emb) for emb in embeddings]}")
        
    except Exception as e:
        print(f"❌ HCX 임베딩 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hcx_direct_api()
    test_hcx_adapter()
    test_hcx_embedding()