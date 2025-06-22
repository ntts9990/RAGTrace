"""
Navigation Model

네비게이션 관련 모델입니다.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class PageInfo:
    """페이지 정보"""
    title: str
    description: str
    icon: str


class NavigationModel:
    """네비게이션 관련 비즈니스 로직"""
    
    @staticmethod
    def get_pages() -> Dict[str, str]:
        """사용 가능한 페이지 목록 반환"""
        return {
            "🎯 Overview": "메인 대시보드",
            "🚀 New Evaluation": "새 평가 실행",
            "📈 Historical": "과거 평가 결과",
            "📚 Detailed Analysis": "상세 분석",
            "📖 Metrics Explanation": "메트릭 설명",
            "⚡ Performance": "성능 모니터링",
        }
    
    @staticmethod
    def get_page_info(page_key: str) -> PageInfo:
        """페이지 정보 반환"""
        pages_info = {
            "🎯 Overview": PageInfo("Overview", "메인 대시보드", "🎯"),
            "🚀 New Evaluation": PageInfo("New Evaluation", "새 평가 실행", "🚀"),
            "📈 Historical": PageInfo("Historical", "과거 평가 결과", "📈"),
            "📚 Detailed Analysis": PageInfo("Detailed Analysis", "상세 분석", "📚"),
            "📖 Metrics Explanation": PageInfo("Metrics Explanation", "메트릭 설명", "📖"),
            "⚡ Performance": PageInfo("Performance", "성능 모니터링", "⚡"),
        }
        return pages_info.get(page_key, PageInfo("Unknown", "알 수 없는 페이지", "❓"))
    
    @staticmethod
    def get_default_page() -> str:
        """기본 페이지 반환"""
        return "🎯 Overview"