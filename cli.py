#!/usr/bin/env python3
"""
RAGTrace CLI 인터페이스

RAGAS 평가를 명령줄에서 실행할 수 있는 CLI 도구
프롬프트 타입 선택 기능 포함
"""

import argparse
import sys
from typing import Optional

from src.config import settings, PROMPT_TYPE_HELP, set_prompt_type_for_session
from src.container import create_container_with_prompts, container
from src.domain.prompts import PromptType
from src.utils.paths import get_available_datasets


def create_parser() -> argparse.ArgumentParser:
    """CLI 파서 생성"""
    parser = argparse.ArgumentParser(
        description="RAGTrace - RAG 시스템 성능 평가 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 프롬프트로 평가 실행
  python cli.py evaluate evaluation_data

  # 한국어 기술 문서 프롬프트로 평가
  python cli.py evaluate evaluation_data --prompt-type korean_tech
  
  # 사용 가능한 데이터셋 목록 보기
  python cli.py list-datasets
  
  # 프롬프트 타입 정보 보기
  python cli.py list-prompts
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 명령어")
    
    # evaluate 서브커맨드
    eval_parser = subparsers.add_parser("evaluate", help="RAG 시스템 평가 실행")
    eval_parser.add_argument(
        "dataset",
        help="평가할 데이터셋 이름 (확장자 제외)"
    )
    eval_parser.add_argument(
        "--prompt-type", 
        choices=[pt.value for pt in PromptType],
        default=None,
        help="사용할 프롬프트 타입"
    )
    eval_parser.add_argument(
        "--output",
        help="결과를 저장할 파일 경로 (선택사항)"
    )
    eval_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세한 로그 출력"
    )
    
    # list-datasets 서브커맨드
    list_parser = subparsers.add_parser("list-datasets", help="사용 가능한 데이터셋 목록 보기")
    
    # list-prompts 서브커맨드
    prompts_parser = subparsers.add_parser("list-prompts", help="사용 가능한 프롬프트 타입 보기")
    
    return parser


def list_datasets():
    """사용 가능한 데이터셋 목록 출력"""
    print("📊 사용 가능한 데이터셋:")
    print("-" * 40)
    
    datasets = get_available_datasets()
    if not datasets:
        print("❌ 사용 가능한 데이터셋이 없습니다.")
        print("   data/ 디렉토리에 JSON 형식의 평가 데이터를 추가하세요.")
        return
    
    for i, dataset in enumerate(datasets, 1):
        print(f"{i}. {dataset}")
    
    print(f"\n총 {len(datasets)}개의 데이터셋이 있습니다.")


def list_prompts():
    """사용 가능한 프롬프트 타입 목록 출력"""
    print("🎯 사용 가능한 프롬프트 타입:")
    print("-" * 50)
    
    for prompt_type in PromptType:
        description = PROMPT_TYPE_HELP.get(prompt_type, "설명 없음")
        status = "✅ 기본값" if prompt_type == PromptType.DEFAULT else "🔧 커스텀"
        print(f"{status} {prompt_type.value:20} : {description}")
    
    print(f"\n현재 기본 설정: {settings.get_prompt_type().value}")
    
    if settings.is_custom_prompt_enabled():
        print("💡 커스텀 프롬프트가 기본값으로 설정되어 있습니다.")
    else:
        print("💡 --prompt-type 옵션으로 다른 프롬프트를 선택할 수 있습니다.")


def evaluate_dataset(dataset_name: str, prompt_type: Optional[str] = None, 
                    output_file: Optional[str] = None, verbose: bool = False):
    """데이터셋 평가 실행"""
    
    # 프롬프트 타입 설정
    if prompt_type:
        try:
            selected_prompt_type = PromptType(prompt_type)
            set_prompt_type_for_session(selected_prompt_type)
        except ValueError:
            print(f"❌ 잘못된 프롬프트 타입: {prompt_type}")
            print(f"   사용 가능한 타입: {[pt.value for pt in PromptType]}")
            return False
    else:
        selected_prompt_type = settings.get_prompt_type()
    
    print(f"🎯 프롬프트 타입: {selected_prompt_type.value}")
    print(f"📊 데이터셋: {dataset_name}")
    
    # 데이터셋 확인
    available_datasets = get_available_datasets()
    if dataset_name not in available_datasets:
        print(f"❌ 데이터셋 '{dataset_name}'을 찾을 수 없습니다.")
        print("사용 가능한 데이터셋:")
        for ds in available_datasets:
            print(f"  - {ds}")
        return False
    
    try:
        # 컨테이너 생성
        if selected_prompt_type == PromptType.DEFAULT:
            eval_container = container
        else:
            eval_container = create_container_with_prompts(selected_prompt_type)
        
        # 평가 실행
        print("\n🚀 평가를 시작합니다...")
        evaluation_use_case = eval_container.get_run_evaluation_use_case(dataset_name)
        
        if verbose:
            print("📝 상세 로그가 활성화되었습니다.")
        
        result = evaluation_use_case.execute()
        
        # 결과 출력
        print("\n✅ 평가가 완료되었습니다!")
        print("=" * 50)
        print("📊 평가 결과:")
        print("-" * 30)
        
        result_dict = result.to_dict()
        
        # 메인 메트릭 출력
        print(f"🏆 종합 점수 (RAGAS Score): {result_dict.get('ragas_score', 0):.3f}")
        print(f"✅ Faithfulness:           {result_dict.get('faithfulness', 0):.3f}")
        print(f"🎯 Answer Relevancy:        {result_dict.get('answer_relevancy', 0):.3f}")
        print(f"🔄 Context Recall:          {result_dict.get('context_recall', 0):.3f}")
        print(f"📍 Context Precision:       {result_dict.get('context_precision', 0):.3f}")
        
        # 메타데이터 출력
        if verbose and 'metadata' in result_dict:
            metadata = result_dict['metadata']
            print("\n📋 평가 정보:")
            print(f"  평가 ID: {metadata.get('evaluation_id', 'N/A')}")
            print(f"  모델: {metadata.get('model', 'N/A')}")
            print(f"  데이터셋 크기: {metadata.get('dataset_size', 'N/A')}")
            print(f"  평가 시간: {metadata.get('timestamp', 'N/A')}")
        
        # 파일 저장
        if output_file:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            print(f"\n💾 결과가 {output_file}에 저장되었습니다.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 평가 중 오류가 발생했습니다: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """CLI 메인 함수"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # 설정 유효성 검증
        from src.config import validate_settings
        validate_settings()
        
    except ValueError as e:
        print(f"❌ 설정 오류: {e}")
        sys.exit(1)
    
    # 명령어 실행
    if args.command == "list-datasets":
        list_datasets()
        
    elif args.command == "list-prompts":
        list_prompts()
        
    elif args.command == "evaluate":
        success = evaluate_dataset(
            dataset_name=args.dataset,
            prompt_type=args.prompt_type,
            output_file=args.output,
            verbose=args.verbose
        )
        if not success:
            sys.exit(1)
    
    else:
        print(f"❌ 알 수 없는 명령어: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()