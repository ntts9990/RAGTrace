"""
Generate Answers Command

답변 생성을 담당하는 명령입니다.
"""

from datasets import Dataset
from src.application.services.generation_service import GenerationService
from src.domain import EvaluationData
from .base_command import EvaluationCommand, EvaluationContext


class GenerateAnswersCommand(EvaluationCommand):
    """답변 생성 명령"""
    
    def __init__(self, generation_service: GenerationService):
        self.generation_service = generation_service
    
    def execute(self, context: EvaluationContext) -> None:
        """답변 생성 실행"""
        self.log_start()
        
        try:
            if not context.raw_data:
                raise ValueError("로드된 데이터가 없습니다.")
            
            # 답변 생성
            generation_result = self.generation_service.generate_missing_answers(context.raw_data)
            context.generation_result = generation_result
            
            # Ragas 데이터셋 형식으로 변환
            ragas_dataset = self._convert_to_dataset(context.raw_data)
            context.ragas_dataset = ragas_dataset
            
            self.log_success()
            
        except Exception as e:
            self.log_error(e)
    
    def _convert_to_dataset(self, evaluation_data_list: list[EvaluationData]) -> Dataset:
        """평가 데이터를 Ragas Dataset 형식으로 변환"""
        data_dict = {
            "question": [d.question for d in evaluation_data_list],
            "contexts": [d.contexts for d in evaluation_data_list],
            "answer": [d.answer for d in evaluation_data_list],
            "ground_truth": [d.ground_truth for d in evaluation_data_list],
        }
        return Dataset.from_dict(data_dict)
    
    def get_command_name(self) -> str:
        return "답변 생성"