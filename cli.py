#!/usr/bin/env python3
"""
RAGTrace CLI 인터페이스

RAGAS 평가를 명령줄에서 실행할 수 있는 CLI 도구
프롬프트 타입 선택 기능 포함
"""

import argparse
import sys
import json
import statistics
from typing import Optional
from pathlib import Path
from datetime import datetime

from src.config import (
    settings, 
    PROMPT_TYPE_HELP, 
    SUPPORTED_LLM_TYPES, 
    SUPPORTED_EMBEDDING_TYPES
)
from src.container import container
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
  # 간단한 평가 실행 (HCX-005 + BGE-M3, 자동 결과 저장)
  python cli.py quick-eval evaluation_data
  
  # 기본 프롬프트로 평가 실행
  python cli.py evaluate evaluation_data.json

  # LLM과 임베딩 모델 선택
  python cli.py evaluate evaluation_data.json --llm gemini --embedding hcx
  
  # 한국어 기술 문서 프롬프트로 평가
  python cli.py evaluate evaluation_data.json --prompt-type korean_tech
  
  # 평가 결과 고급 통계 분석
  python cli.py analyze-results results.json --analysis-type all
  
  # 여러 평가 결과 비교 분석
  python cli.py compare-results model1.json model2.json --labels "Model A" "Model B"
  
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
    
    # export-results 서브커맨드 (새로 추가)
    export_parser = subparsers.add_parser("export-results", help="평가 결과를 파일로 내보내기")
    export_parser.add_argument(
        "result_file",
        help="내보낼 결과 JSON 파일 경로"
    )
    export_parser.add_argument(
        "--format",
        choices=["csv", "summary", "report", "all"],
        default="all",
        help="내보낼 형식 (기본값: all)"
    )
    export_parser.add_argument(
        "--output-dir", "-o",
        default="exports",
        help="출력 디렉토리 (기본값: exports)"
    )
    
    # list-checkpoints 서브커맨드
    checkpoint_list_parser = subparsers.add_parser("list-checkpoints", help="저장된 체크포인트 목록 보기")
    
    # resume-evaluation 서브커맨드
    resume_parser = subparsers.add_parser("resume-evaluation", help="중단된 평가 재개")
    resume_parser.add_argument(
        "session_id",
        help="재개할 평가 세션 ID"
    )
    
    # cleanup-checkpoints 서브커맨드
    cleanup_parser = subparsers.add_parser("cleanup-checkpoints", help="오래된 체크포인트 정리")
    cleanup_parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="보존할 일수 (기본값: 7일)"
    )
    
    # quick-eval 서브커맨드 (새로 추가)
    quick_parser = subparsers.add_parser("quick-eval", help="간단한 평가 실행 (HCX-005 + BGE-M3, 자동 결과 저장)")
    quick_parser.add_argument(
        "dataset",
        help="평가할 데이터셋 이름 (확장자 제외)"
    )
    quick_parser.add_argument(
        "--output-dir",
        default="quick_results",
        help="결과 저장 디렉토리 (기본값: quick_results)"
    )
    quick_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세한 로그 출력"
    )
    
    # analyze-results 서브커맨드 (새로 추가)
    analyze_parser = subparsers.add_parser("analyze-results", help="평가 결과 고급 통계 분석")
    analyze_parser.add_argument(
        "result_file",
        help="분석할 평가 결과 JSON 파일 경로"
    )
    analyze_parser.add_argument(
        "--analysis-type",
        choices=["basic", "eda", "advanced", "all"],
        default="all", 
        help="분석 유형 (기본값: all)"
    )
    analyze_parser.add_argument(
        "--output-dir",
        default="analysis_results",
        help="분석 결과 저장 디렉토리 (기본값: analysis_results)"
    )
    analyze_parser.add_argument(
        "--save-plots",
        action="store_true",
        help="차트를 이미지 파일로 저장"
    )
    
    # compare-results 서브커맨드 (새로 추가)
    compare_parser = subparsers.add_parser("compare-results", help="여러 평가 결과 비교 분석")
    compare_parser.add_argument(
        "result_files",
        nargs="+",
        help="비교할 평가 결과 JSON 파일들"
    )
    compare_parser.add_argument(
        "--output-dir",
        default="comparison_results",
        help="비교 결과 저장 디렉토리 (기본값: comparison_results)"
    )
    compare_parser.add_argument(
        "--labels",
        nargs="*",
        help="각 결과 파일의 라벨 (미지정 시 파일명 사용)"
    )
    
    return parser


