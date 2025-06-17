"""
평가 데이터의 내용을 사전 검증하는 서비스

데이터의 품질을 평가하고 사용자에게 경고를 제공합니다.
"""

from dataclasses import dataclass
from typing import List

from src.domain import EvaluationData
from src.domain.exceptions import DataValidationError


@dataclass
class ValidationIssue:
    """데이터 검증 이슈"""
    item_index: int
    issue_type: str
    description: str
    severity: str  # "warning" | "error"
    field: str


@dataclass
class ValidationReport:
    """데이터 검증 보고서"""
    total_items: int
    valid_items: int
    issues: List[ValidationIssue]
    
    @property
    def error_count(self) -> int:
        return len([issue for issue in self.issues if issue.severity == "error"])
    
    @property
    def warning_count(self) -> int:
        return len([issue for issue in self.issues if issue.severity == "warning"])
    
    @property
    def has_errors(self) -> bool:
        return self.error_count > 0
    
    @property
    def has_warnings(self) -> bool:
        return self.warning_count > 0


class DataContentValidator:
    """데이터 내용 검증기"""
    
    def __init__(self):
        self.min_question_length = 5
        self.min_context_length = 10
        self.min_answer_length = 3
        self.min_ground_truth_length = 3
    
    def validate_data_list(self, data_list: List[EvaluationData]) -> ValidationReport:
        """데이터 리스트의 내용을 검증"""
        issues = []
        valid_items = 0
        
        for idx, data in enumerate(data_list):
            item_issues = self._validate_single_item(data, idx + 1)
            issues.extend(item_issues)
            
            # 에러가 없는 항목만 유효한 것으로 간주
            if not any(issue.severity == "error" for issue in item_issues):
                valid_items += 1
        
        return ValidationReport(
            total_items=len(data_list),
            valid_items=valid_items,
            issues=issues
        )
    
    def _validate_single_item(self, data: EvaluationData, item_index: int) -> List[ValidationIssue]:
        """단일 데이터 항목 검증"""
        issues = []
        
        # Question 검증
        if not data.question or not data.question.strip():
            issues.append(ValidationIssue(
                item_index=item_index,
                issue_type="empty_question",
                description="질문이 비어있습니다",
                severity="error",
                field="question"
            ))
        elif len(data.question.strip()) < self.min_question_length:
            issues.append(ValidationIssue(
                item_index=item_index,
                issue_type="short_question",
                description=f"질문이 너무 짧습니다 ({len(data.question)}자)",
                severity="warning",
                field="question"
            ))
        
        # Contexts 검증
        if not data.contexts or len(data.contexts) == 0:
            issues.append(ValidationIssue(
                item_index=item_index,
                issue_type="empty_contexts",
                description="컨텍스트가 비어있습니다",
                severity="error",
                field="contexts"
            ))
        else:
            # 각 컨텍스트의 내용 검증
            empty_contexts = 0
            for ctx_idx, context in enumerate(data.contexts):
                if not context or not context.strip():
                    empty_contexts += 1
                elif len(context.strip()) < self.min_context_length:
                    issues.append(ValidationIssue(
                        item_index=item_index,
                        issue_type="short_context",
                        description=f"컨텍스트 {ctx_idx + 1}이 너무 짧습니다 ({len(context)}자)",
                        severity="warning",
                        field=f"contexts[{ctx_idx}]"
                    ))
            
            if empty_contexts > 0:
                issues.append(ValidationIssue(
                    item_index=item_index,
                    issue_type="empty_context_items",
                    description=f"{empty_contexts}개의 컨텍스트가 비어있습니다",
                    severity="warning",
                    field="contexts"
                ))
        
        # Answer 검증 (옵션)
        if data.answer and len(data.answer.strip()) < self.min_answer_length:
            issues.append(ValidationIssue(
                item_index=item_index,
                issue_type="short_answer",
                description=f"답변이 너무 짧습니다 ({len(data.answer)}자)",
                severity="warning",
                field="answer"
            ))
        
        # Ground Truth 검증
        if not data.ground_truth or not data.ground_truth.strip():
            issues.append(ValidationIssue(
                item_index=item_index,
                issue_type="empty_ground_truth",
                description="정답(ground_truth)이 비어있습니다",
                severity="error",
                field="ground_truth"
            ))
        elif len(data.ground_truth.strip()) < self.min_ground_truth_length:
            issues.append(ValidationIssue(
                item_index=item_index,
                issue_type="short_ground_truth",
                description=f"정답이 너무 짧습니다 ({len(data.ground_truth)}자)",
                severity="warning",
                field="ground_truth"
            ))
        
        return issues
    
    def create_user_friendly_report(self, report: ValidationReport) -> str:
        """사용자 친화적인 검증 보고서 생성"""
        if not report.has_errors and not report.has_warnings:
            return f"✅ 모든 데이터가 검증을 통과했습니다. ({report.total_items}개 항목)"
        
        lines = []
        lines.append(f"📊 데이터 검증 결과: {report.valid_items}/{report.total_items}개 항목이 유효합니다.")
        
        if report.has_errors:
            lines.append(f"\n❌ 오류 {report.error_count}개:")
            error_issues = [issue for issue in report.issues if issue.severity == "error"]
            for issue in error_issues[:5]:  # 최대 5개만 표시
                lines.append(f"   항목 {issue.item_index}: {issue.description}")
            if len(error_issues) > 5:
                lines.append(f"   ... 그 외 {len(error_issues) - 5}개 오류")
        
        if report.has_warnings:
            lines.append(f"\n⚠️  경고 {report.warning_count}개:")
            warning_issues = [issue for issue in report.issues if issue.severity == "warning"]
            for issue in warning_issues[:5]:  # 최대 5개만 표시
                lines.append(f"   항목 {issue.item_index}: {issue.description}")
            if len(warning_issues) > 5:
                lines.append(f"   ... 그 외 {len(warning_issues) - 5}개 경고")
        
        if report.has_errors:
            lines.append("\n💡 오류가 있는 데이터로는 정확한 평가가 어려울 수 있습니다.")
        elif report.has_warnings:
            lines.append("\n💡 경고가 있지만 평가는 계속 진행할 수 있습니다.")
        
        return "\n".join(lines)