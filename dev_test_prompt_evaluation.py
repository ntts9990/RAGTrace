#!/usr/bin/env python3
"""프롬프트 설정 테스트 스크립트"""

import os
from dotenv import load_dotenv
from datasets import Dataset

load_dotenv()

def test_prompt_evaluation():
    """프롬프트별 평가 테스트"""
    try:
        from src.container import get_evaluation_use_case_with_llm
        from src.domain.prompts import PromptType
        
        # 간단한 테스트 데이터
        test_data = {
            'question': ['원자력 발전소의 주요 안전 시스템은?'],
            'answer': ['원자력 발전소의 주요 안전 시스템으로는 비상냉각시스템, 격납건물, 제어봉 시스템이 있습니다.'],
            'contexts': [['원자력 발전소는 여러 안전 시스템을 갖추고 있습니다. 주요 시스템으로는 비상냉각시스템, 격납건물, 제어봉 시스템 등이 있습니다.']],
            'ground_truth': ['비상냉각시스템, 격납건물, 제어봉 시스템']
        }
        
        # 기본 프롬프트 테스트
        print("=== 기본 프롬프트 테스트 ===")
        try:
            use_case, _, _ = get_evaluation_use_case_with_llm("gemini", "gemini", PromptType.DEFAULT)
            print("✅ 기본 프롬프트 설정 성공")
        except Exception as e:
            print(f"❌ 기본 프롬프트 설정 실패: {e}")
        
        # 원자력 프롬프트 테스트
        print("\n=== 원자력/수력 기술 프롬프트 테스트 ===")
        try:
            use_case, _, _ = get_evaluation_use_case_with_llm("gemini", "gemini", PromptType.NUCLEAR_HYDRO_TECH)
            print("✅ 원자력/수력 기술 프롬프트 설정 성공")
        except Exception as e:
            print(f"❌ 원자력/수력 기술 프롬프트 설정 실패: {e}")
        
        # 한국어 공식 프롬프트 테스트  
        print("\n=== 한국어 공식 문서 프롬프트 테스트 ===")
        try:
            use_case, _, _ = get_evaluation_use_case_with_llm("gemini", "gemini", PromptType.KOREAN_FORMAL)
            print("✅ 한국어 공식 문서 프롬프트 설정 성공")
        except Exception as e:
            print(f"❌ 한국어 공식 문서 프롬프트 설정 실패: {e}")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_prompt_evaluation()