"""
Run Evaluation Command

실제 평가 실행을 담당하는 명령입니다.
"""

import uuid
import datetime
from typing import Any

from .base_command import EvaluationCommand, EvaluationContext


class RunEvaluationCommand(EvaluationCommand):
    """평가 실행 명령"""
    
    def __init__(self, evaluation_runner: Any):
        self.evaluation_runner = evaluation_runner
    
    def execute(self, context: EvaluationContext) -> None:
        """평가 실행 및 최종 리포트 생성"""
        self.log_start()
        
        try:
            if not context.ragas_dataset:
                raise ValueError("RAGAS 데이터셋이 준비되지 않았습니다.")
            
            # 1. 평가 실행 (어댑터는 예외를 그대로 전달)
            parsed_result = self.evaluation_runner.evaluate(dataset=context.ragas_dataset)
            
            # 2. 최종 리포트 생성
            final_report = self._create_final_report(parsed_result, context)
            context.evaluation_result_dict = final_report
            
            self.log_success()
            
        except Exception as e:
            # Command 레벨에서 오류를 중앙 처리
            self.log_error(f"평가 실행 중 심각한 오류 발생: {e}")
            # 파이프라인의 다음 단계를 위해 빈 결과 생성
            context.evaluation_result_dict = self._create_error_report()
            
    def _create_final_report(self, result_dict: dict, context: EvaluationContext) -> dict:
        """최종 리포트 생성"""
        # ragas_score 계산
        metric_values = [v for k, v in result_dict.items() if k != "individual_scores" and v > 0]
        result_dict["ragas_score"] = sum(metric_values) / len(metric_values) if metric_values else 0.0
        
        # 메타데이터 추가
        llm = self.evaluation_runner.llm
        result_dict["metadata"] = {
            "evaluation_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "model": str(getattr(llm, 'model', 'N/A')),
            "temperature": getattr(llm, "temperature", 0.0),
            "dataset_size": len(context.ragas_dataset),
            "strategy": self.evaluation_runner.evaluation_context.primary_strategy.get_strategy_name(),
        }
        
        print(f"✅ 평가 완료!")
        print(f"📊 최종 결과: RAGAS Score = {result_dict['ragas_score']:.4f}")
        return result_dict
    
    def _create_error_report(self) -> dict:
        """오류 발생 시 최종 리포트 생성"""
        metrics = self.evaluation_runner.evaluation_context.get_metrics()
        error_result = {metric.name: 0.0 for metric in metrics}
        error_result["ragas_score"] = 0.0
        error_result["metadata"] = {
            "evaluation_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "error": "Evaluation failed"
        }
        return error_result
    
    def get_command_name(self) -> str:
        return "평가 실행"