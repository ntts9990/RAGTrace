"""
Evaluation Service

평가 실행 관련 서비스입니다.
"""

import json
from typing import Dict, Any

from src.container import get_evaluation_use_case_with_llm
from src.utils.paths import get_evaluation_data_path
from ..models.evaluation_model import EvaluationConfig, EvaluationResult, EvaluationModel
from .database_service import DatabaseService


class EvaluationService:
    """평가 실행 서비스"""
    
    @staticmethod
    def execute_evaluation(config: EvaluationConfig) -> EvaluationResult:
        """평가 실행"""
        # 선택된 LLM, 임베딩, 프롬프트로 유스케이스 가져오기
        evaluation_use_case, llm_adapter, embedding_adapter = get_evaluation_use_case_with_llm(
            config.llm_type, 
            config.embedding_type, 
            config.prompt_type
        )
        
        # 평가 실행
        evaluation_result = evaluation_use_case.execute(dataset_name=config.dataset_name)
        
        # 결과 딕셔너리 변환
        result_dict = evaluation_result.to_dict()
        
        # 메타데이터 추가
        if "metadata" not in result_dict:
            result_dict["metadata"] = {}
        
        result_dict["metadata"].update({
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