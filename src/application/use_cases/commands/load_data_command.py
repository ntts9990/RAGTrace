"""
Load Data Command

데이터 로드를 담당하는 명령입니다.
"""

from typing import TYPE_CHECKING

from src.domain import EvaluationError
from .base_command import EvaluationCommand, EvaluationContext

if TYPE_CHECKING:
    from src.infrastructure.repository import FileRepositoryFactory


class LoadDataCommand(EvaluationCommand):
    """데이터 로드 명령"""
    
    def __init__(self, repository_factory: "FileRepositoryFactory"):
        self.repository_factory = repository_factory
    
    def execute(self, context: EvaluationContext) -> None:
        """데이터 로드 실행"""
        self.log_start()
        
        try:
            # 리포지토리 생성 및 데이터 로드
            repository_port = self.repository_factory.create_repository(context.dataset_name)
            evaluation_data_list = repository_port.load_data()
            
            if not evaluation_data_list:
                raise EvaluationError("평가 데이터가 없습니다.")
            
            # 컨텍스트에 결과 저장
            context.raw_data = evaluation_data_list
            
            print(f"📊 평가할 데이터 개수: {len(evaluation_data_list)}개")
            self.log_success()
            
        except Exception as e:
            self.log_error(e)
    
    def get_command_name(self) -> str:
        return "데이터 로드"