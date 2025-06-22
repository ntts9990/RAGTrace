#!/usr/bin/env python3
"""
RAGTrace CLI 인터페이스

RAGAS 평가를 명령줄에서 실행할 수 있는 CLI 도구
프롬프트 타입 선택 기능 포함
"""

import argparse
import sys
import json
from typing import Optional
from pathlib import Path

from src.config import (
    settings, 
    PROMPT_TYPE_HELP, 
    SUPPORTED_LLM_TYPES, 
    SUPPORTED_EMBEDDING_TYPES
)
from src.container.main_container import container
from src.domain.prompts import PromptType
from src.utils.paths import get_available_datasets, get_evaluation_data_path
from src.infrastructure.data_import.importers import ImporterFactory
from src.infrastructure.data_import.validators import ImportDataValidator


def create_parser() -> argparse.ArgumentParser:
    """CLI 파서 생성"""
    parser = argparse.ArgumentParser(
        description="RAGTrace - RAG 시스템 성능 평가 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 프롬프트로 평가 실행
  python cli.py evaluate evaluation_data.json

  # LLM과 임베딩 모델 선택
  python cli.py evaluate evaluation_data.json --llm gemini --embedding hcx
  
  # 한국어 기술 문서 프롬프트로 평가
  python cli.py evaluate evaluation_data.json --prompt-type korean_tech
  
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
        "--llm",
        choices=SUPPORTED_LLM_TYPES,
        default=settings.DEFAULT_LLM,
        help=f"평가에 사용할 LLM (기본값: {settings.DEFAULT_LLM})"
    )
    eval_parser.add_argument(
        "--embedding",
        choices=SUPPORTED_EMBEDDING_TYPES,
        default=None,
        help=f"평가에 사용할 임베딩 모델 (기본값: {settings.DEFAULT_EMBEDDING}). 지정하지 않으면 기본 임베딩을 사용합니다."
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
    
    # import-data 서브커맨드 (새로 추가)
    import_parser = subparsers.add_parser("import-data", help="Excel/CSV 파일을 JSON 형식으로 변환")
    import_parser.add_argument(
        "input_file",
        help="변환할 Excel(.xlsx, .xls) 또는 CSV 파일 경로"
    )
    import_parser.add_argument(
        "--output", "-o",
        help="변환된 JSON 파일 저장 경로 (기본값: 입력파일명.json)"
    )
    import_parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="변환된 데이터 검증 수행"
    )
    import_parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="배치 처리 크기 (기본값: 50)"
    )
    
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


def import_data(input_file: str, output_file: Optional[str] = None, 
               validate: bool = False, batch_size: int = 50):
    """Excel/CSV 파일을 JSON 형식으로 변환"""
    
    try:
        # Import 어댑터 생성
        importer = ImporterFactory.create_importer(input_file)
        
        # 파일 형식 검증
        if not importer.validate_format(input_file):
            print(f"❌ 파일 형식이 올바르지 않습니다: {input_file}")
            print(f"지원되는 형식: {ImporterFactory.get_supported_formats()}")
            return False
        
        print(f"📂 파일 변환 시작: {input_file}")
        
        # 데이터 Import
        evaluation_data_list = importer.import_data(input_file)
        
        if not evaluation_data_list:
            print("❌ 변환할 데이터가 없습니다.")
            return False
        
        print(f"✅ {len(evaluation_data_list)}개 항목 변환 완료")
        
        # 검증 수행 (옵션)
        if validate:
            validator = ImportDataValidator()
            validation_result = validator.validate_data_list(evaluation_data_list)
            
            print("\n" + validator.get_validation_summary(validation_result))
            
            # 검증 실패 시 상세 정보 출력
            if not validation_result.is_valid:
                print("\n📋 오류 상세:")
                for error in validation_result.errors[:10]:  # 최대 10개만 표시
                    print(f"   {error}")
                
                if len(validation_result.errors) > 10:
                    print(f"   ... 외 {len(validation_result.errors) - 10}개 오류")
                
                if validation_result.warnings:
                    print("\n⚠️ 경고 상세:")
                    for warning in validation_result.warnings[:5]:  # 최대 5개만 표시
                        print(f"   {warning}")
        
        # 출력 파일 경로 결정
        if not output_file:
            input_path = Path(input_file)
            output_file = str(input_path.with_suffix('.json'))
        
        # JSON 파일로 저장
        from dataclasses import asdict
        output_data = [asdict(data) for data in evaluation_data_list]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 변환 결과 저장: {output_file}")
        
        # 배치 처리 정보 출력
        if len(evaluation_data_list) > batch_size:
            estimated_batches = (len(evaluation_data_list) + batch_size - 1) // batch_size
            print(f"\n🔄 배치 처리 정보:")
            print(f"   배치 크기: {batch_size}")
            print(f"   예상 배치 수: {estimated_batches}")
            print(f"   대용량 처리 시 배치 처리를 권장합니다.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 변환 중 오류가 발생했습니다: {str(e)}")
        return False


