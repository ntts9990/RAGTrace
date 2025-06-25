"""
Convert Result Command

결과 변환을 담당하는 명령입니다.
"""

from src.application.services.result_conversion_service import ResultConversionService
from .base_command import EvaluationCommand, EvaluationContext


class ConvertResultCommand(EvaluationCommand):
    """결과 변환 명령"""
    
    def __init__(self, result_conversion_service: ResultConversionService):
        self.result_conversion_service = result_conversion_service
    
    def execute(self, context: EvaluationContext) -> None:
        """결과 변환 실행"""
        self.log_start()
        
        try:
            if not context.evaluation_result_dict:
                raise ValueError("평가 결과가 없습니다.")
            
            if not context.generation_result:
                raise ValueError("답변 생성 결과가 없습니다.")
            
            # 결과 검증 및 변환
            final_result = self.result_conversion_service.validate_and_convert_result(
                context.evaluation_result_dict,
                context.generation_result.failures,
                context.generation_result.successes,
                context.generation_result.failure_details
            )
            
            context.final_result = final_result
            
            self.log_success()
            
        except Exception as e:
            self.log_error(e)
    
    def get_command_name(self) -> str:
        return "결과 변환"