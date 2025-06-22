"""
Run Evaluation Command

실제 평가 실행을 담당하는 명령입니다.
"""

from typing import Any

from .base_command import EvaluationCommand, EvaluationContext


class RunEvaluationCommand(EvaluationCommand):
    """평가 실행 명령"""
    
    def __init__(self, evaluation_runner: Any):
        self.evaluation_runner = evaluation_runner
    
    def execute(self, context: EvaluationContext) -> None:
        """평가 실행"""
        self.log_start()
        
        try:
            if not context.ragas_dataset:
                raise ValueError("RAGAS 데이터셋이 준비되지 않았습니다.")
            
            # 평가 실행
            result_dict = self.evaluation_runner.evaluate(dataset=context.ragas_dataset)
            context.evaluation_result_dict = result_dict
            
            self.log_success()
            
        except Exception as e:
            self.log_error(e)
    
    def get_command_name(self) -> str:
        return "평가 실행"