def list_datasets():
    """사용 가능한 데이터셋 목록 출력"""
    print("📊 사용 가능한 데이터셋:")
    print("-" * 60)
    
    datasets = get_available_datasets()
    if not datasets:
        print("❌ 사용 가능한 데이터셋이 없습니다.")
        print("   data/ 디렉토리에 평가 데이터를 추가하세요.")
        print("   지원 형식: JSON, CSV, Excel (.xlsx, .xls)")
        return
    
    # 파일 형식별로 그룹화
    json_files = [d for d in datasets if d.endswith('.json')]
    csv_files = [d for d in datasets if d.endswith('.csv')]
    excel_files = [d for d in datasets if d.endswith(('.xlsx', '.xls'))]
    
    # 카테고리별 출력
    file_num = 1
    
    if json_files:
        print("\n📄 JSON 파일:")
        for dataset in json_files:
            print(f"  {file_num}. {dataset}")
            file_num += 1
    
    if csv_files:
        print("\n📊 CSV 파일:")
        for dataset in csv_files:
            print(f"  {file_num}. {dataset} (변환 필요)")
            file_num += 1
    
    if excel_files:
        print("\n📈 Excel 파일:")
        for dataset in excel_files:
            print(f"  {file_num}. {dataset} (변환 필요)")
            file_num += 1
    
    print(f"\n총 {len(datasets)}개의 데이터셋이 있습니다.")
    print("\n💡 사용 방법:")
    print("  - JSON: python cli.py evaluate <filename>")
    print("  - CSV/Excel: python cli.py import-data <filename> --output converted.json")


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
    
    # CSV/Excel 파일인 경우 자동 변환
    if dataset_name.endswith(('.csv', '.xlsx', '.xls')):
        print(f"\n📂 CSV/Excel 파일 감지 - JSON으로 자동 변환 중...")
        
        # 데이터 경로 확인 및 처리
        from src.utils.paths import DATA_DIR
        dataset_path = Path(dataset_name)
        if not dataset_path.is_absolute():
            # 상대 경로인 경우 data/ 디렉토리에서 찾기
            dataset_path = DATA_DIR / dataset_name
            if not dataset_path.exists():
                # 현재 디렉토리에서도 찾기
                dataset_path = Path(dataset_name)
        
        if not dataset_path.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {dataset_name}")
            return False
        
        # 변환된 파일명 생성
        base_name = dataset_path.stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        converted_filename = f"{base_name}_converted_{timestamp}.json"
        converted_path = DATA_DIR / converted_filename
        
        # import_data 함수 호출
        import_success = import_data(
            input_file=str(dataset_path),
            output_file=str(converted_path),
            validate=True,
            batch_size=50
        )
        
        if not import_success:
            print("❌ 데이터 변환 실패")
            return False
        
        dataset_name = str(converted_path)
        print(f"✅ 변환 완료: {converted_path}")
    
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
        
        # answer_correctness가 있으면 출력
        if hasattr(result, 'answer_correctness') and result.answer_correctness is not None:
            print(f"answer_correctness: {result.answer_correctness:.4f}")
        
        print("="*50)

        # 자동 보고서 생성
        from src.application.services.result_exporter import ResultExporter
        from dataclasses import asdict
        
        result_dict = asdict(result)
        
        # 메타데이터 추가
        import uuid
        evaluation_id = str(uuid.uuid4())[:8]
        result_dict["metadata"] = {
            "evaluation_id": evaluation_id,
            "timestamp": result_dict.get("timestamp", ""),
            "model": f"{llm.upper()}",
            "embedding_model": f"{embedding_choice.upper()}",
            "dataset": dataset_name,
            "prompt_type": prompt_type_enum.value,
        }
        
        print("\n📤 자동 보고서 생성 중...")
        
        # 출력 디렉토리 생성
        output_dir = Path("exports")
        output_dir.mkdir(exist_ok=True)
        
        exporter = ResultExporter(output_dir=str(output_dir))
        
        try:
            # 전체 패키지 생성 (CSV + 요약 + 보고서)
            files = exporter.export_full_package(result_dict, f"eval_{evaluation_id}")
            
            print(f"✅ 자동 보고서 생성 완료!")
            print(f"📁 출력 디렉토리: {output_dir}")
            print(f"📄 생성된 파일:")
            for file_type, file_path in files.items():
                file_name = Path(file_path).name
                print(f"  - {file_name}")
                
        except Exception as e:
            print(f"⚠️ 자동 보고서 생성 실패: {e}")
            print("평가는 성공했지만 보고서 생성에 문제가 있었습니다.")

        if output_file:
            # 결과를 사용자 지정 파일에도 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 결과가 {output_file} 파일에도 저장되었습니다.")
        
        print("✅ 평가 완료.")
        
        return True

    except Exception as e:
        print(f"\n❌ 평가 중 오류가 발생했습니다: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def export_results(args):
    """평가 결과를 다양한 형식으로 내보내기"""
    from src.application.services.result_exporter import ResultExporter
    
    print(f"📤 결과 내보내기 시작: {args.result_file}")
    
    result_path = Path(args.result_file)
    if not result_path.exists():
        print(f"❌ 결과 파일을 찾을 수 없습니다: {args.result_file}")
        return False
    
    try:
        # 결과 파일 로드
        with open(result_path, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        print(f"✅ 결과 로드 완료")
        
        # 내보내기 서비스 초기화
        exporter = ResultExporter(output_dir=args.output_dir)
        
        files_created = []
        
        if args.format in ["csv", "all"]:
            csv_file = exporter.export_to_csv(result)
            files_created.append(("상세 CSV", csv_file))
            print(f"📊 상세 CSV 생성: {csv_file}")
        
        if args.format in ["summary", "all"]:
            summary_file = exporter.export_summary_csv(result)
            files_created.append(("요약 CSV", summary_file))
            print(f"📈 요약 CSV 생성: {summary_file}")
        
        if args.format in ["report", "all"]:
            report_file = exporter.generate_analysis_report(result)
            files_created.append(("분석 보고서", report_file))
            print(f"📋 분석 보고서 생성: {report_file}")
        
        if args.format == "all":
            print(f"\n✅ 전체 내보내기 완료!")
            print(f"📁 출력 디렉토리: {args.output_dir}")
            print("📄 생성된 파일:")
            for file_type, file_path in files_created:
                print(f"   - {file_type}: {Path(file_path).name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 내보내기 실패: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        return False


def list_checkpoints():
    """저장된 체크포인트 목록 출력"""
    from src.application.services.evaluation_checkpoint import EvaluationCheckpoint
    
    checkpoint_manager = EvaluationCheckpoint()
    sessions = checkpoint_manager.list_sessions()
    
    if not sessions:
        print("📝 저장된 체크포인트가 없습니다.")
        return
    
    print("💾 저장된 평가 세션:")
    print("-" * 100)
    print(f"{'세션 ID':<25} {'데이터셋':<20} {'상태':<10} {'진행률':<8} {'시작 시간':<20}")
    print("-" * 100)
    
    for session in sessions:
        session_id = session['session_id'][:24] + "..." if len(session['session_id']) > 24 else session['session_id']
        dataset_name = session['dataset_name'][:19] + "..." if len(session['dataset_name']) > 19 else session['dataset_name']
        status = session['status']
        progress = f"{session['progress']:.1f}%"
        start_time = session['start_time'][:19] if session['start_time'] else 'N/A'
        
        print(f"{session_id:<25} {dataset_name:<20} {status:<10} {progress:<8} {start_time:<20}")
    
    print(f"\n총 {len(sessions)}개의 세션이 저장되어 있습니다.")


def resume_evaluation(args):
    """중단된 평가 재개"""
    from src.application.services.evaluation_checkpoint import EvaluationCheckpoint, BatchEvaluationManager
    from src.container.factories.evaluation_use_case_factory import EvaluationRequest
    from src.utils.paths import get_evaluation_data_path
    from datasets import Dataset
    
    print(f"🔄 평가 재개 시도: {args.session_id}")
    
    checkpoint_manager = EvaluationCheckpoint()
    checkpoint = checkpoint_manager.resume_session(args.session_id)
    
    if not checkpoint:
        return False
    
    if checkpoint.get('status') == 'completed':
        print("✅ 이미 완료된 평가입니다.")
        
        # 완료된 결과 파일 확인
        result_file = checkpoint_manager.checkpoint_dir / f"{args.session_id}.result.json"
        if result_file.exists():
            print(f"📄 결과 파일: {result_file}")
            
            # 결과 요약 출력
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                print("\n📊 평가 결과 요약:")
                print(f"- RAGAS Score: {result.get('ragas_score', 0):.3f}")
                print(f"- 데이터셋 크기: {result.get('metadata', {}).get('dataset_size', 0)}개")
                print(f"- 성공률: {result.get('metadata', {}).get('success_rate', 0):.1f}%")
                
            except Exception as e:
                print(f"⚠️ 결과 파일 읽기 실패: {e}")
        
        return True
    
    if checkpoint.get('status') == 'failed':
        print("❌ 실패한 평가 세션입니다.")
        partial_result = checkpoint.get('partial_result')
        if partial_result:
            print("📊 부분 결과 출력:")
            print(f"- 부분 RAGAS Score: {partial_result.get('ragas_score', 0):.3f}")
            print(f"- 완료된 항목: {len(partial_result.get('individual_scores', []))}개")
        return False
    
    # 실제 재개 구현
    try:
        print("🔄 중단된 평가를 재개합니다...")
        
        # 체크포인트에서 설정 복원
        config = checkpoint.get('config', {})
        dataset_name = checkpoint.get('dataset_name')
        completed_items = checkpoint.get('completed_items', 0)
        
        print(f"📊 데이터셋: {dataset_name}")
        print(f"✅ 이미 완료: {completed_items}개")
        print(f"🔄 재개 위치: {completed_items + 1}번째 항목부터")
        
        # 원본 데이터셋 로드
        data_path = get_evaluation_data_path(dataset_name)
        if not data_path:
            print(f"❌ 데이터셋을 찾을 수 없습니다: {dataset_name}")
            return False
        
        # 데이터셋 로드 및 미완료 부분만 추출
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        remaining_data = data[completed_items:]  # 미완료 부분만
        
        if not remaining_data:
            print("✅ 모든 항목이 이미 완료되었습니다.")
            return True
        
        print(f"📋 남은 항목: {len(remaining_data)}개")
        
        # 평가 설정 복원
        llm_type = config.get('llm_type', 'gemini')
        embedding_type = config.get('embedding_type', 'gemini')
        prompt_type_str = config.get('prompt_type', 'default')
        
        # PromptType enum으로 변환
        from src.domain.prompts import PromptType
        if isinstance(prompt_type_str, str):
            try:
                prompt_type = PromptType(prompt_type_str)
            except ValueError:
                prompt_type = PromptType.DEFAULT
        else:
            prompt_type = prompt_type_str
        
        print(f"🤖 LLM: {llm_type}")
        print(f"🌐 Embedding: {embedding_type}")
        print(f"🎯 Prompt Type: {prompt_type.value}")
        
        # 평가 어댑터 생성
        request = EvaluationRequest(
            llm_type=llm_type,
            embedding_type=embedding_type,
            prompt_type=prompt_type
        )
        
        evaluation_use_case, llm_adapter, embedding_adapter = container.create_evaluation_use_case(request)
        
        # 남은 데이터로 Dataset 생성
        remaining_dataset = Dataset.from_list(remaining_data)
        
        # RAGAS 어댑터 직접 사용하여 평가 재개
        from src.infrastructure.evaluation.ragas_adapter_legacy import RagasEvalAdapter
        
        ragas_adapter = RagasEvalAdapter(
            llm=llm_adapter,
            embeddings=embedding_adapter,
            prompt_type=prompt_type
        )
        
        # 배치 평가 관리자 생성
        batch_size = config.get('batch_size', 10)
        batch_manager = BatchEvaluationManager(checkpoint_manager, batch_size)
        
        # 체크포인트와 함께 나머지 평가 실행
        def batch_eval_func(batch_dataset):
            return ragas_adapter._run_evaluation_with_timeout(batch_dataset)
        
        # 기존 결과와 새 결과 합치기
        print("🔄 나머지 평가 실행 중...")
        remaining_result = batch_manager.evaluate_with_checkpoints(
            remaining_dataset, 
            batch_eval_func, 
            config
        )
        
        # 기존 개별 결과 가져오기
        existing_results = checkpoint.get('individual_results', [])
        new_results = remaining_result.get('individual_scores', [])
        
        # 전체 결과 합치기
        all_individual_results = existing_results + new_results
        
        # 최종 결과 재계산
        final_result = batch_manager._compile_final_result(
            all_individual_results, 
            config, 
            remaining_result.get('metadata', {}).get('error_count', 0)
        )
        
        # 세션 완료 처리
        checkpoint_manager.complete_session(final_result)
        
        print("\n✅ 평가 재개 완료!")
        print("📊 최종 결과:")
        print(f"- RAGAS Score: {final_result.get('ragas_score', 0):.3f}")
        print(f"- 전체 항목: {len(all_individual_results)}개")
        print(f"- 성공률: {final_result.get('metadata', {}).get('success_rate', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ 평가 재개 실패: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        return False


def cleanup_checkpoints(args):
    """오래된 체크포인트 정리"""
    from src.application.services.evaluation_checkpoint import EvaluationCheckpoint
    
    print(f"🧹 체크포인트 정리 시작 ({args.days}일 이상된 파일)")
    
    checkpoint_manager = EvaluationCheckpoint()
    checkpoint_manager.cleanup_old_sessions(args.days)
    
    print("✅ 체크포인트 정리 완료")
    return True


def quick_eval(args):
    """간단한 평가 실행 (HCX-005 + BGE-M3 + 자동 결과 저장)"""
    import os
    from datetime import datetime
    from pathlib import Path
    
    print("🚀 RAGTrace 간단 평가 시작")
    print("=" * 50)
    print("🤖 LLM: HCX-005 (Naver)")
    print("🌐 Embedding: BGE-M3 (Local)")
    print("📁 데이터셋:", args.dataset)
    print("=" * 50)
    
    # 결과 디렉토리 생성
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # CSV/Excel 파일인 경우 자동 변환
    dataset_to_use = args.dataset
    if args.dataset.endswith(('.csv', '.xlsx', '.xls')):
        print(f"\n📂 CSV/Excel 파일 감지 - JSON으로 자동 변환 중...")
        
        # 데이터 경로 확인 및 처리
        from src.utils.paths import DATA_DIR
        dataset_path = Path(args.dataset)
        if not dataset_path.is_absolute():
            # 상대 경로인 경우 data/ 디렉토리에서 찾기
            dataset_path = DATA_DIR / args.dataset
            if not dataset_path.exists():
                # 현재 디렉토리에서도 찾기
                dataset_path = Path(args.dataset)
        
        if not dataset_path.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {args.dataset}")
            return False
        
        # 변환된 파일명 생성
        base_name = dataset_path.stem
        converted_filename = f"{base_name}_converted.json"
        converted_path = output_dir / converted_filename
        
        # import_data 함수 호출
        import_success = import_data(
            input_file=str(dataset_path),
            output_file=str(converted_path),
            validate=True,
            batch_size=50
        )
        
        if not import_success:
            print("❌ 데이터 변환 실패")
            return False
        
        dataset_to_use = str(converted_path)
        print(f"✅ 변환 완료: {converted_path}")
    
    # 타임스탬프 기반 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dataset_name = Path(dataset_to_use).stem
    result_filename = f"{base_dataset_name}_{timestamp}.json"
    result_path = output_dir / result_filename
    
    try:
        # 1. 평가 실행
        print("\n📊 1단계: 평가 실행 중...")
        success = evaluate_dataset(
            dataset_name=dataset_to_use,
            llm="hcx",
            embedding="bge_m3",
            prompt_type=None,
            output_file=str(result_path),
            verbose=args.verbose
        )
        
        if not success:
            print("❌ 평가 실행 실패")
            return False
        
        # 2. 결과 내보내기
        print(f"\n📤 2단계: 결과 내보내기 중...")
        
        # export_results 함수를 직접 호출하기 위한 args 객체 생성
        class ExportArgs:
            def __init__(self, result_file, output_dir):
                self.result_file = result_file
                self.format = "all"
                self.output_dir = output_dir
        
        export_args = ExportArgs(str(result_path), str(output_dir))
        export_success = export_results(export_args)
        
        if not export_success:
            print("⚠️ 결과 내보내기 실패 (평가는 완료)")
        
        # 3. 결과 요약
        print("\n" + "=" * 50)
        print("✅ 간단 평가 완료!")
        print("=" * 50)
        print(f"📄 평가 결과 파일: {result_path}")
        
        if export_success:
            print(f"📁 분석 보고서 디렉토리: {output_dir}")
            print("📋 생성된 파일:")
            print("   - 상세 CSV: 개별 항목별 점수")
            print("   - 요약 CSV: 메트릭별 기초 통계")
            print("   - 분석 보고서: 상세 성능 분석 (Markdown)")
        
        print(f"\n💡 다음 명령어로 결과를 다시 내보낼 수 있습니다:")
        print(f"   uv run python cli.py export-results {result_path} --format all --output-dir {output_dir}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 간단 평가 중 오류 발생: {str(e)}")
        if args.verbose:
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
            
    elif args.command == "export-results":
        success = export_results(args)
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
    
    elif args.command == "list-checkpoints":
        list_checkpoints()
    
    elif args.command == "resume-evaluation":
        success = resume_evaluation(args)
        if not success:
            sys.exit(1)
    
    elif args.command == "cleanup-checkpoints":
        success = cleanup_checkpoints(args)
        if not success:
            sys.exit(1)
    
    elif args.command == "quick-eval":
        success = quick_eval(args)
        if not success:
            sys.exit(1)
    
    elif args.command == "analyze-results":
        success = analyze_results(args)
        if not success:
            sys.exit(1)
    
    elif args.command == "compare-results":
        success = compare_results(args)
        if not success:
            sys.exit(1)
    
    else:
        print(f"❌ 알 수 없는 명령어: {args.command}")
        parser.print_help()
        sys.exit(1)


def analyze_results(args) -> bool:
    """평가 결과 고급 통계 분석"""
    try:
        result_file = Path(args.result_file)
        if not result_file.exists():
            print(f"❌ 결과 파일을 찾을 수 없습니다: {result_file}")
            return False
        
        # 결과 파일 로드
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        print(f"📊 결과 분석 시작: {result_file.name}")
        print(f"🎯 분석 유형: {args.analysis_type}")
        
        # 출력 디렉토리 생성
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # 개별 점수 추출
        individual_scores = result_data.get("individual_scores", [])
        if not individual_scores:
            print("⚠️ 개별 점수 데이터가 없습니다. 기본 통계만 출력합니다.")
            
        # 분석 유형에 따른 처리
        if args.analysis_type in ["basic", "all"]:
            print("\n📈 기초 통계 분석")
            basic_stats = perform_basic_analysis(result_data, individual_scores)
            save_basic_analysis(basic_stats, output_dir)
            
        if args.analysis_type in ["eda", "all"]:
            print("\n🔍 탐색적 데이터 분석 (EDA)")
            eda_results = perform_eda_analysis(individual_scores)
            save_eda_analysis(eda_results, output_dir)
            
        if args.analysis_type in ["advanced", "all"]:
            print("\n🧮 고급 통계 분석")
            advanced_stats = perform_advanced_analysis(individual_scores)
            save_advanced_analysis(advanced_stats, output_dir)
        
        print(f"\n✅ 분석 완료! 결과가 {output_dir}에 저장되었습니다.")
        return True
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        return False


def compare_results(args) -> bool:
    """여러 평가 결과 비교 분석"""
    try:
        result_files = [Path(f) for f in args.result_files]
        
        # 파일 존재 확인
        for result_file in result_files:
            if not result_file.exists():
                print(f"❌ 결과 파일을 찾을 수 없습니다: {result_file}")
                return False
        
        print(f"📊 {len(result_files)}개 결과 파일 비교 분석")
        
        # 라벨 설정
        if args.labels and len(args.labels) == len(result_files):
            labels = args.labels
        else:
            labels = [f.stem for f in result_files]
        
        # 출력 디렉토리 생성
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # 결과 데이터 로드
        results_data = []
        for i, result_file in enumerate(result_files):
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['label'] = labels[i]
                results_data.append(data)
        
        # 비교 분석 수행
        comparison_stats = perform_comparison_analysis(results_data)
        save_comparison_analysis(comparison_stats, output_dir, labels)
        
        print(f"\n✅ 비교 분석 완료! 결과가 {output_dir}에 저장되었습니다.")
        return True
        
    except Exception as e:
        print(f"❌ 비교 분석 중 오류 발생: {e}")
        return False


def perform_basic_analysis(result_data: dict, individual_scores: list) -> dict:
    """기초 통계 분석 수행"""
    print("  📋 메트릭별 기초 통계 계산 중...")
    
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision', 'answer_correctness']
    basic_stats = {}
    
    for metric in metrics:
        if metric in result_data:
            # 전체 평균값
            overall_mean = result_data[metric]
            
            # 개별 점수에서 통계 계산 (None 값 제외)
            if individual_scores:
                scores = [item.get(metric) for item in individual_scores if item.get(metric) is not None]
                if scores:
                    basic_stats[metric] = {
                        'mean': statistics.mean(scores),
                        'median': statistics.median(scores),
                        'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0.0,
                        'min': min(scores),
                        'max': max(scores),
                        'count': len(scores),
                        'success_rate': len(scores) / len(individual_scores) * 100
                    }
                else:
                    basic_stats[metric] = {'error': 'No valid scores'}
            else:
                basic_stats[metric] = {'mean': overall_mean, 'count': 1}
    
    # 전체 성능 등급 계산
    if 'ragas_score' in result_data:
        ragas_score = result_data['ragas_score']
        if ragas_score >= 0.8:
            grade = "A (우수)"
        elif ragas_score >= 0.6:
            grade = "B (보통)"
        elif ragas_score >= 0.4:
            grade = "C (개선 필요)"
        else:
            grade = "D (크게 개선 필요)"
        
        basic_stats['overall'] = {
            'ragas_score': ragas_score,
            'grade': grade
        }
    
    return basic_stats


def perform_eda_analysis(individual_scores: list) -> dict:
    """탐색적 데이터 분석 수행"""
    if not individual_scores:
        return {'error': 'No individual scores available'}
    
    print("  🔍 상관관계 및 분포 분석 중...")
    
    import pandas as pd
    import numpy as np
    
    # DataFrame 생성 (None 값 제외)
    df = pd.DataFrame(individual_scores)
    
    # 상관관계 매트릭스 계산
    numeric_df = df.select_dtypes(include=[np.number])
    correlation_matrix = numeric_df.corr()
    
    # 분포 특성 분석
    distribution_stats = {}
    for column in numeric_df.columns:
        data = numeric_df[column].dropna()
        if len(data) > 0:
            distribution_stats[column] = {
                'skewness': float(data.skew()),
                'kurtosis': float(data.kurtosis()),
                'quartiles': {
                    'q1': float(data.quantile(0.25)),
                    'q2': float(data.quantile(0.5)),
                    'q3': float(data.quantile(0.75)),
                    'iqr': float(data.quantile(0.75) - data.quantile(0.25))
                }
            }
    
    return {
        'correlation_matrix': correlation_matrix.to_dict(),
        'distribution_stats': distribution_stats,
        'data_completeness': {
            'total_samples': len(individual_scores),
            'missing_data': df.isnull().sum().to_dict()
        }
    }


def perform_advanced_analysis(individual_scores: list) -> dict:
    """고급 통계 분석 수행"""
    if not individual_scores or len(individual_scores) < 3:
        return {'error': 'Insufficient data for advanced analysis (need at least 3 samples)'}
    
    print("  🧮 정규성 검정 및 신뢰구간 계산 중...")
    
    import pandas as pd
    import numpy as np
    from scipy import stats
    
    df = pd.DataFrame(individual_scores)
    advanced_stats = {}
    
    for column in df.select_dtypes(include=[np.number]).columns:
        data = df[column].dropna()
        if len(data) >= 3:
            # 정규성 검정
            shapiro_stat, shapiro_p = stats.shapiro(data)
            
            # 신뢰구간 (95%)
            mean_val = np.mean(data)
            sem = stats.sem(data)
            ci_95 = stats.t.interval(0.95, df=len(data)-1, loc=mean_val, scale=sem)
            
            advanced_stats[column] = {
                'normality_test': {
                    'shapiro_wilk_statistic': float(shapiro_stat),
                    'shapiro_wilk_p_value': float(shapiro_p),
                    'is_normal': shapiro_p > 0.05
                },
                'confidence_intervals': {
                    'mean': float(mean_val),
                    'ci_95_lower': float(ci_95[0]),
                    'ci_95_upper': float(ci_95[1]),
                    'margin_of_error': float(ci_95[1] - mean_val)
                }
            }
    
    return advanced_stats


def perform_comparison_analysis(results_data: list) -> dict:
    """여러 결과 비교 분석"""
    print("  📊 모델 간 성능 비교 중...")
    
    metrics = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision', 'answer_correctness', 'ragas_score']
    comparison_stats = {}
    
    for metric in metrics:
        metric_values = []
        labels = []
        
        for result in results_data:
            if metric in result:
                metric_values.append(result[metric])
                labels.append(result['label'])
        
        if metric_values:
            comparison_stats[metric] = {
                'values': dict(zip(labels, metric_values)),
                'best_model': labels[metric_values.index(max(metric_values))],
                'worst_model': labels[metric_values.index(min(metric_values))],
                'range': max(metric_values) - min(metric_values),
                'mean': statistics.mean(metric_values),
                'std_dev': statistics.stdev(metric_values) if len(metric_values) > 1 else 0.0
            }
    
    return comparison_stats


def save_basic_analysis(stats: dict, output_dir: Path):
    """기초 통계 분석 결과 저장"""
    with open(output_dir / 'basic_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    # 텍스트 요약 저장
    with open(output_dir / 'basic_analysis_summary.txt', 'w', encoding='utf-8') as f:
        f.write("📈 기초 통계 분석 요약\n")
        f.write("=" * 50 + "\n\n")
        
        for metric, data in stats.items():
            if metric == 'overall':
                f.write(f"🎯 전체 성능: {data.get('grade', 'N/A')} (점수: {data.get('ragas_score', 0):.3f})\n\n")
            elif 'error' not in data:
                f.write(f"{metric}:\n")
                f.write(f"  평균: {data.get('mean', 0):.3f}\n")
                f.write(f"  중앙값: {data.get('median', 0):.3f}\n")
                f.write(f"  표준편차: {data.get('std_dev', 0):.3f}\n")
                f.write(f"  범위: {data.get('min', 0):.3f} ~ {data.get('max', 0):.3f}\n")
                if 'success_rate' in data:
                    f.write(f"  성공률: {data['success_rate']:.1f}%\n")
                f.write("\n")
    
    print(f"  ✅ 기초 분석 결과 저장: {output_dir}/basic_analysis.json")


def save_eda_analysis(results: dict, output_dir: Path):
    """EDA 분석 결과 저장"""
    with open(output_dir / 'eda_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ EDA 분석 결과 저장: {output_dir}/eda_analysis.json")


def save_advanced_analysis(stats: dict, output_dir: Path):
    """고급 통계 분석 결과 저장"""
    with open(output_dir / 'advanced_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ 고급 분석 결과 저장: {output_dir}/advanced_analysis.json")


def save_comparison_analysis(stats: dict, output_dir: Path, labels: list):
    """비교 분석 결과 저장"""
    with open(output_dir / 'comparison_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    # 비교 요약 저장
    with open(output_dir / 'comparison_summary.txt', 'w', encoding='utf-8') as f:
        f.write("📊 모델 비교 분석 요약\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"비교 대상: {', '.join(labels)}\n\n")
        
        for metric, data in stats.items():
            if 'values' in data:
                f.write(f"{metric}:\n")
                f.write(f"  최고 성능: {data['best_model']} ({data['values'][data['best_model']]:.3f})\n")
                f.write(f"  최저 성능: {data['worst_model']} ({data['values'][data['worst_model']]:.3f})\n")
                f.write(f"  성능 차이: {data['range']:.3f}\n")
                f.write(f"  평균: {data['mean']:.3f}\n\n")
    
    print(f"  ✅ 비교 분석 결과 저장: {output_dir}/comparison_analysis.json")


if __name__ == "__main__":
    main()