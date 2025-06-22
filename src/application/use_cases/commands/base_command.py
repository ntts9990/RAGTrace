"""
Base Command for Evaluation Pipeline

평가 파이프라인의 기본 Command 인터페이스입니다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, List

from datasets import Dataset
from src.domain import EvaluationData, EvaluationError, EvaluationResult
from src.domain.prompts import PromptType
from src.application.services.generation_service import GenerationResult


@dataclass
class EvaluationContext:
    """평가 실행 컨텍스트 - 명령들 간 데이터 공유"""
    
    # 입력 데이터
    dataset_name: str
    prompt_type: Optional[PromptType] = None
    
    # 중간 결과들
    raw_data: Optional[List[EvaluationData]] = None
    validation_report: Optional[Any] = None
    generation_result: Optional[GenerationResult] = None
    ragas_dataset: Optional[Dataset] = None
    evaluation_result_dict: Optional[dict] = None
    
    # 최종 결과
    final_result: Optional[EvaluationResult] = None


class EvaluationCommand(ABC):
    """평가 명령 기본 인터페이스"""
    
    @abstractmethod
    def execute(self, context: EvaluationContext) -> None:
        """명령 실행"""
        pass
    
    @abstractmethod
    def get_command_name(self) -> str:
        """명령 이름 반환"""
        pass
    
    def log_start(self):
        """명령 시작 로그"""
        print(f"🔄 {self.get_command_name()} 시작...")
    
    def log_success(self):
        """명령 성공 로그"""
        print(f"✅ {self.get_command_name()} 완료")
    
    def log_error(self, error: Exception):
        """명령 오류 로그"""
        print(f"❌ {self.get_command_name()} 실패: {str(error)}")
        raise EvaluationError(f"{self.get_command_name()} 중 오류 발생: {str(error)}") from error