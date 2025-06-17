#!/usr/bin/env python3
"""평가 디버깅을 위한 스크립트"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

from src.container import container

def test_evaluation():
    """평가 실행 테스트"""
    print("=== 평가 디버깅 시작 ===")
    
    # API 키 확인
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"API 키 존재: {bool(api_key)}")
    if api_key:
        print(f"API 키 (마스킹): {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # 평가 실행
        result = container.run_evaluation_use_case.execute(
            dataset_name="evaluation_data_variant1", 
            prompt_type=None
        )
        
        print("\n=== 평가 결과 ===")
        print(f"Faithfulness: {result.faithfulness}")
        print(f"Answer Relevancy: {result.answer_relevancy}")
        print(f"Context Recall: {result.context_recall}")
        print(f"Context Precision: {result.context_precision}")
        print(f"Generation Failures: {result.generation_failures}")
        print(f"Generation Successes: {result.generation_successes}")
        
        if result.generation_failures > 0:
            print(f"\n=== API 실패 상세 정보 ===")
            for detail in result.api_failure_details:
                print(f"Item {detail['item_index']}: {detail['error_type']} - {detail['error_message']}")
                
    except Exception as e:
        print(f"평가 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_evaluation()