def evaluate_dataset(dataset_name: str, llm: str, embedding: Optional[str] = None, 
                    prompt_type: Optional[str] = None, output_file: Optional[str] = None, 
                    verbose: bool = False):
    """데이터셋 평가 실행"""
    
    # 임베딩 모델 선택 (미지정 시 기본 임베딩 사용)
    embedding_choice = embedding or settings.DEFAULT_EMBEDDING
    
    # LLM 및 임베딩 어댑터 선택
    try:
        # 팩토리를 통해 UseCase 생성
        from src.container.factories.evaluation_use_case_factory import EvaluationRequest
        
        request = EvaluationRequest(
            llm_type=llm,
            embedding_type=embedding_choice,
            prompt_type=PromptType(prompt_type) if prompt_type else settings.get_prompt_type()
        )
        
        evaluation_use_case, _, _ = container.create_evaluation_use_case(request)
        
        if llm in ["hcx"] and not settings.CLOVA_STUDIO_API_KEY:
            print(f"❌ '{llm}' LLM을 사용하려면 .env 파일에 CLOVA_STUDIO_API_KEY를 설정해야 합니다.")
            return False
        if embedding_choice in ["hcx"] and not settings.CLOVA_STUDIO_API_KEY:
            print(f"❌ '{embedding_choice}' 임베딩을 사용하려면 .env 파일에 CLOVA_STUDIO_API_KEY를 설정해야 합니다.")
            return False

    except Exception as e:
        print(f"❌ '{llm}' LLM 또는 '{embedding_choice}' 임베딩 어댑터 초기화 중 오류 발생: {e}")
        return False
    
    print(f"🤖 LLM: {llm}")
    print(f"🌐 Embedding: {embedding_choice}")

    # 프롬프트 타입 설정
    prompt_type_enum = PromptType(prompt_type) if prompt_type else settings.get_prompt_type()
    print(f"🎯 프롬프트 타입: {prompt_type_enum.value.upper()}")

    try:
        data_path = get_evaluation_data_path(dataset_name)
        if not data_path:
            print(f"❌ 데이터셋 '{dataset_name}'을 찾을 수 없습니다.")
            available_datasets = get_available_datasets()
            if available_datasets:
                print("사용 가능한 데이터셋:")
                for ds in available_datasets:
                    print(f"  - {ds}")
            return False
            
        print(f"📊 데이터셋: {dataset_name}")

        result = evaluation_use_case.execute(
            dataset_name=dataset_name,
        )
        
        if not result:
            print("❌ 평가 실행에 실패했습니다.")
            return False

        # 결과 요약 출력
        print("\n" + "="*50)
        print("📊 평가 결과 요약")
        print("="*50)
        print(f"ragas_score  : {result.ragas_score:.4f}")
        print(f"answer_relevancy: {result.answer_relevancy:.4f}")
        print(f"faithfulness   : {result.faithfulness:.4f}")
        print(f"context_recall : {result.context_recall:.4f}")
        print(f"context_precision: {result.context_precision:.4f}")
        print("="*50)

        if output_file:
            import json
            from dataclasses import asdict
            
            # 결과를 파일에 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, ensure_ascii=False, indent=2)
            
            print(f"✅ 결과가 {output_file} 파일에 저장되었습니다.")
        else:
            print("✅ 평가 완료.")
        
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
            llm=args.llm,
            embedding=args.embedding,
            prompt_type=args.prompt_type,
            output_file=args.output,
            verbose=args.verbose
        )
        if not success:
            sys.exit(1)
    
    elif args.command == "import-data":
        success = import_data(
            input_file=args.input_file,
            output_file=args.output,
            validate=args.validate,
            batch_size=args.batch_size
        )
        if not success:
            sys.exit(1)
    
    else:
        print(f"❌ 알 수 없는 명령어: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()