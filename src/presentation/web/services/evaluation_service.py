"""
Evaluation Service

평가 실행 관련 서비스입니다.
"""

import json
from typing import Dict, Any
from datetime import datetime

from src.container import container
from src.container.factories.evaluation_use_case_factory import EvaluationRequest
from src.utils.paths import get_evaluation_data_path
from ..models.evaluation_model import EvaluationConfig, EvaluationResult, EvaluationModel
from .database_service import DatabaseService


class EvaluationService:
    """평가 실행 서비스"""
    
    @staticmethod
    def execute_evaluation(config: EvaluationConfig) -> EvaluationResult:
        """평가 실행"""
        # 평가 요청 생성
        request = EvaluationRequest(
            llm_type=config.llm_type,
            embedding_type=config.embedding_type,
            prompt_type=config.prompt_type
        )
        
        # 평가 시작 시간 기록
        import time
        start_time = time.time()
        evaluation_start = datetime.now()
        
        # 컨테이너에서 유스케이스 가져오기
        evaluation_use_case, llm_adapter, embedding_adapter = container.create_evaluation_use_case(request)
        
        # 평가 실행
        evaluation_result = evaluation_use_case.execute(dataset_name=config.dataset_name)
        
        # 평가 종료 시간 기록
        end_time = time.time()
        evaluation_end = datetime.now()
        duration_seconds = end_time - start_time
        duration_minutes = duration_seconds / 60.0
        
        # 결과 딕셔너리 변환
        result_dict = evaluation_result.to_dict()
        
        # 데이터셋 크기 계산
        dataset_size = len(result_dict.get("individual_scores", []))
        avg_time_per_item = duration_seconds / dataset_size if dataset_size > 0 else 0
        
        # 평가 ID 생성
        evaluation_id = f"eval_{evaluation_start.strftime('%Y%m%d_%H%M%S')}_{hash(str(result_dict)) % 100000:05d}"
        
        # 메타데이터 추가
        if "metadata" not in result_dict:
            result_dict["metadata"] = {}
        
        result_dict["metadata"].update({
            "evaluation_id": evaluation_id,
            "timestamp": evaluation_start.strftime('%Y-%m-%d %H:%M:%S'),
            "start_time": evaluation_start.isoformat(),
            "end_time": evaluation_end.isoformat(),
            "total_duration_minutes": duration_minutes,
            "avg_time_per_item_seconds": avg_time_per_item,
            "dataset_size": dataset_size,
            "llm_type": config.llm_type,
            "embedding_type": config.embedding_type,
            "dataset": config.dataset_name,
            "prompt_type": config.prompt_type.value
        })
        
        # QA 데이터 추가 (상세 분석용)
        EvaluationService._add_qa_data(result_dict, config.dataset_name)
        
        # 데이터베이스에 저장
        DatabaseService.save_evaluation_result(result_dict)
        
        # EvaluationResult 모델로 변환하여 반환
        return EvaluationModel.parse_result_dict(result_dict)
    
    @staticmethod
    def _add_qa_data(result_dict: Dict[str, Any], dataset_name: str) -> None:
        """QA 데이터를 결과에 추가"""
        dataset_path = get_evaluation_data_path(dataset_name)
        if dataset_path:
            try:
                from pathlib import Path
                from src.infrastructure.data_import.importers import ExcelImporter, CSVImporter
                
                file_path = Path(dataset_path)
                file_extension = file_path.suffix.lower()
                
                if file_extension in ['.xlsx', '.xls']:
                    # Excel 파일 처리
                    importer = ExcelImporter()
                    evaluation_data_list = importer.import_data(file_path)
                    qa_data = [
                        {
                            "question": item.question,
                            "contexts": item.contexts,
                            "answer": item.answer,
                            "ground_truth": item.ground_truth
                        }
                        for item in evaluation_data_list
                    ]
                elif file_extension == '.csv':
                    # CSV 파일 처리
                    importer = CSVImporter()
                    evaluation_data_list = importer.import_data(file_path)
                    qa_data = [
                        {
                            "question": item.question,
                            "contexts": item.contexts,
                            "answer": item.answer,
                            "ground_truth": item.ground_truth
                        }
                        for item in evaluation_data_list
                    ]
                else:
                    # JSON 파일 처리 (기본)
                    with open(dataset_path, encoding="utf-8") as f:
                        qa_data = json.load(f)
                
                qa_count = len(result_dict.get("individual_scores", []))
                result_dict["qa_data"] = qa_data[:qa_count]
            except Exception:
                # QA 데이터 로드 실패 시 무시
                pass
    
    @staticmethod
    def validate_configuration(config: EvaluationConfig) -> bool:
        """평가 설정 유효성 검증"""
        # HCX 모델 사용 시 API 키 확인
        if config.llm_type == "hcx" or config.embedding_type == "hcx":
            from src.config import settings
            if not settings.CLOVA_STUDIO_API_KEY:
                return False
        
        # 데이터셋 존재 확인
        dataset_path = get_evaluation_data_path(config.dataset_name)
        return dataset_path is not None and dataset_path.exists()
    
    @staticmethod
    def get_configuration_error_message(config: EvaluationConfig) -> str:
        """설정 오류 메시지 반환"""
        if config.llm_type == "hcx" or config.embedding_type == "hcx":
            from src.config import settings
            if not settings.CLOVA_STUDIO_API_KEY:
                return "❌ HCX 모델을 사용하려면 .env 파일에 CLOVA_STUDIO_API_KEY를 설정해야 합니다."
        
        dataset_path = get_evaluation_data_path(config.dataset_name)
        if not dataset_path or not dataset_path.exists():
            return f"❌ 데이터셋 '{config.dataset_name}'을 찾을 수 없습니다."
        
        return "❌ 알 수 없는 설정 오류입니다."