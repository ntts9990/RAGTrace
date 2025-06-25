"""
Evaluation Pipeline

Command 패턴을 사용한 평가 파이프라인입니다.
"""

from typing import List, Optional

from src.domain import EvaluationResult, EvaluationError
from src.domain.prompts import PromptType
from .base_command import EvaluationCommand, EvaluationContext


class EvaluationPipeline:
    """평가 파이프라인 - Command들을 순차적으로 실행"""
    
    def __init__(self):
        self.commands: List[EvaluationCommand] = []
    
    def add_command(self, command: EvaluationCommand) -> 'EvaluationPipeline':
        """명령 추가 (체이닝 가능)"""
        self.commands.append(command)
        return self
    
    def execute(self, dataset_name: str, prompt_type: Optional[PromptType] = None) -> EvaluationResult:
        """파이프라인 실행"""
        print(f"\n=== 평가 파이프라인 시작 ===")
        print(f"📊 데이터셋: {dataset_name}")
        if prompt_type:
            print(f"🎯 프롬프트 타입: {prompt_type.value}")
        
        # 컨텍스트 초기화
        context = EvaluationContext(
            dataset_name=dataset_name,
            prompt_type=prompt_type
        )
        
        try:
            # 모든 명령 순차 실행
            for i, command in enumerate(self.commands, 1):
                print(f"\n[{i}/{len(self.commands)}] {command.get_command_name()}")
                command.execute(context)
            
            # 최종 결과 확인
            if not context.final_result:
                raise EvaluationError("파이프라인 실행 완료되었으나 최종 결과가 없습니다.")
            
            print(f"\n✅ 평가 파이프라인 완료!")
            print(f"📊 최종 RAGAS Score: {context.final_result.ragas_score:.4f}")
            
            return context.final_result
            
        except Exception as e:
            print(f"\n❌ 평가 파이프라인 실패: {str(e)}")
            if isinstance(e, EvaluationError):
                raise
            raise EvaluationError(f"평가 파이프라인 실행 중 오류 발생: {str(e)}") from e
    
    def get_pipeline_info(self) -> str:
        """파이프라인 정보 반환"""
        command_names = [cmd.get_command_name() for cmd in self.commands]
        return f"파이프라인 단계: {' → '.join(command_names)}"