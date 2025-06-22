"""
Validate Data Command

데이터 검증을 담당하는 명령입니다.
"""

from src.application.services.data_validator import DataContentValidator
from .base_command import EvaluationCommand, EvaluationContext


class ValidateDataCommand(EvaluationCommand):
    """데이터 검증 명령"""
    
    def __init__(self, data_validator: DataContentValidator):
        self.data_validator = data_validator
    
    def execute(self, context: EvaluationContext) -> None:
        """데이터 검증 실행"""
        self.log_start()
        
        try:
            if not context.raw_data:
                raise ValueError("로드된 데이터가 없습니다.")
            
            # 데이터 내용 검증
            validation_report = self.data_validator.validate_data_list(context.raw_data)
            context.validation_report = validation_report
            
            # 검증 결과 리포트
            if validation_report.has_errors or validation_report.has_warnings:
                validation_message = self.data_validator.create_user_friendly_report(validation_report)
                print(f"\n{validation_message}")
                
                if validation_report.has_errors:
                    print("\n❓ 오류가 있는 데이터로 평가를 계속 진행합니다.")
                    print("   품질이 낮은 결과가 나올 수 있습니다.")
                elif validation_report.has_warnings:
                    print("\n💡 경고사항이 있지만 평가를 계속 진행합니다.")
            
            self.log_success()
            
        except Exception as e:
            self.log_error(e)
    
    def get_command_name(self) -> str:
        return "데이터 검증"