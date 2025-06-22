"""
Import Data Validators

Import된 데이터의 품질을 검증하는 모듈.
기존 데이터 검증 로직과 통합되어 일관된 품질 관리를 제공합니다.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from ...domain.entities.evaluation_data import EvaluationData


@dataclass
class ValidationResult:
    """데이터 검증 결과"""
    is_valid: bool
    total_records: int
    valid_records: int
    errors: List[str]
    warnings: List[str]
    
    @property
    def success_rate(self) -> float:
        """검증 성공률 (0.0 ~ 1.0)"""
        if self.total_records == 0:
            return 0.0
        return self.valid_records / self.total_records


class ImportDataValidator:
    """Import된 데이터 검증기"""
    
    def __init__(self, 
                 min_question_length: int = 5,
                 min_answer_length: int = 3,
                 min_context_length: int = 10,
                 max_contexts_count: int = 10):
        """
        Args:
            min_question_length: 질문 최소 길이
            min_answer_length: 답변 최소 길이  
            min_context_length: 컨텍스트 최소 길이
            max_contexts_count: 최대 컨텍스트 개수
        """
        self.min_question_length = min_question_length
        self.min_answer_length = min_answer_length
        self.min_context_length = min_context_length
        self.max_contexts_count = max_contexts_count
    
    def validate_data_list(self, data_list: List[EvaluationData]) -> ValidationResult:
        """데이터 리스트 전체 검증"""
        total_records = len(data_list)
        valid_records = 0
        errors = []
        warnings = []
        
        for i, data in enumerate(data_list, 1):
            try:
                # 개별 데이터 검증
                is_valid, data_errors, data_warnings = self._validate_single_data(data, i)
                
                if is_valid:
                    valid_records += 1
                
                errors.extend(data_errors)
                warnings.extend(data_warnings)
                
            except Exception as e:
                errors.append(f"항목 {i}: 검증 중 오류 발생 - {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            total_records=total_records,
            valid_records=valid_records,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_single_data(self, data: EvaluationData, index: int) -> Tuple[bool, List[str], List[str]]:
        """개별 데이터 항목 검증"""
        errors = []
        warnings = []
        
        # 1. 필수 필드 존재 확인
        if not data.question or not data.question.strip():
            errors.append(f"항목 {index}: 질문이 비어있습니다")
        
        if not data.answer or not data.answer.strip():
            errors.append(f"항목 {index}: 답변이 비어있습니다")
        
        if not data.ground_truth or not data.ground_truth.strip():
            errors.append(f"항목 {index}: 정답이 비어있습니다")
        
        if not data.contexts or len(data.contexts) == 0:
            errors.append(f"항목 {index}: 컨텍스트가 비어있습니다")
        
        # 2. 길이 검증
        if data.question and len(data.question.strip()) < self.min_question_length:
            warnings.append(f"항목 {index}: 질문이 너무 짧습니다 ({len(data.question.strip())}자)")
        
        if data.answer and len(data.answer.strip()) < self.min_answer_length:
            warnings.append(f"항목 {index}: 답변이 너무 짧습니다 ({len(data.answer.strip())}자)")
        
        if data.ground_truth and len(data.ground_truth.strip()) < 2:
            warnings.append(f"항목 {index}: 정답이 너무 짧습니다 ({len(data.ground_truth.strip())}자)")
        
        # 3. 컨텍스트 검증
        if data.contexts:
            if len(data.contexts) > self.max_contexts_count:
                warnings.append(f"항목 {index}: 컨텍스트가 너무 많습니다 ({len(data.contexts)}개)")
            
            for ctx_idx, context in enumerate(data.contexts):
                if not context or not context.strip():
                    errors.append(f"항목 {index}: {ctx_idx+1}번째 컨텍스트가 비어있습니다")
                elif len(context.strip()) < self.min_context_length:
                    warnings.append(f"항목 {index}: {ctx_idx+1}번째 컨텍스트가 너무 짧습니다 ({len(context.strip())}자)")
        
        # 4. 중복 검증
        if data.question and data.answer and data.question.strip().lower() == data.answer.strip().lower():
            warnings.append(f"항목 {index}: 질문과 답변이 동일합니다")
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def get_validation_summary(self, result: ValidationResult) -> str:
        """검증 결과 요약 메시지 생성"""
        if result.total_records == 0:
            return "검증할 데이터가 없습니다."
        
        summary_lines = [
            f"📊 데이터 검증 결과:",
            f"   전체: {result.total_records}개",
            f"   유효: {result.valid_records}개",
            f"   성공률: {result.success_rate:.1%}",
        ]
        
        if result.errors:
            summary_lines.append(f"   ❌ 오류: {len(result.errors)}개")
        
        if result.warnings:
            summary_lines.append(f"   ⚠️ 경고: {len(result.warnings)}개")
        
        if result.is_valid:
            summary_lines.append("✅ 모든 데이터가 검증을 통과했습니다.")
        else:
            summary_lines.append("❌ 일부 데이터에 문제가 있습니다.")
        
        return "\n".join(summary_lines)
    
    def filter_valid_data(self, data_list: List[EvaluationData]) -> List[EvaluationData]:
        """유효한 데이터만 필터링하여 반환"""
        valid_data = []
        
        for data in data_list:
            is_valid, _, _ = self._validate_single_data(data, 0)
            if is_valid:
                valid_data.append(data)
        
        return valid_data