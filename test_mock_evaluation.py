#!/usr/bin/env python3
"""Mock 평가 테스트"""

import os
from dotenv import load_dotenv
load_dotenv()

from src.container import container

def test_mock_evaluation():
    """Mock 평가 실행 테스트"""
    print("=== Mock 평가 테스트 ===")
    
    # 기존 데이터로 평가 시도 (답변 생성 없이)
    try:
        # 데이터셋 로드만 확인
        repository = container.repository_factory.create_repository("evaluation_data_variant1")
        data_list = repository.load_data()
        
        print(f"데이터 개수: {len(data_list)}")
        for i, data in enumerate(data_list):
            print(f"Item {i+1}:")
            print(f"  Question: {data.question[:50]}...")
            print(f"  Answer exists: {bool(data.answer)}")
            print(f"  Answer length: {len(data.answer) if data.answer else 0}")
        
        # 데이터 검증 서비스 테스트
        validator = container.run_evaluation_use_case.data_validator
        validation_report = validator.validate_data_list(data_list)
        
        print(f"\n검증 결과:")
        print(f"  Errors: {validation_report.has_errors}")
        print(f"  Warnings: {validation_report.has_warnings}")
        
        return True
        
    except Exception as e:
        print(f"Mock 평가 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_mock_evaluation()