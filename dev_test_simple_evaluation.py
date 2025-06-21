#!/usr/bin/env python3
"""간단한 평가 테스트"""

import os
from dotenv import load_dotenv
from datasets import Dataset

load_dotenv()

def test_simple_evaluation():
    """간단한 1개 데이터로 평가 테스트"""
    try:
        from src.container import get_evaluation_use_case_with_llm
        from src.domain.prompts import PromptType
        
        # 매우 간단한 테스트 데이터 (1개만)
        test_data = {
            'question': ['What is 2+2?'],
            'answer': ['2+2 equals 4'],
            'contexts': [['Basic arithmetic: 2+2=4']],
            'ground_truth': ['4']
        }
        
        print("=== 간단한 평가 테스트 (1개 데이터) ===")
        
        # 기본 프롬프트 테스트
        print("1. 기본 프롬프트 테스트...")
        try:
            use_case, _, _ = get_evaluation_use_case_with_llm("gemini", "gemini", PromptType.DEFAULT)
            print("   ✅ 설정 성공")
            
            # 간단한 평가 실행 (웹 UI 방식과 동일)
            dataset = Dataset.from_dict(test_data)
            from src.infrastructure.evaluation.ragas_adapter import RagasEvalAdapter
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            from src.infrastructure.llm.gemini_adapter import GeminiAdapter
            
            api_key = os.getenv('GEMINI_API_KEY')
            llm_adapter = GeminiAdapter(api_key, "models/gemini-2.5-flash-preview-05-20")
            embedding_adapter = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-exp-03-07",
                google_api_key=api_key
            )
            
            adapter = RagasEvalAdapter(llm_adapter, embedding_adapter, PromptType.DEFAULT)
            result = adapter.evaluate(dataset)
            
            print(f"   ✅ 평가 완료: RAGAS Score = {result.get('ragas_score', 0):.3f}")
            
        except Exception as e:
            print(f"   ❌ 기본 프롬프트 테스트 실패: {e}")
        
        # 원자력 프롬프트 테스트
        print("\n2. 원자력/수력 기술 프롬프트 테스트...")
        try:
            korean_data = {
                'question': ['원자력 발전소의 주요 안전 시스템은?'],
                'answer': ['비상냉각시스템, 격납건물, 제어봉 시스템입니다.'],
                'contexts': [['원자력 발전소는 여러 안전 시스템을 갖추고 있습니다.']],
                'ground_truth': ['비상냉각시스템, 격납건물, 제어봉 시스템']
            }
            
            dataset = Dataset.from_dict(korean_data)
            adapter = RagasEvalAdapter(llm_adapter, embedding_adapter, PromptType.NUCLEAR_HYDRO_TECH)
            result = adapter.evaluate(dataset)
            
            print(f"   ✅ 평가 완료: RAGAS Score = {result.get('ragas_score', 0):.3f}")
            
        except Exception as e:
            print(f"   ❌ 원자력 프롬프트 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_evaluation()