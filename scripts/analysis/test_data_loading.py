#!/usr/bin/env python3
"""테스트 스크립트: 데이터 로딩 기능 검증 (개선된 버전)"""

import sys
import json
from pathlib import Path

# 프로젝트 루트를 찾아 sys.path에 추가
def find_and_add_project_root():
    """프로젝트 루트를 찾아 sys.path에 추가"""
    current_path = Path(__file__).resolve()
    while current_path != current_path.parent:
        if (current_path / 'pyproject.toml').exists():
            sys.path.insert(0, str(current_path))
            return current_path
        current_path = current_path.parent
    raise FileNotFoundError("프로젝트 루트를 찾을 수 없습니다.")

# 프로젝트 루트 추가
project_root = find_and_add_project_root()

# 이제 중앙 경로 관리 모듈을 사용할 수 있음
from src.utils.paths import get_evaluation_data_path, get_available_datasets, PROJECT_ROOT
from src.presentation.web.components.detailed_analysis import load_actual_qa_data_from_dataset


def test_data_loading():
    """데이터 로딩 기능 테스트"""
    print("데이터 로딩 기능 테스트 시작...")
    print("=" * 60)
    
    print(f"프로젝트 루트: {PROJECT_ROOT}")
    print(f"사용 가능한 데이터셋: {get_available_datasets()}")
    print()

    # Test 1: 기본 evaluation_data.json 테스트
    print("[TEST 1] evaluation_data.json 로딩 테스트 (3개 항목)")
    result = load_actual_qa_data_from_dataset("evaluation_data.json", 3)
    if result:
        print(f"✅ 성공: {len(result)}개 항목 로드")
        print(f"   첫 번째 질문: {result[0].get('question', 'N/A')[:50]}...")
    else:
        print("❌ 실패: 데이터를 로드할 수 없음")
    print()

    # Test 2: variant1 데이터 테스트  
    print("[TEST 2] evaluation_data_variant1.json 로딩 테스트 (2개 항목)")
    result = load_actual_qa_data_from_dataset("evaluation_data_variant1.json", 2)
    if result:
        print(f"✅ 성공: {len(result)}개 항목 로드")
        print(f"   첫 번째 질문: {result[0].get('question', 'N/A')[:50]}...")
    else:
        print("❌ 실패: 데이터를 로드할 수 없음")
    print()

    # Test 3: variant 키워드 테스트
    print("[TEST 3] variant 키워드를 포함한 데이터셋명 테스트")
    result = load_actual_qa_data_from_dataset("some_variant1_data", 1)
    if result:
        print(f"✅ 성공: variant1 자동 인식으로 {len(result)}개 항목 로드")
    else:
        print("❌ 실패: variant1 자동 인식 실패")
    print()

    # Test 4: 존재하지 않는 파일 테스트
    print("[TEST 4] 존재하지 않는 파일 테스트")
    result = load_actual_qa_data_from_dataset("non_existent.json", 5)
    if result is None:
        print("✅ 성공: 존재하지 않는 파일에 대해 올바르게 None 반환")
    else:
        print("❌ 실패: None을 반환해야 함")
    print()

    # Test 5: 경로 유틸리티 함수 테스트
    print("[TEST 5] 경로 유틸리티 함수 테스트")
    for dataset_name in ["evaluation_data.json", "evaluation_data_variant1.json", "invalid.json"]:
        path = get_evaluation_data_path(dataset_name)
        if path:
            print(f"✅ {dataset_name}: {path} (존재함)")
        else:
            print(f"❌ {dataset_name}: 파일 없음")
    print()

    # Test 6: 직접 파일 검증
    print("[TEST 6] 직접 파일 시스템 검증")
    data_file = get_evaluation_data_path("evaluation_data.json")
    if data_file:
        print(f"파일 경로: {data_file}")
        print(f"파일 존재: {data_file.exists()}")
        print(f"파일 크기: {data_file.stat().st_size if data_file.exists() else 'N/A'} bytes")
        
        if data_file.exists():
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ 직접 로드 성공: {len(data)}개 항목")
            except Exception as e:
                print(f"❌ 직접 로드 실패: {e}")
    else:
        print("❌ 기본 데이터 파일을 찾을 수 없음")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")


def main():
    """메인 함수"""
    try:
        test_data_loading()
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()