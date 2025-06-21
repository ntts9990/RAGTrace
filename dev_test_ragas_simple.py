#!/usr/bin/env python3
"""
RAGAS 문제 진단용 간단한 테스트
"""

import os
from datasets import Dataset
from langchain_google_genai import GoogleGenerativeAI
from ragas import evaluate
from ragas.metrics import faithfulness

# 환경 변수 확인
if not os.getenv("GEMINI_API_KEY"):
    print("❌ GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    exit(1)

# 간단한 테스트 데이터 (영어)
test_data = {
    "question": ["What is the capital of France?"],
    "contexts": [["Paris is the capital and largest city of France."]],
    "answer": ["The capital of France is Paris."],
    "ground_truth": ["Paris is the capital of France."]
}

print("🧪 RAGAS 간단 테스트 시작")
print("=" * 50)

try:
    # 데이터셋 생성
    dataset = Dataset.from_dict(test_data)
    print(f"✅ 테스트 데이터셋 생성 완료: {len(dataset)}개 항목")
    
    # LLM 설정
    llm = GoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.1
    )
    print(f"✅ LLM 설정 완료: {llm.model}")
    
    # 간단한 LLM 테스트
    test_response = llm.invoke("Hello, how are you?")
    print(f"✅ LLM 응답 테스트: {test_response[:50]}...")
    
    # Faithfulness만 테스트
    print("\n🔍 Faithfulness 메트릭만 테스트...")
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness],
        llm=llm,
        raise_exceptions=True  # 오류 발생시 바로 확인
    )
    
    print(f"✅ 평가 완료!")
    print(f"결과 타입: {type(result)}")
    
    if hasattr(result, "_scores_dict"):
        print(f"점수: {result._scores_dict}")
    else:
        print(f"결과 속성: {dir(result)}")
        
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()